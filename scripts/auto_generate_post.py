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




# Generate a consistent cover image based on the title
def generate_cover(title: str, slug: str):
    from pathlib import Path
    import hashlib, colorsys
    def hcolor(seed, s=0.25, v=0.92):
        h=(int(hashlib.md5(seed.encode()).hexdigest()[:6],16)%360)/360.0
        r,g,b=colorsys.hsv_to_rgb(h,s,v)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    c1=hcolor(title+'a'); c2=hcolor(title+'b'); c3='#f5f7fb'
    svg=f"""<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='630' viewBox='0 0 1200 630'>
  <defs>
    <linearGradient id='bg' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0%' stop-color='{c1}'/>
      <stop offset='100%' stop-color='{c2}'/>
    </linearGradient>
  </defs>
  <rect width='1200' height='630' fill='url(#bg)'/>
  <rect x='64' y='64' width='1072' height='502' rx='18' fill='{c3}' fill-opacity='0.92'/>
  <text x='96' y='165' fill='#0f172a' font-family='Arial, Helvetica, sans-serif' font-size='28' font-weight='700'>LLMCraft</text>
  <foreignObject x='96' y='210' width='980' height='300'>
    <div xmlns='http://www.w3.org/1999/xhtml' style='font-family:Arial,Helvetica,sans-serif;color:#0f172a;font-size:54px;line-height:1.15;font-weight:800;'>""" + title + """</div>
  </foreignObject>
</svg>"""
    out=Path('/home/dev/workspace/blogbot/static/images/posts')
    out.mkdir(parents=True, exist_ok=True)
    (out/f"{slug}-cover.svg").write_text(svg)

def build_post(category, title, date_iso):
    tags = TAGS[category]
    slug = slugify(title)
    dt_full = f"{date_iso}T09:00:00Z"
    cover = f"/images/posts/{slug}-cover.svg"

    body = f'''---
title: "{title}"
description: "Executive-grade implementation guide with governance, architecture, and KPI-driven decision guidance."
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

{title} is not just a technical topic; it is an operational and governance decision. This post is written for CTOs, CEOs, software architects, and tech leads who need consistent outcomes, controlled risk, and measurable business value.

## Executive context
Explain why this topic matters to leadership in measurable terms (risk, cost, delivery speed). Identify the business outcome this topic improves.

## Problem definition
Define the core problem in production terms (reliability, compliance, cost, latency). Provide a real-world framing rather than a theoretical one.

## Architecture and operating model
Provide an architecture view with clear components, ownership boundaries, and critical interfaces. Highlight where control points should be enforced.

## Governance and policy controls
List governance controls that prevent risk: allowlists, approval gates, audit logs, and release policies.

## KPI and measurement framework
Define KPIs that leadership will care about. Include a scorecard or dashboard format.

## Implementation roadmap (90 days)
Break down into phases with weekly objectives and measurable outcomes.

## Risks and mitigations
Outline the top risks and how to mitigate each with technical or process controls.

## Practical checklist
Include a checklist to drive implementation discipline.

## Official references
- OpenAI docs: https://platform.openai.com/docs
- OpenTelemetry docs: https://opentelemetry.io/docs/
- Cloudflare Workers docs: https://developers.cloudflare.com/workers/

## Final recommendation
Summarize the strategic guidance in 3–5 sentences, framed for executives.
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
    # Word count check (soft enforcement)
    import re
    wc = len(re.findall(r"\b\w+\b", content))
    if wc < 1200 or wc > 1800:
        print(f"WARNING: Generated post word count {wc} outside 1200-1800 range")


    subprocess.run(['git', '-C', str(ROOT), 'add', str(out)], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'commit', '-m', f'content(auto): add recurring post {fname}'], check=True)
    subprocess.run(['bash', '-lc', "GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_github_openclaw -o IdentitiesOnly=yes' git -C /home/dev/workspace/blogbot push origin main"], check=True)
    print(f'Created and pushed: {out}')


if __name__ == '__main__':
    main()
