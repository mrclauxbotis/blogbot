#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timedelta, timezone
import re
import subprocess

ROOT = Path('/home/dev/workspace/blogbot')
POSTS = ROOT / 'content' / 'posts'

TOPICS = [
    # Domain 1: Agentic Architecture & Orchestration
    ("Agentic Architecture", "Building Production Agentic Loops: stop_reason, Tool Execution, and Loop Control"),
    ("Multi-Agent Systems", "Coordinator-Subagent Patterns: Designing Hub-and-Spoke Agent Orchestration"),
    ("Agent Workflows", "Programmatic Enforcement vs Prompt Guidance: When LLM Compliance Isn't Enough"),
    ("Agent SDK Hooks", "Intercepting Tool Calls with Agent SDK Hooks: Data Normalization and Policy Gates"),
    ("Task Decomposition", "Prompt Chaining vs Dynamic Decomposition: Choosing the Right Workflow Pattern"),
    ("Session Management", "Session Resumption, Forking, and State Recovery in Long-Running Agents"),

    # Domain 2: Tool Design & MCP Integration
    ("MCP Tools", "Designing MCP Tool Interfaces That LLMs Actually Select Correctly"),
    ("MCP Error Handling", "Structured Error Responses for MCP Tools: Beyond 'Operation Failed'"),
    ("Tool Distribution", "Tool Overload Is Real: Scoping Agent Tool Access for Reliable Selection"),
    ("MCP Configuration", "MCP Server Scoping in Claude Code: Project vs User Level Configuration"),
    ("Built-in Tools", "Grep vs Glob vs Read: Selecting the Right Built-in Tool for Codebase Exploration"),

    # Domain 3: Claude Code Configuration & Workflows
    ("Claude Code Config", "CLAUDE.md Hierarchy Deep Dive: User, Project, and Directory-Level Configuration"),
    ("Claude Code Skills", "Custom Slash Commands and Skills: context:fork, allowed-tools, and Isolation"),
    ("Path-Specific Rules", "Glob-Pattern Rules in .claude/rules/: Conditional Convention Loading That Scales"),
    ("Plan Mode", "Plan Mode vs Direct Execution: A Decision Framework for Claude Code Tasks"),
    ("CI/CD Integration", "Claude Code in CI/CD Pipelines: Non-Interactive Mode, JSON Output, and PR Reviews"),
    ("Iterative Refinement", "Test-Driven Iteration with Claude Code: The Interview Pattern and Beyond"),

    # Domain 4: Prompt Engineering & Structured Output
    ("Prompt Precision", "Explicit Criteria Over Vague Instructions: Reducing False Positives in LLM Reviews"),
    ("Few-Shot Prompting", "Few-Shot Examples That Generalize: Targeting Ambiguity, Not Just Format"),
    ("Structured Output", "Guaranteed Schema Compliance with tool_use: JSON Schemas and tool_choice Patterns"),
    ("Validation Loops", "Retry-with-Feedback Loops: When Retries Work and When They Never Will"),
    ("Batch Processing", "Message Batches API: 50% Cost Savings and When NOT to Use It"),
    ("Multi-Pass Review", "Independent Review Instances Beat Self-Review: Multi-Pass Architectures for Code"),

    # Domain 5: Context Management & Reliability
    ("Context Management", "Lost in the Middle: Managing Context Windows Across Long Agent Interactions"),
    ("Escalation Patterns", "Escalation Calibration: Why Sentiment Scores and Confidence Are Unreliable Proxies"),
    ("Error Propagation", "Error Propagation in Multi-Agent Systems: Structured Context for Coordinator Recovery"),
    ("Codebase Exploration", "Context Degradation in Extended Sessions: Scratchpads, Subagents, and /compact"),
    ("Human Review", "Confidence Calibration and Stratified Sampling: Designing Human Review Workflows"),
    ("Information Provenance", "Preserving Source Attribution Through Multi-Agent Synthesis Pipelines"),
]

