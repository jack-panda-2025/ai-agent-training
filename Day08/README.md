# Day 8 — Supervisor Pattern

## What this does
Given a tech article URL, produces an English summary and
Chinese translation using a Supervisor multi-agent pattern.

## Task
Given a tech article URL:
1. Fetch and parse the article (fetcher)
2. Summarize into 3-5 bullet points (summarizer)
3. Translate summary to Chinese (translator)

## How it works
A supervisor agent reads current state after every worker,
decides who runs next, and routes until all tasks are done.