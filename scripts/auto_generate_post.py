#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timedelta, timezone
import re
import subprocess

ROOT = Path('/home/dev/workspace/blogbot')
POSTS = ROOT / 'content' / 'posts'

TOPICS = [
    ("AI Agents", "Agent Reliability Playbook for Production Teams"),
    ("RAG & Vector Search", "RAG Relevance Tuning in Production: A Practical Guide"),
    ("AI Platform & MLOps", "LLM Platform Governance: Controls CTOs Should Standardize"),
    ("Local LLMs", "Operating Local LLMs at Scale: Capacity and Cost Tradeoffs"),
    ("AI Coding Tools", "AI Coding Assistants in Enterprise SDLC: Adoption Without Chaos"),
]

TAGS = {
    "AI Agents": ["ai agents", "reliability", "production", "architecture"],
    "RAG & Vector Search": ["rag", "retrieval", "vector search", "evaluation"],
    "AI Platform & MLOps": ["mlops", "llmops", "governance", "platform"],
    "Local LLMs": ["local llm", "inference", "ollama", "performance"],
    "AI Coding Tools": ["copilot", "cursor", "developer productivity", "governance"],
}


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s[:80].strip('-')


def parse_dates():
    used = set()
    for p in POSTS.glob('*.md'):
        txt = p.read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'^date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})T', txt, re.M)
        if m:
            used.add(m.group(1))
    return used


def previous_monday(dt):
    # Monday=0
    days_back = (dt.weekday() - 0) % 7
    return dt - timedelta(days=days_back)


def next_available_monday(used_dates):
    # start from this week's Monday, then go backward until find unused
    now = datetime.now(timezone.utc)
    cand = previous_monday(now).date()
    for _ in range(520):
        s = cand.isoformat()
        if s not in used_dates:
            return cand
        cand = cand - timedelta(days=7)
    raise RuntimeError('No available Monday date found in search window')


def next_topic():
    # rotate by number of existing posts
    count = len(list(POSTS.glob('*.md')))
    return TOPICS[count % len(TOPICS)]


def build_post(category, title, date_iso):
    tags = TAGS[category]
    slug = slugify(title)
    dt_full = f"{date_iso}T09:00:00Z"
    cover = "/images/inference-cost-control-cover.svg"

    body = f'''---
title: "{title}"
description: "Executive-grade implementation guide for {title.lower()} with practical architecture, governance controls, and KPI tracking."
date: {dt_full}
lastmod: {dt_full}
draft: false
author: "The Editorial Team"
categories: ["{category}"]
tags: ["{tags[0]}", "{tags[1]}", "{tags[2]}", "{tags[3]}"]
keywords: ["{title}", "production AI", "CTO playbook"]
cover:
  image: "{cover}"
  alt: "{title}"
---

For CTOs, CEOs, Software Architects, and Tech Leads, the priority is not experimentation speed alone. The priority is **predictable delivery**: quality, risk control, and measurable business impact.

## Executive context
This topic matters because organizations are moving from isolated pilots to portfolio-level AI operations. That shift requires clear ownership, release governance, and explicit cost-quality tradeoffs.

## Architecture and operating model
A practical production model should include:

1. **Clear ownership** across product, platform, security, and operations
2. **Policy-enforced execution** (guardrails, approvals, budgets)
3. **Observability by default** (latency, quality, cost, incidents)
4. **Rollback-ready releases** (canary strategy + objective gates)

## Leadership KPI set
Track these metrics weekly:

- Task success rate (business-defined)
- Escalation rate to human teams
- Cost per successful outcome
- p95 response latency
- Quality regression incidents per release

## Decision framework for technical leadership
Use a release gate model:

- **Gate A:** offline quality and policy checks
- **Gate B:** staging integration and tool reliability
- **Gate C:** production canary with rollback triggers

If any gate fails, block rollout.

## Official documentation references
- OpenAI docs: https://platform.openai.com/docs
- Cloudflare Workers docs: https://developers.cloudflare.com/workers/
- OpenTelemetry docs: https://opentelemetry.io/docs/

## Recommendation
Treat AI delivery as an engineering system with product accountability. Teams that standardize gates, metrics, and ownership scale faster with fewer incidents.
'''
    return slug, body


def main():
    POSTS.mkdir(parents=True, exist_ok=True)
    used = parse_dates()
    monday = next_available_monday(used)
    category, title = next_topic()
    slug, content = build_post(category, title, monday.isoformat())
    fname = f"{monday.isoformat()}-{slug}.md"
    out = POSTS / fname
    out.write_text(content, encoding='utf-8')

    subprocess.run(['git', '-C', str(ROOT), 'add', str(out)], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'commit', '-m', f'content(auto): add recurring post {fname}'], check=True)
    subprocess.run(['bash', '-lc', "GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_github_openclaw -o IdentitiesOnly=yes' git -C /home/dev/workspace/blogbot push origin main"], check=True)
    print(f'Created and pushed: {out}')


if __name__ == '__main__':
    main()