TAGS = {
    "Agentic Architecture": ["agentic loops", "stop_reason", "tool execution", "claude agent sdk", "loop control"],
    "Multi-Agent Systems": ["multi-agent", "coordinator", "subagent", "hub-and-spoke", "orchestration"],
    "Agent Workflows": ["programmatic enforcement", "hooks", "prerequisites", "workflow ordering", "handoff"],
    "Agent SDK Hooks": ["PostToolUse", "tool interception", "data normalization", "policy enforcement", "hooks"],
    "Task Decomposition": ["prompt chaining", "dynamic decomposition", "task planning", "code review"],
    "Session Management": ["session resumption", "fork_session", "state persistence", "crash recovery"],
    "MCP Tools": ["mcp", "tool descriptions", "tool selection", "tool design", "model context protocol"],
    "MCP Error Handling": ["isError", "error categories", "retryable", "structured errors", "mcp"],
    "Tool Distribution": ["tool_choice", "scoped tools", "allowedTools", "agent specialization"],
    "MCP Configuration": [".mcp.json", "environment variables", "mcp servers", "project scope", "user scope"],
    "Built-in Tools": ["grep", "glob", "read", "write", "edit", "bash", "codebase exploration"],
    "Claude Code Config": ["CLAUDE.md", "configuration hierarchy", "@import", ".claude/rules/", "claude code"],
    "Claude Code Skills": ["slash commands", "skills", "context:fork", "allowed-tools", "argument-hint"],
    "Path-Specific Rules": ["glob patterns", "YAML frontmatter", "conditional rules", "path scoping"],
    "Plan Mode": ["plan mode", "direct execution", "explore subagent", "architectural decisions", "claude code"],
    "CI/CD Integration": ["ci/cd", "-p flag", "--output-format json", "pr review", "non-interactive mode"],
    "Iterative Refinement": ["test-driven", "interview pattern", "input/output examples", "progressive improvement"],
    "Prompt Precision": ["explicit criteria", "false positives", "review precision", "severity classification"],
    "Few-Shot Prompting": ["few-shot", "examples", "ambiguity", "generalization", "output consistency"],
    "Structured Output": ["tool_use", "json schema", "tool_choice", "structured extraction", "schema design"],
    "Validation Loops": ["retry", "validation", "feedback loops", "self-correction", "pydantic"],
    "Batch Processing": ["message batches api", "custom_id", "cost optimization", "latency tolerance"],
    "Multi-Pass Review": ["self-review", "independent instances", "multi-pass", "attention dilution", "code review"],
    "Context Management": ["context window", "token budget", "progressive summarization", "lost in the middle"],
    "Escalation Patterns": ["escalation", "human-in-the-loop", "ambiguity resolution", "customer support"],
    "Error Propagation": ["error propagation", "partial results", "coordinator recovery", "multi-agent errors"],
    "Codebase Exploration": ["context degradation", "scratchpad", "/compact", "subagent delegation"],
    "Human Review": ["confidence calibration", "stratified sampling", "human review", "accuracy segmentation"],
    "Information Provenance": ["source attribution", "claim-source mapping", "temporal data", "conflict annotation"],
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
    # Word count enforcement (hard)
    import re
    wc = len(re.findall(r"\b\w+\b", content))
    if wc < 1200 or wc > 1800:
        raise RuntimeError(f"Generated post word count {wc} outside 1200-1800 range")


    subprocess.run(['git', '-C', str(ROOT), 'add', str(out)], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'commit', '-m', f'content(auto): add recurring post {fname}'], check=True)
    subprocess.run(['bash', '-lc', "GIT_SSH_COMMAND='ssh -i ~/.ssh/id_ed25519_github_openclaw -o IdentitiesOnly=yes' git -C /home/dev/workspace/blogbot push origin main"], check=True)
    print(f'Created and pushed: {out}')


if __name__ == '__main__':
    main()
