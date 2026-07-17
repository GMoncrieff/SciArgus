# SciArgus

**A free, automated weekly newsletter that watches the scientific literature for you.**

---

In Greek mythology, **Argus Panoptes** was the all-seeing giant with a hundred eyes — a watchful guardian who never slept. SciArgus carries that spirit into the world of scientific publishing. With thousands of papers released every week across hundreds of journals, no researcher can keep up. SciArgus watches the literature with tireless, many-eyed attention so you don't have to. Each Monday, it delivers a curated email with the papers that matter most to your specific research interests — scored, ranked, and summarised in plain language.

---

## Table of Contents

- [Why a Custom Newsletter?](#why-a-custom-newsletter)
- [How It Works](#how-it-works)
- [Defining Your Interests](#defining-your-interests)
  - [Topics](#topics)
  - [Authors](#authors)
  - [Journals](#journals)
- [Setup Guide](#setup-guide)
  - [1. Create a GitHub Account](#1-create-a-github-account)
  - [2. Fork This Repository](#2-fork-this-repository)
  - [3. Get a Gemini API Key](#3-get-a-gemini-api-key)
  - [4. Get an OpenAlex API Key](#4-get-an-openalex-api-key)
  - [5. Create a Gmail App Password](#5-create-a-gmail-app-password)
  - [6. Add Your Secrets to GitHub](#6-add-your-secrets-to-github)
  - [7. Customise Your Config Files](#7-customise-your-config-files)
  - [8. Test It](#8-test-it)
- [What It Costs](#what-it-costs)
- [Troubleshooting](#troubleshooting)

---

## Why a Custom Newsletter?

Existing tools for tracking the scientific literature fall into two camps:

1. **Too broad.** Journal table-of-contents alerts flood your inbox with dozens of papers you don't care about, from every subfield the journal covers.
2. **Too narrow.** Keyword alerts on Google Scholar or PubMed miss papers that use different terminology, and they can't understand the *context* of your interests.

SciArgus takes a different approach. You describe your research interests in your own words — as rich, paragraph-length descriptions — and an AI model reads every candidate paper and scores how relevant it is to *your specific interests*. The result is a weekly digest of up to 20 papers, each with a personalised summary explaining why it matters to you.

You also track specific authors. Even if a colleague publishes something outside your usual keywords, SciArgus will find it and tell you how it connects to your work.

Because you control the configuration, you get exactly the newsletter you want — not what an algorithm trained on clicks thinks you want.

---

## How It Works

SciArgus runs as a scheduled GitHub Action every Monday morning. The pipeline has five stages:

```
1. RESOLVE     Plain-text names  -->  OpenAlex IDs  (cached for 30 days)
2. SCRAPE      Search OpenAlex for papers from the last 7 days
3. SCORE       AI ranks every paper against all your topic descriptions
4. SUMMARISE   AI writes a personalised "why this is cool" for the top papers
5. EMAIL       Sends a formatted HTML newsletter to your inbox
```

**Stage 1 — Resolve.** Your config files use plain-text names (e.g. "Nature Ecology & Evolution", "Sara Beery"). On the first run, SciArgus looks up each name in [OpenAlex](https://openalex.org) — a free, open index of the world's research — and saves the resolved identifiers in a local cache. This cache is reused for 30 days, so subsequent runs skip this step entirely.

**Stage 2 — Scrape.** SciArgus searches OpenAlex in two ways:
- **By topic:** For each of your topics, it searches for papers published in the last 7 days in your tracked journals. This means a broad topic like "Machine Learning" only returns papers from ecology and conservation journals (or whichever journals you track), not the entire ML literature.
- **By author:** It fetches all recent papers by your tracked authors, regardless of journal.

**Stage 3 — Score.** All candidate papers (typically 100–200) are sent to Google's Gemini AI in batches. The model reads each paper's title and abstract, compares it against all your topic descriptions simultaneously, and assigns a relevance score (0–10) and a best-matching topic.

**Stage 4 — Summarise.** The top 10 topic-matched papers and top 10 author papers are selected. For each, the AI writes 2–3 sentences explaining why the paper is relevant to your specific interests. These are personalised — they reference your topic descriptions, not generic summaries.

**Stage 5 — Email.** Everything is rendered into a clean HTML email and sent via Gmail.

---

## Defining Your Interests

Your newsletter is shaped by three configuration files in the `config/` folder. These are plain text files that you edit directly — no code required.

### Topics

**File:** `config/topics.md`

Topics are your core research interests. Each topic has a **heading** (starting with `#`) followed by a **description paragraph**. The heading is used to search for papers; the description is what the AI uses to judge relevance and write summaries.

**The description matters.** A vague description produces vague results. Be specific about what excites you.

**Format:**

```markdown
#Your Topic Name
A detailed paragraph describing what you're interested in within this
topic. Be specific. Mention particular methods, organisms, scales, or
questions. The AI uses this text to decide which papers are relevant
to you and to write personalised summaries.

#Another Topic
Another detailed description...
```

**Example:**

```markdown
#Remote Sensing of Biodiversity
Research into the application of remote sensing for the quantification
of biodiversity and ecosystems at both local and global scales. This
encompasses all sensor technologies — including drones, airborne and
satellite LiDAR, radar, and optical sensors (particularly hyperspectral).
Topics should cover the development of new sensor technologies, the
creation of novel algorithms for ecosystem monitoring, and advancements
in leveraging existing sensors to derive critical biodiversity information.
```

**Tips:**
- Use 5–15 topics. Fewer than 5 may miss papers; more than 15 dilutes the scoring.
- Each paper is assigned to at most one topic (its best match), so topics can overlap without causing duplicates.
- The heading is used as a search query on OpenAlex, so use natural, descriptive headings.

### Authors

**File:** `config/authors.md`

A list of researchers whose output you want to track. One name per line.

**Format:**

```
Andrew Balmford
Sara Beery
Hugh Possingham
```

**Tips:**
- Use the name as it appears on their publications. OpenAlex resolves to the highest-cited matching author, so common names usually resolve correctly.
- Author papers are included regardless of journal — this is how you catch a collaborator's paper in a journal you don't normally follow.
- If a name doesn't resolve (you'll see a warning in the logs), try the full name as listed on their Google Scholar or ORCID profile.
- 20–50 authors is a reasonable range.

### Journals

**File:** `config/journals.md`

A whitelist of journals and preprint servers. One name per line. These serve as a quality filter for topic searches — SciArgus only returns topic-matched papers published in these venues.

**Format:**

```
Nature
Science
bioRxiv
Conservation Biology
Remote Sensing of Environment
```

**Tips:**
- Include the preprint servers relevant to your field (bioRxiv, arXiv, EcoEvoRxiv, etc.) to catch papers before formal publication.
- This list does NOT apply to author papers — those are included from any venue.
- 50–150 journals is typical. Cast a wide net; the AI scoring handles relevance.
- Use the journal's full name as it appears on its website. OpenAlex is flexible with matching.

---

## Setup Guide

This guide assumes no programming experience. You'll need a web browser and about 30 minutes.

### 1. Create a GitHub Account

If you don't have one, go to [github.com](https://github.com) and sign up for a free account. GitHub is where the code lives and where the automated weekly job runs.

### 2. Fork This Repository

A "fork" creates your own copy of SciArgus that you can customise.

1. Go to the [SciArgus repository](https://github.com/GMoncrieff/SciArgus)
2. Click the **Fork** button in the top-right corner
3. On the next page, click **Create fork**

You now have your own copy at `github.com/YOUR-USERNAME/SciArgus`.

> **Important:** After forking, you need to enable GitHub Actions on your fork. Go to the **Actions** tab in your forked repository and click **"I understand my workflows, go ahead and enable them"**.

### 3. Get a Gemini API Key

SciArgus uses Google's Gemini AI to score and summarise papers. The free tier is more than sufficient.

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **Get API key** in the left sidebar
4. Click **Create API key**
5. Copy the key — you'll need it in step 5

The free tier allows 15 requests per minute and 500 requests per day. SciArgus uses roughly 20 requests per run, well within these limits.

### 4. Get an OpenAlex API Key

SciArgus uses the [OpenAlex](https://openalex.org) API to find and resolve papers, authors, and journals. **An OpenAlex API key is required** to avoid rate-limit errors and ensure reliable access.

1. Go to the [OpenAlex API key request page](https://docs.openalex.org/how-to-use-the-api/api-key)
2. Follow the instructions to request your free API key
3. Copy the key — you'll need it in step 6

### 5. Create a Gmail App Password

SciArgus sends the newsletter email through Gmail. To allow this, you need to create an "app password" — a special password that lets the script log into your Gmail account to send mail.

**Prerequisites:** You must have 2-Step Verification enabled on your Google account.

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", make sure **2-Step Verification** is turned **On**
4. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
5. Under "App name", type `SciArgus` and click **Create**
6. Google will show you a 16-character password. **Copy it immediately** — it will not be shown again

This password only allows sending email; it cannot access your files or other Google services.

> **Tip:** You can use any Gmail address as the sender. If you prefer, create a dedicated Gmail account (e.g. `my-sciargus@gmail.com`) so the newsletter comes from a separate address.

### 6. Add Your Secrets to GitHub

Secrets are private values that GitHub Actions can use but that never appear in your code or logs.

1. Go to your forked repository on GitHub
2. Click **Settings** (the gear icon tab at the top)
3. In the left sidebar, click **Secrets and variables** > **Actions**
4. Click **New repository secret** and add each of the following:

| Secret name | Value | Example |
|---|---|---|
| `GEMINI_KEY` | Your Gemini API key from step 3 | `AIzaSy...` |
| `OPENALEX_SECRET` | **Required.** Your OpenAlex API key from step 4 | `openalex_...` |
| `GOOGLE_APP_PASSWORD` | The 16-character app password from step 5 | `abcd efgh ijkl mnop` |
| `SENDER_EMAIL` | The Gmail address you created the app password for | `my-sciargus@gmail.com` |
| `RECEIVER_EMAIL` | The email address where you want to receive the newsletter | `yourname@university.edu` |

The sender and receiver can be the same address if you like.

> **OpenAlex API Key (required).** SciArgus requires a valid OpenAlex API key to avoid 429 rate-limit errors and ensure reliable access to the OpenAlex API. [Request a free API key from OpenAlex](https://docs.openalex.org/how-to-use-the-api/api-key) and add it as the `OPENALEX_SECRET` secret. The key is sent as an `api_key` query parameter on every OpenAlex request.

### 7. Customise Your Config Files

Now edit the three config files to match your interests.

1. In your forked repository on GitHub, navigate to the `config/` folder
2. Click on `topics.md`, then click the **pencil icon** (Edit this file)
3. Replace the content with your own topics and descriptions
4. Click **Commit changes**
5. Repeat for `authors.md` and `journals.md`

See [Defining Your Interests](#defining-your-interests) above for format details and tips.

### 8. Test It

Trigger a manual run to make sure everything works:

1. Go to the **Actions** tab in your repository
2. Click **Weekly SciArgus Newsletter** in the left sidebar
3. Click **Run workflow** > **Run workflow**
4. Wait 5–10 minutes for the run to complete (you can watch the live logs by clicking on the running job)
5. Check your inbox

If the run fails, click on the failed job to see the logs. Common issues are covered in [Troubleshooting](#troubleshooting) below.

Once it works, the newsletter will arrive automatically every Monday at 08:00 UTC. No further action needed.

---

## What It Costs

**Nothing.** Every service SciArgus uses has a free tier that is more than sufficient:

| Service | What it provides | Free tier limits | SciArgus usage per run |
|---|---|---|---|
| **GitHub Actions** | Runs the code weekly | 2,000 minutes/month | ~10 minutes/run (~40 min/month) |
| **OpenAlex API** | Paper metadata and search | Free with API key | ~30 requests |
| **Gemini API** | AI scoring and summaries | 500 requests/day, 15/min | ~20 requests |
| **Gmail SMTP** | Sends the email | 500 emails/day | 1 email |

No credit card is required for any of these services.

---

## Troubleshooting

**The workflow failed — where do I see the error?**
Go to the **Actions** tab, click on the failed run, then click on the **send-newsletter** job. Expand the **Run newsletter** step to see the full logs.

**"No results for [author/journal name]"**
OpenAlex couldn't find that name. Try the exact name as it appears on the author's publications or the journal's website. Check for typos. Names with special characters (accents, hyphens) sometimes need the exact Unicode character.

**"400 Bad Request" for a journal name**
Some journal names with commas cause issues with the OpenAlex API filter syntax. Try shortening the name or removing the comma.

**"429 RESOURCE_EXHAUSTED" from Gemini**
You've hit the Gemini API rate limit. This usually means the daily quota is exhausted (500 requests/day on the free tier). The pipeline will retry automatically, but if the daily cap is reached, you'll need to wait until it resets (midnight Pacific time). This should not happen under normal usage.

**The email didn't arrive**
Check your spam folder. If using a new Gmail account as the sender, the first few emails may be flagged as spam. Mark it as "not spam" and future emails should arrive normally.

**Papers seem irrelevant**
Improve your topic descriptions. The more specific and detailed your descriptions, the better the AI can judge relevance. Vague one-line descriptions produce noisy results.

**I want to change the schedule**
Edit `.github/workflows/weekly_newsletter.yml`. The `cron` line controls the schedule. The format is `minute hour day-of-month month day-of-week` in UTC. For example, `'0 14 * * 5'` runs at 2pm UTC every Friday.
