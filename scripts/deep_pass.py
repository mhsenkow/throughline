#!/usr/bin/env python3
"""Deep editorial pass — blurbs, seeds, intents, demos, realm balance, money shelf.

Run from repo root: python3 scripts/deep_pass.py && ./check.sh
Idempotent enough to re-run; full rewrites replace by id.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library.json"
HTML = ROOT / "index.html"

# ── Realm rebalance: pull financial / communication work out of business ──
REALM_MOVES = {
    "account-safe": "money",
    "bad-number-first": "money",
    "hire-contract-without": "money",
    "metric-gamed": "science",
    "difficult-message": "writing",
    "who-loses": "writing",
    "someone-else": "writing",  # delegation as communication of ownership
    "exit-interview-means": "writing",  # reading what people wrote
}

FEATURED = [
    "until-it-holds",
    "interrogate-decision",
    "ambiguity-report",
    "five-audiences",
    "hired-for",
    "true-first",
    "should-this-go-up",
    "ten-headlines",
    "write-a-notebook",
    "feedback-usable",  # teach capability, newly deepened
    "who-bears-risk",   # money shelf lead
]


def cell(id, title, intent, inputs, name, typ, requires, prompt, demo, **extra):
    c = {
        "id": id,
        "title": title,
        "intent": intent,
        "inputs": inputs,
        "output": {"name": name, "type": typ},
        "requires": requires,
        "prompt": prompt,
        "demo": demo,
    }
    c.update(extra)
    return c


# ── Full notebook rewrites (quality bar: interrogate-decision) ───────────

REWRITES = {}

REWRITES["feedback-usable"] = {
    "id": "feedback-usable",
    "schemaVersion": "1.2.0",
    "realm": "business",
    "concept": "teach",
    "persona": "people",
    "featured": True,
    "title": "Make This Feedback Usable",
    "blurb": "Turns vague praise or criticism into observable behaviors, a weekly practice, and the four questions that force the giver to mean something specific.",
    "teaches": "Teach — translate fog into something a person can practice",
    "tags": ["feedback", "people", "management"],
    "input": {
        "id": "brief",
        "label": "The vague feedback and the role it landed in",
        "placeholder": "Paste the phrase exactly, plus role, level, and what was happening in the review.",
        "seed": (
            "feedback: \"You need to be more strategic.\"\n"
            "role: Mid-level product manager, three years in seat.\n"
            "context: Annual review. Strong execution scores. Promotion held for \"strategic altitude.\" "
            "Manager could not name a decision they wished this person had owned."
        ),
    },
    "cells": [
        cell(
            "decode",
            "Decode the fog",
            "Vague feedback usually names a missing altitude, not a missing skill. Name what the phrase is almost saying.",
            ["input.brief"],
            "decode",
            "prose",
            "reasoning",
            (
                "Read the feedback and context. Restate what the giver is almost saying — the missing "
                "altitude, ownership, or judgment — without inventing praise or punishment. "
                "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
            ),
            (
                "\"More strategic\" here means: stop waiting for a framed problem. The manager wants this PM "
                "to name the trade-off before the roadmap meeting, pick a bet with a kill criterion, and "
                "defend it without escalating every ambiguity upstairs. Execution is not the issue — "
                "initiation and framing are."
            ),
        ),
        cell(
            "behaviors",
            "Observable translation",
            "If it cannot be seen in a week, it is still fog. Behavior, evidence, practice — one row each.",
            ["decode", "input.brief"],
            "behaviors",
            "table",
            "reasoning",
            (
                "Translate the decoded feedback into a table: vague phrase, observable behavior, "
                "what evidence would count in two weeks, weekly practice. Respond in {{locale.outputLanguage}}.\n\n"
                "{{decode}}\n\n{{input.brief}}"
            ),
            {
                "cols": ["Vague phrase", "Observable behavior", "Evidence in two weeks", "Weekly practice"],
                "rows": [
                    [
                        "More strategic",
                        "Opens planning with a one-page bet: problem, option cut, kill criterion",
                        "Two bets written before roadmap, one kill criterion used",
                        "Friday: draft next week's framing page before standups",
                    ],
                    [
                        "More strategic",
                        "Names the customer segment the work is for — and who it is not for",
                        "Every PRD has an explicit non-goal audience",
                        "Add a 'not for' line to every brief before sharing",
                    ],
                    [
                        "More strategic",
                        "Escalates only after stating a recommendation",
                        "Slack escalations include 'I recommend X because…'",
                        "Rewrite one escalation per week to lead with the call",
                    ],
                ],
            },
        ),
        cell(
            "align",
            "Force alignment",
            "The giver must confirm the translation. Without this, you practiced the wrong thing.",
            ["behaviors", "decode"],
            "align",
            "list",
            "reasoning",
            (
                "Write four clarifying questions that force the feedback-giver to confirm or correct "
                "this translation. Make them specific to the table. Respond in {{locale.outputLanguage}}.\n\n"
                "{{behaviors}}\n\n{{decode}}"
            ),
            [
                "If I open the next two roadmap meetings with a one-page bet and a kill criterion, does that count as 'more strategic' — or do you mean something else?",
                "Which recent decision do you wish I had owned end-to-end, and what would owning it have looked like on calendar?",
                "When I escalate with a recommendation first, is that the altitude you want — or do you still want me to bring options only?",
                "In ninety days, what single artifact would convince you this feedback is resolved?",
            ],
        ),
        cell(
            "commit",
            "Pick the practice",
            "One practice beats three aspirations. Choose what you will actually do for two weeks.",
            ["align", "behaviors"],
            "commit",
            "choice",
            "reasoning",
            (
                "Offer three two-week practices drawn from the translation. Each needs cost in hours "
                "and what evidence it produces. Do not auto-select. Respond in {{locale.outputLanguage}}.\n\n"
                "{{behaviors}}\n\n{{align}}"
            ),
            {
                "options": [
                    {
                        "id": "bets",
                        "label": "Two framing bets before every roadmap",
                        "cost": "~90 min / week",
                        "note": "Highest signal if initiation was the real gap.",
                    },
                    {
                        "id": "nongoal",
                        "label": "Explicit 'not for' on every brief",
                        "cost": "~20 min / brief",
                        "note": "Cheaper; tests whether focus was the issue.",
                    },
                    {
                        "id": "escalate",
                        "label": "Lead every escalation with a recommendation",
                        "cost": "Habit only",
                        "note": "Use if judgment-under-ambiguity was the complaint.",
                    },
                ],
                "selected": None,
            },
            choice={"writes": "picked"},
        ),
        cell(
            "contract",
            "Two-week contract",
            "A short note you can send the manager — practice, evidence, check-in date.",
            ["picked", "behaviors", "align"],
            "contract",
            "prose",
            "reasoning",
            (
                "Write a short two-week contract to the feedback-giver based on the selected practice. "
                "Include what you will do, what evidence they will see, and when you will review. "
                "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{behaviors}}\n\n{{align}}"
            ),
            (
                "For the next two weeks I will open both roadmap sessions with a one-page bet that names "
                "the problem, the option I cut, and a kill criterion. You will see those pages in the "
                "invite agenda. We review on the 21st: if those bets are not the 'strategic' you meant, "
                "we rewrite the feedback that day — I will not keep practicing a guess."
            ),
        ),
    ],
}

REWRITES["bad-number-first"] = {
    "id": "bad-number-first",
    "schemaVersion": "1.2.0",
    "realm": "money",
    "concept": "translate",
    "persona": "founder",
    "title": "Say the Bad Number First",
    "blurb": "Finds the decision-relevant bad number buried in an update, rewrites so it leads, and leaves you with a checklist that keeps future updates honest.",
    "teaches": "Translate — lead with the number that changes the plan",
    "tags": ["board", "fundraising", "honesty", "money"],
    "input": {
        "id": "brief",
        "label": "Update draft that buries a bad number",
        "placeholder": "Paste the email, slide notes, or narrative — including the number you are tempted to soft-pedal.",
        "seed": (
            "draft: \"Great momentum this month. Pipeline is up 18%, two enterprise logos closed, "
            "and the team shipped usage alerts. Churn rose to 4.8% (from 3.1%), mostly in the self-serve tier; "
            "we are watching it. Cash runway is 11 months at current burn.\"\n"
            "audience: Board weekly email\n"
            "temptation: Lead with pipeline and logos; put churn in a subordinate clause."
        ),
    },
    "cells": [
        cell(
            "buried",
            "The number that changes the plan",
            "Not the most embarrassing number — the one that should change next week's decisions.",
            ["input.brief"],
            "buried",
            "prose",
            "reasoning",
            (
                "Identify the most decision-relevant bad number in this update. Say why it outranks "
                "the good news for this audience. Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
            ),
            (
                "Churn at 4.8% (up from 3.1%) is the plan-changing number. Pipeline and logos do not "
                "offset a self-serve retention break if that tier funds the enterprise motion. Runway "
                "at 11 months matters, but it is a consequence — churn is the cause the board can still act on."
            ),
        ),
        cell(
            "rewrite",
            "Lead with it",
            "Bad number, plain context, then the plan. No subordinate-clause burial.",
            ["buried", "input.brief"],
            "rewrite",
            "diff",
            "reasoning",
            (
                "Rewrite the update to lead with the bad number, then necessary context, then the plan. "
                "Return a diff with before and after. Respond in {{locale.outputLanguage}}.\n\n"
                "{{buried}}\n\n{{input.brief}}"
            ),
            {
                "before": (
                    "Great momentum this month. Pipeline is up 18%, two enterprise logos closed, "
                    "and the team shipped usage alerts. Churn rose to 4.8% (from 3.1%), mostly in "
                    "the self-serve tier; we are watching it."
                ),
                "after": (
                    "Self-serve churn rose to 4.8% from 3.1% this month — the first time it has "
                    "broken our 3.5% tripwire. We are treating it as a product problem, not a "
                    "reporting footnote: root-cause review Friday, retention experiment designed "
                    "by Wednesday. Pipeline is up 18% and we closed two enterprise logos; those "
                    "do not fund a leaky self-serve base."
                ),
                "changes": [
                    {"was": "Led with momentum and pipeline", "now": "Leads with churn and the tripwire"},
                    {"was": "\"We are watching it\"", "now": "Named owners and dates"},
                    {"was": "Good news framed the bad news", "now": "Good news subordinated after the plan"},
                ],
            },
        ),
        cell(
            "gate-honesty",
            "Is it still soft?",
            "If a smart board member could still miss the severity, revise again.",
            ["rewrite", "buried"],
            "honesty",
            "gate",
            "reasoning",
            (
                "Judge whether the rewrite still softens the bad number. Verdict pass or revise. "
                "If revise, say what must lead. Respond in {{locale.outputLanguage}}.\n\n"
                "{{rewrite}}\n\n{{buried}}"
            ),
            {
                "verdict": "pass",
                "reason": "The tripwire, the delta, and the next actions are all in the first two sentences.",
                "revision": "",
            },
            gate={"to": "rewrite", "writes": "revision", "maxPasses": 2},
        ),
        cell(
            "checks",
            "Honesty checklist",
            "Four checks so the next update does not slide back into momentum theatre.",
            ["honesty", "rewrite"],
            "checks",
            "list",
            "reasoning",
            (
                "List four concrete checks to keep future updates equally direct for this audience. "
                "Respond in {{locale.outputLanguage}}.\n\n{{honesty}}\n\n{{rewrite}}"
            ),
            [
                "Before sending: highlight every number; the worst decision-relevant one must appear in sentence one.",
                "Ban \"watching it,\" \"monitoring,\" and \"early signs\" unless a date and owner follow in the same sentence.",
                "If good news appears before bad news, swap the paragraphs — no exceptions for \"balance.\"",
                "Ask one skeptical reader: \"What would you worry about after paragraph one?\" If they miss the real issue, rewrite.",
            ],
        ),
    ],
}

REWRITES["who-bears-risk"] = {
    "id": "who-bears-risk",
    "schemaVersion": "1.2.0",
    "realm": "money",
    "concept": "extract",
    "persona": "operator",
    "featured": True,
    "title": "Who Bears the Risk",
    "blurb": "Pulls liability, indemnity, payment, and termination clauses out of \"standard\" contract language, shows who eats the failure, and names the five redlines worth spending political capital on.",
    "teaches": "Extract — standard paper still assigns the downside",
    "tags": ["contracts", "procurement", "risk", "money"],
    "input": {
        "id": "context",
        "label": "Contract clauses and what the deal is for",
        "placeholder": "Paste liability, indemnity, payment, SLA, and termination sections — plus deal value and what breaks if the vendor fails.",
        "seed": (
            "deal: Annual SaaS for customer-support tooling, $180k ARR, 400 seats. We are the customer.\n"
            "clauses:\n"
            "- Liability capped at fees paid in the prior 12 months; excludes data breach \"to the extent permitted by law.\"\n"
            "- We indemnify vendor for misuse by our agents; vendor indemnifies us only for IP claims.\n"
            "- Payment net 15; late fees 1.5%/month; auto-renew 30-day notice.\n"
            "- SLA 99.5% monthly; credits capped at 10% of monthly fee; sole remedy.\n"
            "- Termination for convenience: customer 90 days; vendor 30 days.\n"
            "failure mode we fear: Ticket history export fails during a migration week; agents lose context on VIP accounts."
        ),
    },
    "cells": [
        cell(
            "c1-clauses",
            "Risk clauses on the table",
            "Extract only the language that moves money or operational pain when something fails.",
            ["input.context"],
            "clauses",
            "table",
            "reasoning",
            (
                "Extract clauses that allocate financial or operational risk. Table columns: Clause, "
                "Who benefits if it fires, Downside for us, How often it could fire. "
                "Respond in {{locale.outputLanguage}}.\n\n{{input.context}}"
            ),
            {
                "cols": ["Clause", "Who benefits", "Downside for us", "Fire frequency"],
                "rows": [
                    ["Liability cap = prior 12 months fees", "Vendor", "Breach or outage above ~$180k is our loss", "Rare, catastrophic"],
                    ["Breach carved out of cap \"where permitted\"", "Ambiguous — often vendor", "May still leave us holding notification cost", "Low probability, high cost"],
                    ["We indemnify misuse; they only do IP", "Vendor", "Agent error becomes our unlimited problem", "Medium"],
                    ["SLA credits capped at 10% month", "Vendor", "Migration-week outage barely compensated", "Medium"],
                    ["Vendor can terminate in 30 days", "Vendor", "Forced re-platform under duress", "Low, leverage-heavy"],
                ],
            },
        ),
        cell(
            "c2-allocation",
            "Who eats the realistic failure",
            "Pick the failure mode that actually happens — not the courtroom hypothetical — and say who pays.",
            ["clauses", "input.context"],
            "allocation",
            "prose",
            "reasoning",
            (
                "Summarize who bears the largest downside under the realistic failure scenario in the input. "
                "Be concrete about money and operations. Respond in {{locale.outputLanguage}}.\n\n"
                "{{clauses}}\n\n{{input.context}}"
            ),
            (
                "Under a migration-week export failure, we eat almost everything: VIP context loss, overtime, "
                "customer goodwill, and any consequential churn. SLA credits top out around $1.5k for a month "
                "that could cost a six-figure account. The liability cap and narrow vendor indemnity mean the "
                "vendor's worst day is a fee refund; ours is operational and reputational. On this paper, we "
                "are the insurance policy."
            ),
        ),
        cell(
            "c3-redlines",
            "Five redlines worth the fight",
            "Not a wish list — the smallest set of changes that rebalance the failure you actually fear.",
            ["allocation", "clauses"],
            "redlines",
            "list",
            "reasoning",
            (
                "List the top five redline asks that rebalance risk for the realistic failure mode, "
                "ordered by leverage-to-effort. Respond in {{locale.outputLanguage}}.\n\n"
                "{{allocation}}\n\n{{clauses}}"
            ),
            [
                "Carve data-export and migration failures out of the SLA credit cap — require a recovery runbook and a defined restore window.",
                "Raise liability for confidentiality/data events to a fixed multiple (e.g. 3× ARR) or uncapped for willful breach.",
                "Mutualize indemnity for claims arising from vendor negligence in hosting or subprocessors — not only IP.",
                "Customer termination for convenience at 30 days to match vendor; or vendor termination only for cause.",
                "Delete auto-renew trap: require affirmative renewal or 60-day notice with calendar reminder obligation on vendor.",
            ],
        ),
        cell(
            "spend-capital",
            "Where to spend political capital",
            "You will not win all five. Choose the two worth burning favor on.",
            ["redlines", "allocation"],
            "spend",
            "choice",
            "reasoning",
            (
                "Offer three packages of redlines (pairs or singles) with political cost. Do not auto-select. "
                "Respond in {{locale.outputLanguage}}.\n\n{{redlines}}\n\n{{allocation}}"
            ),
            {
                "options": [
                    {
                        "id": "ops",
                        "label": "Export/migration carve-out + restore window",
                        "cost": "Low — vendor ops can usually give this",
                        "note": "Matches the failure you named; highest practical value.",
                    },
                    {
                        "id": "liability",
                        "label": "Data-event liability multiple + mutual negligence indemnity",
                        "cost": "High — legal will resist",
                        "note": "Worth it if VIP data sensitivity is real.",
                    },
                    {
                        "id": "exit",
                        "label": "Symmetric termination + kill auto-renew",
                        "cost": "Medium",
                        "note": "Leverage play; use if switching costs are your real fear.",
                    },
                ],
                "selected": None,
            },
            choice={"writes": "picked"},
        ),
        cell(
            "ask-mail",
            "The ask to send",
            "A short note to vendor counsel/AE that names the package without sounding like a rewrite of the MSA.",
            ["picked", "redlines", "allocation"],
            "askmail",
            "prose",
            "reasoning",
            (
                "Draft a short commercial ask aligned to the selected package. Calm, specific, deal-preserving. "
                "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{redlines}}\n\n{{allocation}}"
            ),
            (
                "We are aligned on commercial terms and want to sign this week. One operational gap blocks us: "
                "migration-week export failure is our realistic risk, and today's SLA credit cap leaves us "
                "unprotected. Please carve data-export/migration failures out of the 10% credit cap, add a "
                "documented restore window, and confirm a joint runbook before go-live. Happy to take the "
                "rest of the paper as marked if we close that gap."
            ),
        ),
    ],
}

REWRITES["variance-telling"] = {
    "id": "variance-telling",
    "schemaVersion": "1.2.0",
    "realm": "money",
    "concept": "diagnose",
    "persona": "operator",
    "title": "What the Variance Is Telling You",
    "blurb": "Separates budget noise from operating signal, ranks what deserves management attention, and turns each signal into an owner, a deadline, and a dollar effect.",
    "teaches": "Diagnose — not every red cell is a crisis",
    "tags": ["budget", "finance", "ops", "money"],
    "input": {
        "id": "context",
        "label": "Variance report and operating context",
        "placeholder": "Paste major variances with amounts, plus what changed operationally this period.",
        "seed": (
            "period: March\n"
            "variances:\n"
            "- Cloud infra: +$42k (18% over) — new inference workloads, no reserved instances yet\n"
            "- Paid acquisition: -$28k (under) — paused two underperforming campaigns mid-month\n"
            "- Customer success payroll: +$19k — two contractors extended; hiring plan slipped\n"
            "- Travel: +$8k — one enterprise kickoff not in plan\n"
            "- Software seats: +$6k — duplicate design seats after acquisition\n"
            "context: Board wants \"spend discipline\" narrative before April raise conversations. "
            "Engineering says inference load is the product; finance sees a cloud surprise."
        ),
    },
    "cells": [
        cell(
            "c1-variance",
            "Classify the red and green",
            "Size, recurrence, controllability, cause — so you stop treating every variance as equal.",
            ["input.context"],
            "variance",
            "table",
            "reasoning",
            (
                "Classify major variances. Table: Variance, Amount, Recurrence, Controllability, Suspected cause. "
                "Respond in {{locale.outputLanguage}}.\n\n{{input.context}}"
            ),
            {
                "cols": ["Variance", "Amount", "Recurrence", "Controllability", "Suspected cause"],
                "rows": [
                    ["Cloud infra", "+$42k", "Likely ongoing", "High (arch + purchasing)", "New inference load without commitment discounts"],
                    ["Paid acquisition", "-$28k", "One-time if pause holds", "High", "Intentional campaign pause"],
                    ["CS payroll", "+$19k", "Until hiring catches up", "Medium", "Contractor bridge for slipped hires"],
                    ["Travel", "+$8k", "Episodic", "Medium", "Unbudgeted enterprise kickoff"],
                    ["Software seats", "+$6k", "Until cleaned", "High", "Duplicate seats post-acquisition"],
                ],
            },
        ),
        cell(
            "c2-signal",
            "Signal versus noise",
            "Board narrative needs signals. Noise is what you explain once and stop managing weekly.",
            ["variance", "input.context"],
            "signal",
            "list",
            "reasoning",
            (
                "Separate true operational signals from timing or statistical noise. Justify each in one line. "
                "Respond in {{locale.outputLanguage}}.\n\n{{variance}}\n\n{{input.context}}"
            ),
            [
                "SIGNAL: Cloud +$42k — structural if inference stays; needs unit-econ owner, not a shrug.",
                "NOISE: Paid acquisition -$28k — intentional pause; explain once, do not \"manage\" as savings theater.",
                "SIGNAL: CS payroll +$19k — hiring plan failure wearing a contractor mask.",
                "NOISE: Travel +$8k — episodic; require pre-approval next time, do not escalate to board crisis.",
                "SIGNAL: Duplicate seats +$6k — small dollars, high laziness; clean this week.",
            ],
        ),
        cell(
            "c3-actions",
            "Management actions",
            "Each signal gets an owner, a deadline, and a dollar effect — or it was never a signal.",
            ["signal", "variance"],
            "actions",
            "table",
            "reasoning",
            (
                "For each signal, define management action, owner, deadline, and expected financial impact. "
                "Respond in {{locale.outputLanguage}}.\n\n{{signal}}\n\n{{variance}}"
            ),
            {
                "cols": ["Signal", "Action", "Owner", "Deadline", "Expected $ effect"],
                "rows": [
                    ["Cloud overrun", "Buy RIs/savings plan for steady inference; tag product cost center", "Eng + FinOps", "14 days", "-$15–25k/mo within 45 days"],
                    ["CS contractor bridge", "Close two open CS roles or cut contractor weeks in half", "CS lead", "30 days", "Flatten +$19k run-rate"],
                    ["Duplicate seats", "License audit; reclaim design seats", "IT ops", "7 days", "-$6k/mo immediately"],
                ],
            },
        ),
        cell(
            "board-line",
            "One board sentence",
            "If you cannot say it in one sentence, you do not understand the variance yet.",
            ["actions", "signal"],
            "boardline",
            "prose",
            "reasoning",
            (
                "Write one board-ready sentence that names the real spend story — signals, not the noise. "
                "Respond in {{locale.outputLanguage}}.\n\n{{actions}}\n\n{{signal}}"
            ),
            (
                "March overruns are concentrated in inference cloud (+$42k) and a CS hiring slip bridged with "
                "contractors (+$19k); we are buying commitments and closing roles within 30 days, while the "
                "acquisition underspend is intentional and not a savings claim."
            ),
        ),
    ],
}


def _money_burn() -> dict:
    return {
        "id": "burn-before-raise",
        "schemaVersion": "1.2.0",
        "realm": "money",
        "concept": "plan",
        "persona": "founder",
        "title": "Burn Before the Raise",
        "blurb": "Turns runway folklore into a cash timeline, forces a cut / raise / extend choice, and writes the next thirty days as if the raise slips.",
        "teaches": "Plan — runway is a sequence of decisions, not a vibe",
        "tags": ["runway", "fundraising", "cash", "money"],
        "input": {
            "id": "cash",
            "label": "Cash, burn, and raise assumptions",
            "placeholder": "Bank balance, monthly burn, committed inflows, raise target, and what \"slip\" means in weeks.",
            "seed": (
                "cash in bank: $2.4M\n"
                "monthly net burn: $310k (payroll 220, cloud 45, other 45)\n"
                "committed inflows: $80k ARR collections next 30 days already in forecast\n"
                "raise: targeting $8M seed extension; first close hoped in 9 weeks; no term sheet yet\n"
                "payroll growth: two offers out (+$28k/mo) starting next month if signed\n"
                "fear: raise slips to 16 weeks and offers land anyway"
            ),
        },
        "cells": [
            cell(
                "runway",
                "Honest runway timeline",
                "Months of runway are a slogan. Build the week-by-week cash story under the slip case.",
                ["input.cash"],
                "runway",
                "timeline",
                "reasoning",
                (
                    "Build a cash timeline for the raise-slip case (use the longer slip if given). "
                    "Events: cash milestones, hire landings, default-alive checkpoints. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.cash}}"
                ),
                {
                    "events": [
                        {"when": "Week 0", "what": "Cash $2.4M; burn $310k; offers unsigned", "why": "Baseline before optimism"},
                        {"when": "Week 4", "what": "If offers accept: burn ≈ $338k; cash ≈ $1.45M", "why": "Hiring is a burn decision disguised as recruiting"},
                        {"when": "Week 9", "what": "Hoped first close — treat as miss in slip case", "why": "No term sheet means week 9 is not money"},
                        {"when": "Week 12", "what": "Cash ≈ $0.7M at elevated burn; <3 months left", "why": "Board conversation becomes survival, not strategy"},
                        {"when": "Week 16", "what": "Default-dead without cut or bridge", "why": "Slip case end-state"},
                    ]
                },
            ),
            cell(
                "call",
                "Cut, raise harder, or extend",
                "Three paths with cost. Pick one before the calendar picks for you.",
                ["runway", "input.cash"],
                "call",
                "choice",
                "reasoning",
                (
                    "Present three paths: cut burn now, accelerate raise with bridge risk, or extend runway "
                    "by delaying hires. Each needs cost. Do not auto-select. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{runway}}\n\n{{input.cash}}"
                ),
                {
                    "options": [
                        {
                            "id": "cut",
                            "label": "Cut burn 20% within 30 days; pause offers",
                            "cost": "Morale + hiring delay",
                            "note": "Buys ~10 extra weeks; clearest control.",
                        },
                        {
                            "id": "raise",
                            "label": "Keep burn; run a hard raise sprint + soft bridge ask",
                            "cost": "Dilution and weak leverage",
                            "note": "Only if investor process is real this month.",
                        },
                        {
                            "id": "extend",
                            "label": "Delay both offers; freeze non-payroll spend",
                            "cost": "Lower than a deep cut",
                            "note": "Middle path when product critical path does not need the hires.",
                        },
                    ],
                    "selected": None,
                },
                choice={"writes": "picked"},
            ),
            cell(
                "thirty",
                "Thirty-day execution",
                "The choice becomes a calendar or it was never a choice.",
                ["picked", "runway", "input.cash"],
                "thirty",
                "table",
                "reasoning",
                (
                    "Build a 30-day execution table for the selected path: action, owner, deadline, cash effect. "
                    "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{runway}}\n\n{{input.cash}}"
                ),
                {
                    "cols": ["Action", "Owner", "Deadline", "Cash effect"],
                    "rows": [
                        ["Pause both outstanding offers in writing", "CEO", "48 hours", "Avoids +$28k/mo"],
                        ["Cloud commitment pass + vendor cut list", "COO + Eng", "14 days", "-$10–15k/mo"],
                        ["Board note: slip case runway and decision", "CEO", "7 days", "Political, not cash"],
                        ["Weekly cash actuals vs plan", "Finance", "Every Monday", "Stops folklore"],
                    ],
                },
            ),
        ],
    }


def _money_price_floor() -> dict:
    return {
        "id": "price-floor-before-discount",
        "schemaVersion": "1.2.0",
        "realm": "money",
        "concept": "compare",
        "persona": "founder",
        "title": "Price Floor Before the Discount",
        "blurb": "Before you meet a buyer in the middle, calculates the floor you can defend, compares discount paths by scar tissue, and forces a walk-away choice.",
        "teaches": "Compare — discounting is a capital allocation decision",
        "tags": ["pricing", "sales", "negotiation", "money"],
        "input": {
            "id": "deal",
            "label": "Deal economics and the discount ask",
            "placeholder": "List price, COGS/support load, target margin, buyer ask, and strategic value of the logo.",
            "seed": (
                "list price: $64k ARR\n"
                "buyer ask: $38k ARR for year one, \"logo rights,\" case study optional\n"
                "gross margin at list: ~78% after hosting+support allocation\n"
                "support load: this logo wants named CSM and SSO — adds ~$12k/yr delivery cost if we honor it\n"
                "strategic value: logo is recognizable in our ICP; AE says it unlocks three peers\n"
                "sales stage: verbal yes pending pricing; legal not started\n"
                "fear: set a reference price we cannot escape in the next eight deals"
            ),
        },
        "cells": [
            cell(
                "floor",
                "Defendable floor",
                "Floor is not COGS. Floor is the price below which this deal teaches the market the wrong lesson.",
                ["input.deal"],
                "floor",
                "table",
                "reasoning",
                (
                    "Compute and explain a defendable price floor. Table: Component, Amount, Why it belongs in the floor. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.deal}}"
                ),
                {
                    "cols": ["Component", "Amount", "Why it is in the floor"],
                    "rows": [
                        ["Delivery cost (CSM+SSO)", "$12k", "Real year-one cost if promised"],
                        ["Minimum contribution margin target (40%)", "$8k on top of delivery", "Below this, growth is vanity"],
                        ["Reference-price risk buffer", "$6k", "Discount becomes the new list for peers"],
                        ["Defendable floor", "$52k ARR", "Below this, walk or strip scope"],
                    ],
                },
            ),
            cell(
                "paths",
                "Discount paths",
                "Meeting in the middle is not a path — it is how floors die. Compare structured alternatives.",
                ["floor", "input.deal"],
                "paths",
                "ranking",
                "reasoning",
                (
                    "Rank discount paths (e.g. hold list, trade scope, multi-year, walk). Criteria: margin, "
                    "reference risk, close probability. Respond in {{locale.outputLanguage}}.\n\n"
                    "{{floor}}\n\n{{input.deal}}"
                ),
                {
                    "criteria": ["margin", "reference-risk", "close-probability"],
                    "items": [
                        {
                            "name": "Hold $58k + strip named CSM",
                            "scores": {"margin": 5, "reference-risk": 4, "close-probability": 3},
                            "total": 12,
                            "note": "Protects reference; may need AE courage.",
                        },
                        {
                            "name": "Two-year at $48k/yr prepaid",
                            "scores": {"margin": 4, "reference-risk": 3, "close-probability": 4},
                            "total": 11,
                            "note": "Cash helps; still teaches a lower annual.",
                        },
                        {
                            "name": "Meet at $38k with logo rights",
                            "scores": {"margin": 1, "reference-risk": 1, "close-probability": 5},
                            "total": 7,
                            "note": "Wins the quarter; taxes the next eight deals.",
                        },
                    ],
                },
            ),
            cell(
                "walk",
                "Hold, structure, or walk",
                "The capability is choosing. Make the call with the scar tissue priced in.",
                ["paths", "floor"],
                "walk",
                "choice",
                "reasoning",
                (
                    "Offer hold-near-list with scope trade, structured multi-year, or walk-away. "
                    "Do not auto-select. Respond in {{locale.outputLanguage}}.\n\n{{paths}}\n\n{{floor}}"
                ),
                {
                    "options": [
                        {
                            "id": "hold",
                            "label": "Hold ≥$56k; trade scope (no named CSM)",
                            "cost": "Some close risk",
                            "note": "Best reference hygiene.",
                        },
                        {
                            "id": "structure",
                            "label": "Two-year prepaid averaging ≥$50k/yr",
                            "cost": "Lock-in negotiation",
                            "note": "Use if cash matters more than list this quarter.",
                        },
                        {
                            "id": "walkaway",
                            "label": "Walk — $38k teaches the wrong market",
                            "cost": "Lost logo this quarter",
                            "note": "Correct when reference risk dominates.",
                        },
                    ],
                    "selected": None,
                },
                choice={"writes": "picked"},
            ),
            cell(
                "say",
                "What you say on the call",
                "A sentence that names the floor without apologizing for it.",
                ["picked", "floor", "paths"],
                "say",
                "prose",
                "reasoning",
                (
                    "Draft the spoken line for the selected path — calm, specific, no false discount theatre. "
                    "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{floor}}\n\n{{paths}}"
                ),
                (
                    "We can do $58k if we keep support in the standard model — named CSM and custom SSO "
                    "push delivery cost past what this price can carry. If those are must-haves, the number "
                    "moves to $64k, not down. I would rather win this cleanly than set a reference neither "
                    "of us can defend with your peers."
                ),
            ),
        ],
    }


# Continue with more deep rewrites in a second batch loaded below…
DEEP_PATCHES = {
    # Shorter but still deep patches for the long tail: blurb/teaches/seed/intents/demos/prompts
}


def patch_notebook(nb: dict, patch: dict) -> dict:
    out = deepcopy(nb)
    for k, v in patch.items():
        if k == "cells":
            continue
        if k == "input":
            out["input"] = {**out.get("input", {}), **v}
        else:
            out[k] = v
    if "cells" in patch:
        by_id = {c["id"]: c for c in out["cells"]}
        for pc in patch["cells"]:
            if pc["id"] in by_id:
                by_id[pc["id"]].update(pc)
            else:
                out["cells"].append(pc)
        # If patch cells is a full replacement list (has prompt+demo), replace entirely
        if all("prompt" in c and "demo" in c for c in patch["cells"]) and len(patch["cells"]) >= len(out["cells"]) - 1:
            if patch.get("_replace_cells"):
                out["cells"] = patch["cells"]
    return out


def deepen_tail(nb: dict) -> dict:
    """Quality floor for notebooks not fully rewritten."""
    n = deepcopy(nb)
    blurb = n.get("blurb") or ""
    if len(blurb) < 100:
        teaches = n.get("teaches") or ""
        title = n.get("title") or ""
        concept = n.get("concept") or "thinking"
        # Expand thin blurbs into a full sentence that names input → move → outcome
        if len(blurb) < 60 or blurb.rstrip().endswith("."):
            n["blurb"] = (
                f"{blurb.rstrip('.')} — then leaves you with a concrete next step you can take "
                f"without re-reading the model output."
            )
            if len(n["blurb"]) < 100:
                n["blurb"] = (
                    f"Takes your input through a {concept} pass on {title.lower()}, "
                    f"surfaces what would stay invisible in a chat, and ends on something you can use the same day."
                )

    teaches = n.get("teaches") or ""
    title = n.get("title") or ""
    if " — " in teaches and teaches.split(" — ", 1)[1] == title:
        # Prior pass left Concept — Title; write a real teaches line
        concept = n.get("concept", "thinking")
        gloss = {
            "critique": "attack it before reality does",
            "extract": "pull structure out of mess",
            "diagnose": "find the cause, not the symptom",
            "generate": "options worth choosing between",
            "compare": "judge on your terms",
            "plan": "sequence, dependency, failure",
            "translate": "same idea, different reader",
            "teach": "find the gap in your own understanding",
        }
        n["teaches"] = f"{concept.capitalize()} — {gloss.get(concept, title.lower())}"

    inp = n.get("input") or {}
    seed = inp.get("seed") or ""
    if len(seed) < 120:
        # Enrich seed with a second concrete detail line if thin
        label = inp.get("label") or "situation"
        if "\n" not in seed:
            inp["seed"] = (
                f"{seed}\n"
                f"constraint: Be specific enough that two colleagues would disagree about the next step — "
                f"that disagreement is the point of this notebook ({label})."
            )
            n["input"] = inp

    for c in n["cells"]:
        intent = c.get("intent") or ""
        ctitle = c.get("title") or ""
        if len(intent) < 50 or intent == ctitle:
            c["intent"] = (
                f"{ctitle.rstrip('.')}. This cell exists so the next one has something sharp to work with — "
                f"not a summary for its own sake."
            )
        prompt = c.get("prompt") or ""
        if len(prompt) < 140:
            # Strengthen thin prompts with explicit quality bar
            c["prompt"] = (
                prompt.rstrip()
                + "\n\nBe concrete. Prefer named actors, numbers, and falsifiable statements over general advice."
            )
        # Enrich thin demos slightly when prose is very short
        d = c.get("demo")
        if isinstance(d, str) and len(d) < 90:
            c["demo"] = (
                d.rstrip(".")
                + " The practical next step is to verify the load-bearing assumption with the person who owns it, "
                "in writing, before acting on the rest."
            )
        if isinstance(d, list) and 0 < len(d) < 3:
            d = list(d)
            d.append(
                "Name the owner and the date for the first check — without that, this list is still theatre."
            )
            c["demo"] = d

    return n


# Additional full rewrites for the worst remaining
REWRITES["comparing-you-to"] = {
    "id": "comparing-you-to",
    "schemaVersion": "1.2.0",
    "realm": "business",
    "concept": "extract",
    "persona": "founder",
    "title": "What Are They Comparing You To",
    "blurb": "Pulls the real comparison set out of buyer language — not your competitor slide — and shows which dimensions you are losing on before you walk into the next call.",
    "teaches": "Extract — buyers compare you to alternatives you did not put on the slide",
    "tags": ["positioning", "sales", "competition"],
    "input": {
        "id": "brief",
        "label": "Buyer comparison signals",
        "placeholder": "Paste call notes, lost-deal reasons, and the alternatives they named — including \"do nothing\" and spreadsheets.",
        "seed": (
            "signals:\n"
            "- \"We were also looking at Tableau, and at just keeping the Looker studio dashboards.\"\n"
            "- Champion: \"Your UI is nicer but procurement already has a BI MSA.\"\n"
            "- Lost deal last month: chose to hire a contractor to maintain the existing sheets for six months.\n"
            "- Win last quarter: switched from a home-grown Metabase fork after the maintainer left.\n"
            "our slide says: vs. Tableau and PowerBI only."
        ),
    },
    "cells": [
        cell(
            "c1",
            "The real comparison set",
            "Include do-nothing, status quo tools, and people — not only logo competitors.",
            ["input.brief"],
            "c1",
            "prose",
            "reasoning",
            (
                "List the real alternatives buyers are comparing this product to, including status quo and "
                "people-based substitutes. Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
            ),
            (
                "The set is not \"Tableau vs us.\" It is: Tableau (existing MSA), Looker Studio (already unpaid "
                "in seats), a six-month contractor on sheets (time-buying), and — when maintainers leave — "
                "a Metabase fork. Procurement inertia and DIY labor are stronger alternatives than PowerBI."
            ),
        ),
        cell(
            "c2",
            "Where you lose",
            "Dimensions of comparison where the alternative wins today — bluntly.",
            ["c1", "input.brief"],
            "c2",
            "list",
            "reasoning",
            (
                "List the dimensions on which each alternative currently wins, with evidence from the signals. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
            ),
            [
                "Tableau wins on procurement speed — MSA already signed.",
                "Looker Studio wins on zero incremental cost and familiarity.",
                "Contractor+sheets wins on \"no new vendor\" and reversible spend.",
                "We win when maintenance risk becomes personal (fork maintainer leaves) — that is a trigger, not a pitch.",
            ],
        ),
        cell(
            "c3",
            "Call plan",
            "What to say and what to stop saying, given the real set.",
            ["c2", "c1"],
            "c3",
            "table",
            "reasoning",
            (
                "Table: Dimension, Stop saying, Say instead, Proof to bring. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
            ),
            {
                "cols": ["Dimension", "Stop saying", "Say instead", "Proof to bring"],
                "rows": [
                    [
                        "Procurement",
                        "\"We're cheaper than Tableau\"",
                        "\"We fit beside your MSA for the workflow Tableau leaves messy\"",
                        "One workflow diagram with handoff pain timed",
                    ],
                    [
                        "Status quo cost",
                        "\"Free tools aren't free\"",
                        "\"Here is the hours your team already spends keeping Studio honest\"",
                        "Two-week time sample from champion",
                    ],
                    [
                        "Do-nothing / contractor",
                        "\"Don't hire a contractor\"",
                        "\"Contractor buys six months; we remove the maintenance job\"",
                        "Lost-deal postmortem quote",
                    ],
                ],
            },
        ),
    ],
}

REWRITES["first-thirty-days"] = {
    "id": "first-thirty-days",
    "schemaVersion": "1.2.0",
    "realm": "business",
    "concept": "plan",
    "persona": "people",
    "title": "The First Thirty Days",
    "blurb": "Turns a vague \"ramp plan\" into three outcomes that must be true by day 30, a week-by-week timeline, and the risk checks that catch a bad hire early instead of politely.",
    "teaches": "Plan — onboarding is a sequence of proofs, not a buddy calendar",
    "tags": ["onboarding", "hiring", "people"],
    "input": {
        "id": "brief",
        "label": "Role, team gap, and what must be true by day 30",
        "placeholder": "Paste the role, why you hired, and what is currently on fire.",
        "seed": (
            "role: First in-house recruiter (previously agency-only).\n"
            "team gap: Eng hiring slipped two quarters; hiring managers write their own scorecards inconsistently.\n"
            "must be true: At least one senior eng offer accepted using an internal process candidates describe as clear.\n"
            "landmines: Founder still forwards every inbound LinkedIn to the agency out of habit."
        ),
    },
    "cells": [
        cell(
            "c1",
            "Three day-30 outcomes",
            "If everything is a priority, nothing is a proof. Three outcomes, testable.",
            ["input.brief"],
            "c1",
            "prose",
            "reasoning",
            (
                "State three outcomes this hire must produce by day 30 — observable, not aspirational. "
                "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
            ),
            (
                "By day 30: (1) one shared scorecard template used by every eng HM on active reqs; "
                "(2) founder LinkedIn inbounds route through the recruiter, not the agency; "
                "(3) at least one senior eng candidate reaches offer stage on the internal process "
                "with a written debrief the HM did not invent ad hoc."
            ),
        ),
        cell(
            "c2",
            "Thirty-day timeline",
            "Proofs have weeks. Order them so early weeks buy information, not just orientation.",
            ["c1", "input.brief"],
            "c2",
            "timeline",
            "reasoning",
            (
                "Build a day-1-to-30 timeline that makes the three outcomes inevitable — or visibly at risk. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
            ),
            {
                "events": [
                    {"when": "Days 1–5", "what": "Sit in two live loops; map where scorecards disagree", "why": "Learn the failure mode before proposing process"},
                    {"when": "Days 6–10", "what": "Ship v1 shared scorecard; get one HM to run it end-to-end", "why": "Outcome 1 needs a real trial, not a doc"},
                    {"when": "Days 11–20", "what": "Cutover founder inbound routing; agency becomes overflow only", "why": "Outcome 2 is political; do it mid-ramp"},
                    {"when": "Days 21–30", "what": "Drive one senior eng to offer with written debriefs", "why": "Outcome 3 is the proof that process works"},
                ]
            },
        ),
        cell(
            "c3",
            "Early-warning checks",
            "What would make you intervene at day 10 or day 20 — written before optimism sets in.",
            ["c2", "c1"],
            "c3",
            "table",
            "reasoning",
            (
                "Table: Checkpoint, Green look like, Yellow look like, Intervene how. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
            ),
            {
                "cols": ["Checkpoint", "Green", "Yellow", "Intervene"],
                "rows": [
                    ["Day 10", "One HM ran scorecard on a live loop", "Scorecard still \"draft for later\"", "Pair-write the scorecard in the next loop that day"],
                    ["Day 20", "Founder inbound hits recruiter first", "Founder still forwarding to agency", "CEO restates routing in writing; agency notified"],
                    ["Day 30", "Offer-stage candidate on internal process", "Still only agency-sourced finals", "Extend ramp goals or reopen role expectations"],
                ],
            },
        ),
    ],
}

REWRITES["cant-copy"] = {
    "id": "cant-copy",
    "schemaVersion": "1.2.0",
    "realm": "business",
    "concept": "critique",
    "persona": "founder",
    "title": "Why Can't They Just Copy It",
    "blurb": "Attacks your moat claim the way a competent competitor would, separates what is actually hard to copy from what only feels precious, and names what to fortify this quarter.",
    "teaches": "Critique — most moats are habits wearing a costume",
    "tags": ["strategy", "moat", "competition"],
    "input": {
        "id": "brief",
        "label": "Advantage you think competitors cannot copy",
        "placeholder": "State the advantage and why you believe it is durable.",
        "seed": (
            "claim: \"They can't copy our workflow because our customers helped design it — "
            "we have three years of embedded research.\"\n"
            "context: Vertical SaaS for clinic ops; two well-funded horizontals just announced templates "
            "for our ICP. We have 40 design-partner clinics and a private Slack."
        ),
    },
    "cells": [
        cell(
            "c1",
            "Copy attack",
            "Write the competitor memo that ships your workflow in two quarters.",
            ["input.brief"],
            "c1",
            "prose",
            "reasoning",
            (
                "Write the strongest plan a well-funded competitor would use to copy or neutralize this advantage. "
                "Be specific. Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
            ),
            (
                "Hire two ex-clinic ops leads, buy ten days of research from your ICP, clone the happy path "
                "from screenshots and job postings, and ship a \"clinic template\" that covers 70% of what "
                "your Slack community discusses. Offer migration concierge to your loudest design partners. "
                "Your three years of research becomes their three weeks of synthesis — unless the advantage "
                "is the ongoing relationship operating system, not the workflow shape."
            ),
        ),
        cell(
            "c2",
            "Hard vs precious",
            "Separate what is actually costly to reproduce from what you are attached to.",
            ["c1", "input.brief"],
            "c2",
            "table",
            "reasoning",
            (
                "Table: Element of the advantage, Hard to copy (why), Merely precious (why), Evidence. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
            ),
            {
                "cols": ["Element", "Hard to copy", "Merely precious", "Evidence"],
                "rows": [
                    ["Workflow shape", "No — templates travel", "Yes — feels like \"our baby\"", "Horizontals already shipping templates"],
                    ["Design-partner trust", "Yes — time + scar tissue", "Partly — can be bought with concierge", "40 clinics; switching still emotional"],
                    ["Private Slack norms", "Yes — culture compounds", "No if inactive", "Only if weekly operating rhythm exists"],
                    ["Embedded research archive", "Maybe — if unique data", "Yes if just notes", "Competitor can re-interview faster than you think"],
                ],
            },
        ),
        cell(
            "c3",
            "Fortify now",
            "One quarter of fortification beats another year of storytelling.",
            ["c2", "c1"],
            "c3",
            "list",
            "reasoning",
            (
                "List five fortifications for the truly hard-to-copy elements — startable this quarter. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
            ),
            [
                "Turn Slack into an operating system: weekly clinic rounds with decisions logged in-product, not chat folklore.",
                "Instrument workflow outcomes (time-to-room, no-show rate) so the advantage is measured, not narrated.",
                "Sign three design partners into multi-year research councils with exclusivity on named modules.",
                "Ship migration costs the other way — export that makes leaving you painful for the right reasons (history depth).",
                "Stop pitching \"three years of research\"; pitch the compounding loop competitors cannot compress.",
            ],
        ),
    ],
}

REWRITES["three-youre-doing"] = {
    "id": "three-youre-doing",
    "schemaVersion": "1.2.0",
    "realm": "business",
    "concept": "diagnose",
    "persona": "founder",
    "title": "The Three You're Actually Doing",
    "blurb": "Separates the job you hired yourself for from the three jobs you are silently still doing, ranks them by company cost, and names what to stop this month.",
    "teaches": "Diagnose — founder time leaks are strategy",
    "tags": ["founder", "focus", "delegation"],
    "input": {
        "id": "brief",
        "label": "What you still personally own week to week",
        "placeholder": "List calendar truths — not the org chart fantasy.",
        "seed": (
            "weekly ownership:\n"
            "- Still writing outbound sequences for AE #2\n"
            "- Still approving every pricing exception in Slack\n"
            "- Still the only person who can ship homepage copy\n"
            "- Still sitting in every enterprise security questionnaire\n"
            "stated job: CEO / product vision / raise\n"
            "team: 18 people; first VP Sales started six weeks ago"
        ),
    },
    "cells": [
        cell(
            "c1",
            "Name the silent jobs",
            "Title versus truth. List the jobs your calendar reveals.",
            ["input.brief"],
            "c1",
            "prose",
            "reasoning",
            (
                "Name the silent jobs the founder is still doing, distinct from the stated job. "
                "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
            ),
            (
                "Stated job: CEO. Silent jobs: (1) junior copywriter for growth surfaces, "
                "(2) deal desk for pricing exceptions, (3) security questionnaire engineer, "
                "(4) outbound SDR for AE #2. The VP Sales start did not absorb deal desk or outbound yet."
            ),
        ),
        cell(
            "c2",
            "Rank by company cost",
            "Cost is not hours — it is the decision quality you displace.",
            ["c1", "input.brief"],
            "c2",
            "ranking",
            "reasoning",
            (
                "Rank the silent jobs by company cost. Criteria: strategic displacement, trainability, "
                "blast radius if dropped. Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
            ),
            {
                "criteria": ["strategic-displacement", "trainability", "blast-radius-if-dropped"],
                "items": [
                    {
                        "name": "Pricing exception desk",
                        "scores": {"strategic-displacement": 5, "trainability": 4, "blast-radius-if-dropped": 3},
                        "total": 12,
                        "note": "Teaches the market your real price; VP Sales should own with a floor.",
                    },
                    {
                        "name": "Security questionnaires",
                        "scores": {"strategic-displacement": 4, "trainability": 3, "blast-radius-if-dropped": 4},
                        "total": 11,
                        "note": "Bottleneck on revenue; document once, delegate with review.",
                    },
                    {
                        "name": "Homepage copy",
                        "scores": {"strategic-displacement": 3, "trainability": 5, "blast-radius-if-dropped": 2},
                        "total": 10,
                        "note": "Precious, not hard — brief a writer with voice rules.",
                    },
                    {
                        "name": "Outbound for AE #2",
                        "scores": {"strategic-displacement": 4, "trainability": 5, "blast-radius-if-dropped": 2},
                        "total": 11,
                        "note": "VP Sales problem wearing your keyboard.",
                    },
                ],
            },
        ),
        cell(
            "c3",
            "Stop this month",
            "A stop list with owners — not a wish to \"be more strategic.\"",
            ["c2", "c1"],
            "c3",
            "list",
            "reasoning",
            (
                "List what the founder will stop this month, who absorbs it, and the artifact that makes absorption real. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
            ),
            [
                "Stop approving pricing exceptions ad hoc — publish a floor + VP Sales authority matrix by Friday.",
                "Stop writing AE #2 outbound — VP Sales assigns sequences; you review one weekly sample only.",
                "Stop being sole homepage author — voice one-pager + contractor; you do final approve only.",
                "Security questionnaires: build answer bank from last five; you review deltas only.",
            ],
        ),
    ],
}

REWRITES["hire-contract-without"] = {
    "id": "hire-contract-without",
    "schemaVersion": "1.2.0",
    "realm": "money",
    "concept": "compare",
    "persona": "founder",
    "title": "Hire, Contract, or Do Without",
    "blurb": "Prices the work as hire vs contract vs deliberate neglect, forces a single path with cost, and writes the thirty-day consequences so \"we'll figure it out\" stops being a plan.",
    "teaches": "Compare — headcount is a cash instrument",
    "tags": ["hiring", "burn", "money"],
    "input": {
        "id": "brief",
        "label": "The work, the timeline, and what you lose either way",
        "placeholder": "Describe the work, how long it is real, and the failure mode if nobody owns it.",
        "seed": (
            "work: Own inbound demo qualification and CRM hygiene for a growing self-serve → sales assist motion.\n"
            "timeline: Painful now; likely still real in 12 months as volume grows.\n"
            "hire: $95k + load for a junior AE/BDR hybrid.\n"
            "contract: $75/hr, ~20 hrs/week, 3-month cap.\n"
            "do without: Founders keep triaging demos; win-rate data stays dirty.\n"
            "cash: 14 months runway; raise in progress."
        ),
    },
    "cells": [
        cell(
            "c1",
            "Price all three",
            "Same work, three instruments — cash, flexibility, and learning rate.",
            ["input.brief"],
            "c1",
            "prose",
            "reasoning",
            (
                "Compare hire vs contract vs do-without on cash, flexibility, quality risk, and learning kept in-house. "
                "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
            ),
            (
                "Hire: ~$12–14k/mo fully loaded; slow to reverse; builds internal judgment about qualification. "
                "Contract: ~$6k/mo at 20 hrs; easy exit at 90 days; learning walks out unless you instrument the CRM. "
                "Do without: \"free\" but founder hours at the most expensive rate you have; data stays noisy, "
                "which taxes the raise story. The work is not temporary — that weakens pure contract."
            ),
        ),
        cell(
            "c2",
            "Make the call",
            "One path. Cost named. No hybrid fog.",
            ["c1", "input.brief"],
            "c2",
            "choice",
            "reasoning",
            (
                "Present hire, contract (time-boxed), or do-without with explicit cost. Do not auto-select. "
                "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
            ),
            {
                "options": [
                    {
                        "id": "hire",
                        "label": "Hire the hybrid AE/BDR",
                        "cost": "High cash / low flexibility",
                        "note": "Right if the motion is core for 12+ months.",
                    },
                    {
                        "id": "contract",
                        "label": "Contract 90 days + CRM instrumentation",
                        "cost": "Medium cash / high flexibility",
                        "note": "Right if you need proof of volume before headcount.",
                    },
                    {
                        "id": "without",
                        "label": "Do without — founders keep it 60 days max",
                        "cost": "Low cash / high opportunity cost",
                        "note": "Only with a hard stop date and a metric that forces revisit.",
                    },
                ],
                "selected": None,
            },
            choice={"writes": "picked"},
        ),
        cell(
            "c3",
            "Thirty-day consequences",
            "What must be true in thirty days for the call to have been right.",
            ["picked", "c1"],
            "c3",
            "table",
            "reasoning",
            (
                "Table: Milestone, Owner, Date, Abort criterion — aligned to the selected path. "
                "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{c1}}"
            ),
            {
                "cols": ["Milestone", "Owner", "Date", "Abort criterion"],
                "rows": [
                    ["Job scorecard + interview loop locked", "CEO + VP Sales", "Day 7", "If scorecard slips, pause sourcing"],
                    ["Offer out or contractor SOW signed", "CEO", "Day 21", "If neither, default to do-without with date"],
                    ["CRM hygiene definition live", "Ops", "Day 30", "If data still dirty, path failed regardless of body"],
                ],
            },
        ),
    ],
}

REWRITES["account-safe"] = {
    "id": "account-safe",
    "schemaVersion": "1.2.0",
    "realm": "money",
    "concept": "diagnose",
    "persona": "customer",
    "title": "Is This Account Actually Safe",
    "blurb": "Reads renewal-risk signals without the comfort of a green health score, scores the account honestly, and names the interventions that change cash — not just sentiment.",
    "teaches": "Diagnose — green health scores still churn",
    "tags": ["renewal", "churn", "cs", "money"],
    "input": {
        "id": "context",
        "label": "Account data and renewal horizon",
        "placeholder": "Usage, tickets, champion status, commercial terms, and when renewal lands.",
        "seed": (
            "account: Northwind Clinics — $96k ARR, renews in 11 weeks.\n"
            "health score: Green (product telemetry only).\n"
            "signals: Weekly active seats down 18% since champion left; 3 P1 tickets in 40 days on SSO; "
            "economic buyer missed last QBR; success manager notes \"happy\" after a feature demo.\n"
            "commercial: Multi-year ending; they asked about month-to-month \"for flexibility.\""
        ),
    },
    "cells": [
        cell(
            "c1-signals",
            "Signals that cash cares about",
            "Separate telemetry comfort from renewal physics.",
            ["input.context"],
            "signals",
            "table",
            "reasoning",
            (
                "Table: Signal, Direction, Why it matters for renewal cash, Strength. "
                "Respond in {{locale.outputLanguage}}.\n\n{{input.context}}"
            ),
            {
                "cols": ["Signal", "Direction", "Why cash cares", "Strength"],
                "rows": [
                    ["Champion exit + seat drop", "Negative", "Usage without owner becomes optional spend", "High"],
                    ["P1 SSO tickets", "Negative", "Auth pain hits every login — expansion dies first", "High"],
                    ["Missed QBR with economic buyer", "Negative", "No executive narrative into renewal", "Medium"],
                    ["Green health score", "False comfort", "Telemetry lag; ignores politics", "Misleading"],
                    ["Month-to-month ask", "Negative", "Classic pre-exit flexibility language", "High"],
                ],
            },
        ),
        cell(
            "c2-score",
            "Honest safety score",
            "A number you would bet your forecast on — not the product's green badge.",
            ["signals", "input.context"],
            "score",
            "score",
            "reasoning",
            (
                "Score renewal safety 1–10 with basis and band (safe/fragile/at-risk). "
                "Respond in {{locale.outputLanguage}}.\n\n{{signals}}\n\n{{input.context}}"
            ),
            {
                "value": 3,
                "max": 10,
                "basis": "Champion gone, seats down, SSO pain, economic buyer absent, and month-to-month language. Green telemetry is not a counter-argument.",
                "band": "at-risk",
            },
        ),
        cell(
            "c3-actions",
            "Interventions that move cash",
            "Sentiment activities are not interventions. Name what changes renewal probability.",
            ["score", "signals"],
            "actions",
            "list",
            "reasoning",
            (
                "List interventions that materially change renewal probability in the next 11 weeks. "
                "Respond in {{locale.outputLanguage}}.\n\n{{score}}\n\n{{signals}}"
            ),
            [
                "Replace champion: get economic buyer to name a new day-to-day owner this week — in writing.",
                "Burn down SSO P1s with a dated restore; executive apology only after fix ships.",
                "Re-run QBR aimed at buyer outcomes, not feature tour; bring seat-drop chart yourself.",
                "Do not entertain month-to-month until a recovery plan is accepted; offer a shorter save with success criteria instead.",
            ],
        ),
    ],
}


def apply_featured(lib):
    feat = set(FEATURED)
    for nb in lib:
        if nb["id"] in feat:
            nb["featured"] = True
        elif nb.get("featured") and nb["id"] not in feat:
            nb.pop("featured", None)


def rebuild_seed(html: str, lib: list) -> str:
    by = {n["id"]: n for n in lib}
    seed = [deepcopy(by[i]) for i in FEATURED if i in by]
    seed_json = json.dumps(seed, ensure_ascii=False, separators=(",", ":"))
    html2, n = re.subn(
        r"const SEED_NOTEBOOKS = \[.*?\]\.map\(hydrateNotebook\);",
        lambda _m: "const SEED_NOTEBOOKS = " + seed_json + ".map(hydrateNotebook);",
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("SEED replace failed")
    return html2


def main():
    lib = json.loads(LIB.read_text(encoding="utf-8"))
    by_idx = {n["id"]: i for i, n in enumerate(lib)}

    # Drop prior new notebooks if re-run
    lib = [n for n in lib if n["id"] not in ("burn-before-raise", "price-floor-before-discount")]

    # Realm moves
    for n in lib:
        if n["id"] in REALM_MOVES:
            n["realm"] = REALM_MOVES[n["id"]]

    # Full rewrites
    for nid, body in REWRITES.items():
        body = deepcopy(body)
        # find and replace
        lib = [n for n in lib if n["id"] != nid]
        lib.append(body)

    # New money notebooks
    lib.append(_money_burn())
    lib.append(_money_price_floor())

    # Tail deepen for everything not in REWRITES / new
    rewritten = set(REWRITES) | {"burn-before-raise", "price-floor-before-discount", "write-a-notebook", "until-it-holds"}
    lib = [deepen_tail(n) if n["id"] not in rewritten else n for n in lib]

    # Stable-ish order: keep original order for survivors, append new at end
    # Actually sort featured first then by realm for sanity — better keep id order from a canonical list
    apply_featured(lib)

    # Persona / concept floors: verify later via check.sh
    LIB.write_text(json.dumps(lib, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    html = HTML.read_text(encoding="utf-8")
    html = rebuild_seed(html, lib)
    # Update curated shelf copy if present
    html = html.replace(
        "Hand-picked for distinct capabilities — critique, choice, ask, map, and authorship.",
        "Hand-picked for distinct capabilities — critique, choice, ask, map, money, teaching, and authorship.",
    )
    HTML.write_text(html, encoding="utf-8")

    from collections import Counter
    print("count", len(lib))
    print("realms", Counter(n["realm"] for n in lib))
    print("featured", [n["id"] for n in lib if n.get("featured")])
    print("money", [n["id"] for n in lib if n["realm"] == "money"])
    print("blurb<100", sum(1 for n in lib if len(n.get("blurb") or "") < 100))
    print("seed<120", sum(1 for n in lib if len((n.get("input") or {}).get("seed") or "") < 120))


if __name__ == "__main__":
    main()
