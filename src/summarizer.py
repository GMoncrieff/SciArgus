from __future__ import annotations

import json
import logging
import time

from google import genai

from .models import Paper, Topic

logger = logging.getLogger(__name__)

MODEL = "gemini-3.5-flash-lite"
RPM_LIMIT = 15
SCORING_BATCH_SIZE = 10
SUMMARY_BATCH_SIZE = 5


class RateLimiter:
    """Enforce max N calls per 60-second window."""

    def __init__(self, max_calls: int = RPM_LIMIT):
        self.max_calls = max_calls
        self.timestamps: list[float] = []

    def wait(self) -> None:
        now = time.time()
        # Remove timestamps older than 60s
        self.timestamps = [t for t in self.timestamps if now - t < 60]
        if len(self.timestamps) >= self.max_calls:
            sleep_time = 60 - (now - self.timestamps[0]) + 1
            if sleep_time > 0:
                logger.info("Rate limit: sleeping %.1fs", sleep_time)
                time.sleep(sleep_time)
        self.timestamps.append(time.time())


def _call_gemini(
    client: genai.Client,
    prompt: str,
    limiter: RateLimiter,
    retries: int = 1,
) -> str | None:
    for attempt in range(retries + 1):
        limiter.wait()
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.3,
                ),
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < retries:
                logger.warning("Rate limited (429), sleeping 62s before retry")
                time.sleep(62)
                continue
            if attempt < retries:
                logger.warning("Gemini error: %s, retrying in 10s", e)
                time.sleep(10)
                continue
            logger.error("Gemini call failed after retries: %s", e)
            return None
    return None


def _extract_json(text: str) -> list[dict] | None:
    # Strip markdown code fences if present
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last lines (fences)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to find JSON array in the text
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from response: %s", text[:200])
                return None
        return None


def score_papers(
    client: genai.Client,
    papers: list[Paper],
    topics: list[Topic],
    limiter: RateLimiter,
) -> None:
    """Score all papers against all topics. Modifies papers in-place."""
    if not papers:
        return

    topic_block = "\n".join(
        f"{i + 1}. {t.label}: {t.description}" for i, t in enumerate(topics)
    )

    for batch_start in range(0, len(papers), SCORING_BATCH_SIZE):
        batch = papers[batch_start : batch_start + SCORING_BATCH_SIZE]
        papers_block = "\n".join(
            f'{i + 1}. "{p.title}" — {(p.abstract or "No abstract available")[:200]}'
            for i, p in enumerate(batch)
        )

        prompt = f"""You are a research paper curator. Score each paper's relevance (0-10) to the BEST matching research interest below. Only assign a score above 0 if the paper is clearly relevant to one of these specific interests.

RESEARCH INTERESTS:
{topic_block}

PAPERS:
{papers_block}

Return ONLY a JSON array, no other text: [{{"index": 1, "topic": 4, "score": 8}}, ...]
Where "index" is the paper number (1-based), "topic" is the interest number (1-based), and "score" is 0-10."""

        result = _call_gemini(client, prompt, limiter)
        if not result:
            logger.warning("Scoring batch failed, assigning score 0")
            continue

        scores = _extract_json(result)
        if not scores:
            continue

        for entry in scores:
            idx = (entry.get("index") or 0) - 1
            topic_num = entry.get("topic")
            score = entry.get("score") or 0
            if topic_num is None or score == 0:
                continue
            topic_idx = topic_num - 1
            if 0 <= idx < len(batch) and 0 <= topic_idx < len(topics):
                batch[idx].relevance_score = score
                batch[idx].matched_topic = topics[topic_idx].label

        logger.info(
            "Scored batch %d-%d",
            batch_start + 1,
            batch_start + len(batch),
        )


def generate_summaries(
    client: genai.Client,
    papers: list[Paper],
    topics: list[Topic],
    limiter: RateLimiter,
) -> None:
    """Generate personalized summaries for selected papers. Modifies in-place."""
    if not papers:
        return

    topic_map = {t.label: t.description for t in topics}

    for batch_start in range(0, len(papers), SUMMARY_BATCH_SIZE):
        batch = papers[batch_start : batch_start + SUMMARY_BATCH_SIZE]

        papers_block = ""
        for i, p in enumerate(batch):
            interest_desc = topic_map.get(p.matched_topic or "", "general research")
            papers_block += f"""
Paper {i + 1}:
Research interest: "{interest_desc}"
Title: {p.title}
Abstract: {(p.abstract or 'No abstract available')[:500]}
"""

        prompt = f"""For each paper below, write 2-3 sentences explaining why it is interesting and relevant to the specified research interest. Be specific about the connection. Address the reader directly as "you".

{papers_block}

Return ONLY a JSON array: [{{"index": 1, "summary": "This paper..."}}, ...]"""

        result = _call_gemini(client, prompt, limiter)
        if not result:
            logger.warning("Summary batch failed, papers will render without summaries")
            continue

        summaries = _extract_json(result)
        if not summaries:
            continue

        for entry in summaries:
            idx = (entry.get("index") or 0) - 1
            if 0 <= idx < len(batch):
                batch[idx].summary = entry.get("summary")

        logger.info(
            "Generated summaries for batch %d-%d",
            batch_start + 1,
            batch_start + len(batch),
        )
