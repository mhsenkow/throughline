#!/usr/bin/env python3
"""Editorial pass: make the library hold.

Fixes live-run prompt bugs, deepens thin authorship signals, consolidates
sparse realms, raises behavioral cell density, features a curated shelf,
and adds the dogfood authoring notebook.
"""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_PATH = ROOT / "library.json"
HTML_PATH = ROOT / "index.html"

GENERIC_PH = {
    "Paste the relevant details.",
    "Paste the details this notebook needs.",
}

REALM_MERGE = {
    "music": "craft",
    "fantasy": "craft",
    "photo": "craft",
    "making": "craft",
    "games": "craft",
    "garden": "life",
    "food": "life",
    "health": "life",
    "home": "life",
}

# Curated top shelf — each earns the slot by teaching a distinct capability.
FEATURED = [
    "until-it-holds",       # gate / recursion
    "interrogate-decision", # assumption archaeology
    "ambiguity-report",     # reading for divergence
    "five-audiences",       # range + self-diagnosis
    "hired-for",            # ask (human in the loop)
    "true-first",           # dependency gate
    "should-this-go-up",    # choice with cost
    "ten-headlines",        # map over strategies
    "write-a-notebook",     # dogfood authorship
]

PLACEHOLDERS = {
    "questions-cant-yes": ("Meeting notes and the decision you need", "Paste the meeting context and the yes/no decision that is stalling progress."),
    "objection-behind": ("Stated objection and account signals", "The objection in their words, plus renewal, usage, or champion signals."),
    "when-they-left": ("Churn story and activity clues", "What they said when they left, and what usage looked like in the last 60 days."),
    "ticket-to-repro": ("Raw ticket and product context", "Paste the ticket as written, plus the product surface it touches."),
    "reply-no-escalate": ("Draft reply and incident facts", "Your draft reply, and the facts you are willing to stand behind."),
    "account-safe": ("Account data and renewal horizon", "Health signals, open tickets, and when renewal lands."),
    "demo-the-problem": ("Discovery notes and stakeholder", "What you heard in discovery, and who will sit in the demo."),
    "next-person-needs": ("Handoff notes and next owner", "What you know now, and who picks this up next."),
    "what-else-explains": ("Observation and context", "The observation that surprised you, plus measurement context."),
    "define-before-chart": ("Metric name and business use", "The metric you want charted, and the decision it is meant to support."),
    "who-isnt-in-data": ("Dataset summary and population goal", "What the dataset covers, and who you think it represents."),
    "chart-implies": ("Chart description and notes", "Describe the chart as a reader would see it — axes, series, and annotation."),
    "did-it-win": ("A/B summary and decision policy", "Lift, intervals, guardrails, and the policy you use to ship or kill."),
    "number-under": ("Metric trend and candidate drivers", "The move in the number, and the drivers you already suspect."),
    "which-half-delete": ("Analysis doc and decision audience", "Paste the draft analysis and name who must decide from it."),
    "who-bears-risk": ("Contract text and deal context", "Paste the clauses that allocate risk, plus what the deal is for."),
    "compare-your-terms": ("Vendor quotes and buyer criteria", "Quotes side by side, and the criteria that actually matter to you."),
    "process-breaks": ("Process description and failure signals", "The process as written, and where it already fails in practice."),
    "someone-else": ("Task inventory and quality bar", "The work you want off your plate, and what 'done well' looks like."),
    "variance-telling": ("Variance report and operating context", "The variances, and the operating context a manager needs."),
    "policy-breaks": ("Policy text and edge cases", "Paste the policy, plus the edges where it already breaks."),
    "renew-or-leave": ("Contract state and alternatives", "Current terms, price, and the realistic alternatives."),
    "role-actually-needs": ("Job req and team state", "Paste the job description and what the team is failing at today."),
    "answer-told-you": ("Interview answer", "Paste the candidate's answer as close to verbatim as you can."),
    "feedback-usable": ("Feedback phrase and role context", "The vague feedback, and the role it was given in."),
    "first-thirty-days": ("Role and hiring context", "The role, the team gap, and what must be true by day 30."),
    "case-holds": ("Performance claim and evidence", "The claim you want to make stick, and the evidence you have."),
    "exit-interview-means": ("Exit comments", "Paste exit-interview notes. Names optional; patterns matter."),
    "policy-plain": ("Policy sentence", "Paste the sentence people keep misreading."),
    "what-must-be-true": ("Strategy bet and constraint", "The bet in one sentence, plus the hard constraint you already know."),
    "cant-copy": ("Advantage claim", "What you think competitors cannot copy, and why."),
    "hire-contract-without": ("Hire vs contract decision", "The work, the timeline, and what you lose either way."),
    "bad-number-first": ("Deck or narrative with a buried number", "Paste the section that hides the number you do not want to lead with."),
    "comparing-you-to": ("Competitor comparison", "Who buyers compare you to, and on which dimensions."),
    "three-youre-doing": ("Current founder workload", "List what you personally still own week to week."),
    "wrong-model": ("Topic and common wrong line", "The topic, and the sentence students keep arriving with."),
    "show-thinking": ("Worked problem", "Paste a problem and a student's worked solution."),
    "question-testing": ("Construct and exam question", "The thinking skill you want to test, and the question as written."),
    "field-disagrees": ("Claim and conflicting sources", "The claim, and where the field splits."),
    "method-cannot-see": ("Method and research goal", "The method you are using, and what you hope it can show."),
    "three-depths": ("Concept to teach at three depths", "The concept, and who the shallowest and deepest readers are."),
    "edit-hiding": ("Edit notes and intent", "What you cut or graded, and what the final image must still say."),
    "fight-boring": ("Encounter or level design", "The fight or level as designed, and why it currently feels flat."),
    "repair-replace": ("Broken thing and constraints", "What failed, age/cost, and how long you can live without it."),
    "appointment-questions": ("Appointment type and symptoms", "What the visit is for, and what you need answered before you leave."),
    "cook-from-there": ("Fridge inventory and constraints", "What is actually in the kitchen, plus time and cleanup limits."),
}

INTENT_FIX = {
    ("build-timeline", "scope"): "Name the window and the actors so reconstruction has edges.",
    ("build-timeline", "reconstruction"): "Rebuild the sequence from the evidence you have — gaps stay visible.",
    ("build-timeline", "next-checks"): "The next facts that would change the reconstruction if found.",
    ("what-else-touches", "touchpoints"): "Everything this change can reach, including the quiet dependents.",
    ("what-else-touches", "blast-radius"): "Where failure would show up first, and how loud it would be.",
    ("what-else-touches", "priority"): "Order the blast by cost of being wrong, not by how interesting it is.",
    ("comment-worth-making", "rubric"): "A keep/cut rubric for comments that do not waste the author's attention.",
    ("comment-worth-making", "decision"): "Choose keep, revise, or cut — preference alone is not a reason to speak.",
    ("comment-worth-making", "rewrite"): "If it stays, make it actionable. If it goes, say why in one line.",
    ("safe-order", "ordered-steps"): "Sequence the work so each step earns the right to do the next.",
    ("safe-order", "gates"): "The checks that must pass before the next step is allowed.",
    ("safe-order", "brief"): "A brief someone else could execute without calling you.",
    ("guess-last", "hypotheses"): "Candidate causes ranked by how cheaply they can be wrong.",
    ("guess-last", "ranked-tests"): "The smallest tests that would kill each hypothesis.",
    ("guess-last", "first-run"): "The one test to run first — and what result would stop you.",
    ("break-costs", "delta"): "What actually changes if you make the break.",
    ("break-costs", "cost-table"): "Cost of the break versus cost of living with the status quo.",
    ("break-costs", "recommendation"): "A recommendation that prices irreversibility honestly.",
    ("how-you-undo", "triggers"): "What would make you want the undo — name it before you ship.",
    ("how-you-undo", "rollback-plan"): "The rollback as a timeline, not a hope.",
    ("how-you-undo", "drill"): "The drill you would run so the rollback is not theoretical.",
    ("say-it-in-half", "half-diff"): "Cut the copy in half without losing the load-bearing claim.",
    ("say-it-in-half", "edge-constraints"): "What the shorter version can no longer promise.",
    ("say-it-in-half", "final-line"): "The line that survives when everything decorative is gone.",
    ("empty-says", "reading"): "What the empty state currently teaches — including what it teaches badly.",
    ("empty-says", "issues"): "Where emptiness becomes abandonment, blame, or fog.",
    ("empty-says", "rewrite"): "A rewrite that tells the user what to do next, not that they failed.",
    ("without-mouse", "audit-list"): "Every action that currently requires a pointer.",
    ("without-mouse", "findings"): "Which of those actions are blocked, awkward, or invisible from the keyboard.",
    ("without-mouse", "severity"): "Order the keyboard failures by how completely they strand someone.",
    ("component-yet", "criteria"): "The criteria that decide whether this should be a shared component.",
    ("component-yet", "decision"): "Choose extract, wait, or leave local — with the cost of each.",
    ("component-yet", "rationale"): "The one-paragraph rationale you would put in the PR.",
    ("sessions-support", "claims"): "What the research sessions actually support, versus what people will claim.",
    ("sessions-support", "gaps"): "The gaps between evidence and the decision people want to make.",
    ("sessions-support", "next-study"): "The smallest next study that would close the load-bearing gap.",
    ("system-broke", "drift-table"): "Where the design system and the product have drifted apart.",
    ("system-broke", "severity-rank"): "Which drifts cost the most consistency or trust.",
    ("system-broke", "repair-plan"): "A repair plan that starts with the drift that breaks users first.",
    ("who-loses", "collateral"): "Who pays if this claim is taken at face value.",
    ("who-loses", "impact"): "Impact by audience — including the ones not in the room.",
    ("who-loses", "rewrite"): "A rewrite that keeps the promise without hiding the cost.",
    ("can-you-say-that", "proof-needs"): "What would have to be true for this claim to be sayable.",
    ("can-you-say-that", "gaps"): "Where the proof is missing, thin, or someone else's.",
    ("can-you-say-that", "safe-claim"): "The strongest claim you can actually defend today.",
    ("wrong-room", "fit-rank"): "How well each message fits the room you are actually in.",
    ("wrong-room", "adapted-lines"): "Adapted lines that fit without becoming a different product.",
    ("wrong-room", "top-two"): "The two versions worth taking into the room.",
    ("objection-in-head", "objections"): "The objections already forming while they listen.",
    ("objection-in-head", "objection-map"): "Which objections are factual, emotional, or procedural.",
    ("objection-in-head", "pre-handle"): "The pre-handle you say before they have to say it.",
    ("sound-like-us", "voice-score"): "How far this copy sits from the voice you claim to have.",
    ("sound-like-us", "why-off"): "The specific tells that make it sound like everyone else.",
    ("sound-like-us", "voice-rewrite"): "A rewrite that sounds like you without becoming parody.",
    ("ten-headlines", "strategies"): "Three strategies worth writing headlines for — not ten random angles.",
    ("ten-headlines", "headline-map"): "Headlines per strategy, so you can judge the strategy not the line.",
    ("ten-headlines", "strategy-rank"): "Rank strategies by clarity, distinctiveness, and proof-readiness.",
    ("why-now", "drivers"): "The forces that make now different from six months ago.",
    ("why-now", "delay-cost"): "What delay actually costs — not what urgency theatre claims.",
    ("why-now", "urgency-case"): "The urgency case you can defend without inventing a crisis.",
}


def fix_template_vars(prompt: str, cell: dict) -> str:
    """Collapse alternate template dialects to bag keys the runtime understands."""
    def repl(m: re.Match) -> str:
        ref = m.group(1)
        if ref == "locale.outputLanguage" or ref.startswith("input."):
            return m.group(0)
        if ref.endswith(".picked"):
            writes = (cell.get("choice") or {}).get("writes")
            if writes:
                return "{{" + writes + "}}"
            return "{{" + ref.split(".", 1)[0] + "}}"
        if ".output" in ref:
            return "{{" + ref.split(".output", 1)[0] + "}}"
        return m.group(0)

    return re.sub(r"\{\{([\w.]+)\}\}", repl, prompt)


def ensure_inputs_in_prompt(prompt: str, inputs: list[str]) -> str:
    missing = []
    for ref in inputs:
        if ref.startswith("input."):
            if "{{" + ref + "}}" not in prompt:
                missing.append(ref)
        else:
            # bag key — accept {{name}} after dialect fix
            if "{{" + ref + "}}" not in prompt and not re.search(
                r"\{\{" + re.escape(ref) + r"\.", prompt
            ):
                missing.append(ref)
    if not missing:
        return prompt
    block = "\n\n" + "\n\n".join(f"{ref}:\n{{{{{ref}}}}}" for ref in missing)
    return prompt.rstrip() + block


def deepen_intents(nb: dict) -> None:
    for cell in nb["cells"]:
        key = (nb["id"], cell["id"])
        if key in INTENT_FIX:
            cell["intent"] = INTENT_FIX[key]
            continue
        intent = cell.get("intent") or ""
        title = cell.get("title") or ""
        if intent.startswith("Step producing") or intent == title or len(intent) < 24:
            # Prefer a readable sentence from the title when we have no hand fix.
            if title and not intent.startswith("Step"):
                cell["intent"] = title[0].upper() + title[1:] if title else intent
            elif title:
                cell["intent"] = f"Do the work of: {title[0].lower() + title[1:]}"


def fix_teaches(nb: dict) -> None:
    teaches = nb.get("teaches") or ""
    blurb = nb.get("blurb") or ""
    # Truncated teaches often equal a cut blurb.
    if len(teaches) < 40 or teaches.rstrip().endswith((" the", " a", " to", " and", " of", " w")):
        # Derive a short teaches from concept + title move.
        concept = nb.get("concept", "thinking")
        nb["teaches"] = f"{concept.capitalize()} — {nb['title']}"
    if teaches == blurb[: len(teaches)] and len(blurb) > len(teaches):
        nb["teaches"] = f"{nb.get('concept', 'thinking').capitalize()} — {nb['title']}"


def deepen_input(nb: dict) -> None:
    inp = nb.get("input") or {}
    nid = nb["id"]
    if nid in PLACEHOLDERS:
        label, ph = PLACEHOLDERS[nid]
        inp["label"] = label
        inp["placeholder"] = ph
    elif (inp.get("placeholder") or "") in GENERIC_PH:
        label = inp.get("label") or "Your material"
        if label == "Your situation":
            label = f"Material for: {nb['title']}"
            inp["label"] = label
        inp["placeholder"] = f"Paste what {label[0].lower() + label[1:]} looks like in your words."
    nb["input"] = inp


def fix_prompts(nb: dict) -> None:
    for cell in nb["cells"]:
        prompt = cell.get("prompt") or ""
        prompt = fix_template_vars(prompt, cell)
        prompt = ensure_inputs_in_prompt(prompt, cell.get("inputs") or [])
        # choice cells that write a pick should include the writes key downstream
        cell["prompt"] = prompt


# ── Behavioral upgrades ──────────────────────────────────────────────────

def upgrade_what_must_be_true(nb: dict) -> None:
    """Add a pursue/pause/kill choice — the point of scoring assumptions."""
    if any(c.get("output", {}).get("type") == "choice" for c in nb["cells"]):
        return
    nb["schemaVersion"] = "1.2.0"
    nb["blurb"] = (
        "Scores the assumptions a strategy bet needs, then forces a pursue / pause / kill "
        "choice before you write the plan."
    )
    nb["teaches"] = "Compare — score assumptions, then choose with cost"
    # rename thin c1/c2/c3 for readability where still generic
    cells = nb["cells"]
    if len(cells) >= 3 and cells[2]["id"] == "c3":
        # Insert choice before final plan; retarget plan to use picked
        choice = {
            "id": "call",
            "title": "Make the call",
            "intent": "A score without a decision is theatre. Pick pursue, pause, or kill with eyes open.",
            "inputs": ["c2", "c1"],
            "output": {"name": "call", "type": "choice"},
            "choice": {"writes": "picked"},
            "requires": "reasoning",
            "prompt": (
                "Based on the condition scorecard, present three options: pursue now, pause for a "
                "90-day test, or kill the bet. Each option needs an honest cost. Do not auto-select. "
                "Respond in {{locale.outputLanguage}}.\n\nconditions:\n{{c1}}\n\nscorecard:\n{{c2}}"
            ),
            "demo": {
                "options": [
                    {
                        "id": "pursue",
                        "label": "Pursue — fund the 90-day de-risk plan",
                        "cost": "High",
                        "note": "Only if the weakest conditions have a real owner this quarter.",
                    },
                    {
                        "id": "pause",
                        "label": "Pause — run one test before more spend",
                        "cost": "Medium",
                        "note": "Buys evidence; risks losing a calendar window.",
                    },
                    {
                        "id": "kill",
                        "label": "Kill — the bet needs conditions you cannot move",
                        "cost": "Low now / high later if you drift",
                        "note": "Use when controllability is low and kill criteria are already met.",
                    },
                ],
                "selected": None,
            },
        }
        plan = cells[2]
        plan["inputs"] = ["picked", "c2", "c1"]
        plan["intent"] = "Execution steps that match the call you just made — not a generic roadmap."
        plan["prompt"] = (
            "Write a short execution table aligned to the selected call. If pause, the rows are tests. "
            "If kill, the rows are wind-down and message. If pursue, the rows are the first 90 days. "
            "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\nscorecard:\n{{c2}}\n\nconditions:\n{{c1}}"
        )
        cells.insert(2, choice)


def upgrade_case_holds(nb: dict) -> None:
    """Gate: if the case does not hold, send them back to restate the claim."""
    if any(c.get("gate") for c in nb["cells"]):
        return
    nb["schemaVersion"] = "1.2.0"
    nb["blurb"] = (
        "Restates a performance claim in testable terms, pressure-tests the evidence, and gates "
        "whether the case holds — looping you back if it does not."
    )
    nb["teaches"] = "Critique — a case that fails sends you back"
    cells = nb["cells"]
    if len(cells) < 3:
        return
    # Replace final cell with gate that can jump to c1
    gate = {
        "id": "holds",
        "title": "Does the case hold?",
        "intent": "A verdict, not a vibe. If it fails, revise the claim — do not dress the evidence.",
        "inputs": ["c2", "c1"],
        "output": {"name": "holds", "type": "gate"},
        "gate": {"to": "c1", "writes": "revision", "maxPasses": 2},
        "requires": "reasoning",
        "prompt": (
            "Judge whether this performance case holds. Verdict must be pass or revise. "
            "If revise, say what the claim must become. Respond in {{locale.outputLanguage}}.\n\n"
            "claim:\n{{c1}}\n\nevidence:\n{{c2}}"
        ),
        "demo": {
            "verdict": "revise",
            "reason": "The claim asserts sustained underperformance but the evidence only covers one quarter and one rater.",
            "revision": "Narrow the claim to Q2 delivery outcomes under this manager, or gather a second rater and prior-quarter baseline before asserting a pattern.",
        },
    }
    # Keep a closing actions cell after gate for when it passes — insert gate before last, retitle last
    last = cells[-1]
    last["id"] = "close-gaps"
    last["title"] = "Close the gaps or stand down"
    last["intent"] = "If the gate passed, list the remaining evidence to gather. If it revised, show the new claim path."
    last["inputs"] = ["holds", "c2", "c1"]
    last["prompt"] = (
        "Given the gate result, list the concrete next evidence steps — or state that the case should not proceed. "
        "Respond in {{locale.outputLanguage}}.\n\ngate:\n{{holds}}\n\nevidence:\n{{c2}}\n\nclaim:\n{{c1}}"
    )
    cells.insert(-1, gate)


def upgrade_did_it_win(nb: dict) -> None:
    if any(c.get("output", {}).get("type") == "choice" for c in nb["cells"]):
        return
    nb["schemaVersion"] = "1.2.0"
    nb["blurb"] = (
        "Turns an A/B summary into decision criteria and a scored call, then forces ship / hold / kill."
    )
    nb["teaches"] = "Compare — experiment results become a choice with cost"
    cells = nb["cells"]
    if len(cells) < 3:
        return
    # Actual bag keys in this notebook
    criteria = cells[0]["output"]["name"]
    score = cells[1]["output"]["name"]
    choice = {
        "id": "verdict-choice",
        "title": "Ship, hold, or kill",
        "intent": "The score is not the decision. Pick the path and price it.",
        "inputs": [score, criteria],
        "output": {"name": "verdictChoice", "type": "choice"},
        "choice": {"writes": "picked"},
        "requires": "reasoning",
        "prompt": (
            "Present ship, hold for more evidence, or kill. Each needs cost and the condition that would change your mind. "
            "Do not auto-select. Respond in {{locale.outputLanguage}}.\n\n"
            f"criteria:\n{{{{{criteria}}}}}\n\nscore:\n{{{{{score}}}}}"
        ),
        "demo": {
            "options": [
                {"id": "ship", "label": "Ship to the tested segment", "cost": "Medium", "note": "Lift clears policy; watch guardrail for 14 days."},
                {"id": "hold", "label": "Hold — extend the test", "cost": "Low", "note": "Interval still crosses the kill line."},
                {"id": "kill", "label": "Kill — does not clear policy", "cost": "Low now", "note": "Use when guardrails fail or lift is not decision-relevant."},
            ],
            "selected": None,
        },
    }
    last = cells[-1]
    last["inputs"] = ["picked", score, criteria]
    last["intent"] = "The message and next measurement that match the call."
    last["prompt"] = (
        "Write the decision note and next measurement plan for the selected call. "
        "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n"
        f"score:\n{{{{{score}}}}}\n\ncriteria:\n{{{{{criteria}}}}}"
    )
    cells.insert(-1, choice)


def upgrade_role_actually_needs(nb: dict) -> None:
    if any(c.get("ask") for c in nb["cells"]):
        return
    nb["schemaVersion"] = "1.2.0"
    nb["teaches"] = "Extract — then ask what success looks like before you hire"
    cells = nb["cells"]
    if len(cells) < 2:
        return
    ask = {
        "id": "success-ask",
        "title": "What does success look like in 90 days?",
        "intent": "The run pauses here. Without your answer, the interview plan is generic.",
        "inputs": ["c2"],
        "output": {"name": "success", "type": "prose"},
        "requires": "fast",
        "ask": {
            "label": "In 90 days, what must be true that is not true today?",
            "placeholder": "e.g. One launch ships without founder edits; sales uses a single narrative deck…",
        },
        "prompt": (
            "If unanswered, ask what must be true in 90 days. Respond in {{locale.outputLanguage}}.\n\n{{c2}}"
        ),
        "demo": "One launch ships without founder copy edits, and sales runs a single narrative deck in every enterprise first meeting.",
    }
    last = cells[-1]
    last["inputs"] = list(dict.fromkeys([*(last.get("inputs") or []), "success"]))
    last["prompt"] = ensure_inputs_in_prompt(last.get("prompt") or "", last["inputs"])
    cells.insert(-1, ask)


def upgrade_guess_last(nb: dict) -> None:
    if any(c.get("output", {}).get("type") == "choice" for c in nb["cells"]):
        return
    nb["schemaVersion"] = "1.2.0"
    nb["teaches"] = "Diagnose — pick the cheapest test before you dig"
    cells = nb["cells"]
    if len(cells) < 3:
        return
    hyps = cells[0]["output"]["name"]
    ranked = cells[1]["output"]["name"]
    choice = {
        "id": "pick-test",
        "title": "Which test runs first?",
        "intent": "Force a single first test so diagnosis does not become a brainstorm.",
        "inputs": [ranked, hyps],
        "output": {"name": "pick", "type": "choice"},
        "choice": {"writes": "picked"},
        "requires": "reasoning",
        "prompt": (
            "Offer three first-test options drawn from the ranked tests. Each needs cost in time and what a negative result kills. "
            "Do not auto-select. Respond in {{locale.outputLanguage}}.\n\n"
            f"{{{{{ranked}}}}}\n\n{{{{{hyps}}}}}"
        ),
        "demo": {
            "options": [
                {"id": "a", "label": "Reproduce on last known-good build", "cost": "30 min", "note": "Kills 'environment only' if it still fails."},
                {"id": "b", "label": "Diff recent dependency bumps", "cost": "20 min", "note": "Kills 'our code' if a dep explains the regression."},
                {"id": "c", "label": "Capture one failing trace end-to-end", "cost": "45 min", "note": "Expensive; only if A and B stay ambiguous."},
            ],
            "selected": None,
        },
    }
    last = cells[-1]
    last["inputs"] = ["picked", ranked, hyps]
    last["intent"] = "Write the first-run protocol for the test you picked."
    last["prompt"] = (
        "Write the first-run protocol for the selected test: steps, what success/failure looks like, and when to stop. "
        "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n"
        f"tests:\n{{{{{ranked}}}}}\n\nhypotheses:\n{{{{{hyps}}}}}"
    )
    cells.insert(-1, choice)


def upgrade_can_you_say_that(nb: dict) -> None:
    if any(c.get("gate") for c in nb["cells"]):
        return
    nb["schemaVersion"] = "1.2.0"
    nb["teaches"] = "Critique — unsafe claims get sent back"
    cells = nb["cells"]
    if len(cells) < 2:
        return
    # Find the safe-claim / diff cell — gate after gaps
    gaps = next((c for c in cells if "gap" in c["id"] or c["output"]["type"] == "list"), cells[1])
    gate = {
        "id": "sayable",
        "title": "Is it sayable yet?",
        "intent": "If the proof gaps are load-bearing, do not ship the claim — revise it.",
        "inputs": [gaps["output"]["name"]],
        "output": {"name": "sayable", "type": "gate"},
        "gate": {"to": cells[0]["id"], "writes": "revision", "maxPasses": 2},
        "requires": "reasoning",
        "prompt": (
            "Judge whether the original claim is sayable given these proof gaps. "
            "Verdict pass or revise. If revise, state the narrowed claim. "
            "Respond in {{locale.outputLanguage}}.\n\ngaps:\n{{" + gaps["output"]["name"] + "}}"
        ),
        "demo": {
            "verdict": "revise",
            "reason": "The claim asserts category leadership without a named comparison set or time window.",
            "revision": "Claim only what you can evidence for the last two quarters against named peers.",
        },
    }
    # Insert before last cell
    cells.insert(-1, gate)
    last = cells[-1]
    last["inputs"] = list(dict.fromkeys([*(last.get("inputs") or []), "sayable"]))
    last["prompt"] = ensure_inputs_in_prompt(
        fix_template_vars(last.get("prompt") or "", last), last["inputs"]
    )


def upgrade_cook_from_there(nb: dict) -> None:
    if any(c.get("output", {}).get("type") == "choice" for c in nb["cells"]):
        return
    nb["schemaVersion"] = "1.2.0"
    nb["teaches"] = "Generate — then choose one meal under real constraints"
    cells = nb["cells"]
    if len(cells) < 3:
        return
    meal_list = cells[1]["output"]["name"]
    choice = {
        "id": "pick-meal",
        "title": "Cook which one?",
        "intent": "Options without a pick become a second chore. Choose under tonight's constraints.",
        "inputs": [meal_list, "c1"],
        "output": {"name": "mealChoice", "type": "choice"},
        "choice": {"writes": "picked"},
        "requires": "reasoning",
        "prompt": (
            "Offer three meal options from the list with effort cost. Do not auto-select. "
            "Respond in {{locale.outputLanguage}}.\n\n{{" + meal_list + "}}\n\n{{c1}}"
        ),
        "demo": {
            "options": [
                {"id": "a", "label": "Chickpea lemon rice skillet", "cost": "20 min / one pan", "note": "Best leftover value."},
                {"id": "b", "label": "Spinach onion frittata", "cost": "25 min", "note": "Uses eggs down first."},
                {"id": "c", "label": "Egg fried rice with spinach", "cost": "15 min", "note": "Fastest; least elegant."},
            ],
            "selected": None,
        },
    }
    last = cells[-1]
    last["inputs"] = ["picked", meal_list]
    last["title"] = "Cook card"
    last["intent"] = "A single cook card for the meal you picked — steps, timing, cleanup."
    last["prompt"] = (
        "Write a short cook card for the selected meal: ingredients used, steps, timing, cleanup. "
        "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\noptions:\n{{" + meal_list + "}}"
    )
    last["output"] = {"name": "cookcard", "type": "markdown"}
    last["demo"] = (
        "### Chickpea lemon rice skillet\n"
        "1. Soften onion in one pan.\n"
        "2. Add chickpeas + spinach until wilted.\n"
        "3. Fold in rice; finish with lemon and yogurt on the side.\n"
        "**Time:** ~20 minutes. **Cleanup:** one pan, one bowl."
    )
    cells.insert(-1, choice)


UPGRADES = {
    "what-must-be-true": upgrade_what_must_be_true,
    "case-holds": upgrade_case_holds,
    "did-it-win": upgrade_did_it_win,
    "role-actually-needs": upgrade_role_actually_needs,
    "guess-last": upgrade_guess_last,
    "can-you-say-that": upgrade_can_you_say_that,
    "cook-from-there": upgrade_cook_from_there,
}


def make_write_a_notebook() -> dict:
    return {
        "id": "write-a-notebook",
        "schemaVersion": "1.2.0",
        "realm": "learning",
        "concept": "teach",
        "persona": "scholar",
        "featured": True,
        "title": "Write a Notebook",
        "blurb": (
            "Turns a capability you want someone to feel into a Throughline notebook — "
            "cell by cell — and emits paste-ready JSON. This is how the library grows."
        ),
        "teaches": "Teach — authorship as a runnable pipeline",
        "tags": ["authoring", "dogfood", "schema", "library"],
        "input": {
            "id": "capability",
            "label": "The capability to make legible",
            "placeholder": "One sentence: what should someone understand after running this?",
            "seed": (
                "A hiring manager should feel the difference between a polished job description "
                "and the operating needs the team actually has — then leave with interview questions "
                "aimed at those needs."
            ),
        },
        "cells": [
            {
                "id": "move",
                "title": "Name the move",
                "intent": "Every notebook teaches one kind of thinking. If you cannot name it, you do not have a notebook yet.",
                "inputs": ["input.capability"],
                "output": {"name": "move", "type": "table"},
                "requires": "reasoning",
                "prompt": (
                    "From this capability, propose: title, persona, realm, concept "
                    "(critique|extract|diagnose|generate|compare|plan|translate|teach), "
                    "one-line teaches, and the single input the user must bring. "
                    "Return a table with columns Field, Value. Respond in {{locale.outputLanguage}}.\n\n"
                    "{{input.capability}}"
                ),
                "demo": {
                    "cols": ["Field", "Value"],
                    "rows": [
                        ["title", "What This Role Actually Needs"],
                        ["persona", "people"],
                        ["realm", "business"],
                        ["concept", "extract"],
                        ["teaches", "Extract — strip job-ad language to operating needs"],
                        ["input", "Job req plus what the team is failing at today"],
                    ],
                },
            },
            {
                "id": "shape",
                "title": "Pick the shape",
                "intent": "Linear prose is the default. Gate, choice, map, and ask exist for when the capability is the control flow.",
                "inputs": ["move", "input.capability"],
                "output": {"name": "shape", "type": "choice"},
                "choice": {"writes": "pickedShape"},
                "requires": "reasoning",
                "prompt": (
                    "Choose the notebook shape that best teaches this capability. Options must include "
                    "cost. Do not auto-select. Respond in {{locale.outputLanguage}}.\n\n"
                    "{{move}}\n\n{{input.capability}}"
                ),
                "demo": {
                    "options": [
                        {
                            "id": "linear",
                            "label": "Linear — three cells, typed handoffs",
                            "cost": "Lowest",
                            "note": "Default. Use when reading top to bottom already teaches the move.",
                        },
                        {
                            "id": "choice",
                            "label": "Choice — force a pick with cost before the last cell",
                            "cost": "Medium",
                            "note": "When the capability is deciding, not summarizing.",
                        },
                        {
                            "id": "gate",
                            "label": "Gate — loop until the work holds",
                            "cost": "Higher",
                            "note": "When failure to revise is the failure mode.",
                        },
                        {
                            "id": "ask",
                            "label": "Ask — pause for a human fact the model must not invent",
                            "cost": "Medium",
                            "note": "When a later cell is garbage without one answer only the user has.",
                        },
                        {
                            "id": "map",
                            "label": "Map — run one prompt per item in a list",
                            "cost": "Medium",
                            "note": "When the capability is coverage across items, not one answer.",
                        },
                    ],
                    "selected": None,
                },
            },
            {
                "id": "cells",
                "title": "Draft the cells",
                "intent": "Each cell needs intent (why it exists), typed output, and a prompt that interpolates prior bag keys.",
                "inputs": ["pickedShape", "move", "input.capability"],
                "output": {"name": "cellDraft", "type": "markdown"},
                "requires": "reasoning",
                "prompt": (
                    "Draft 3–5 cells for this notebook. For each cell give: id, title, intent (one sentence), "
                    "output type (prose|list|table|markdown|score|diff|ranking|timeline|choice|gate), "
                    "inputs (bag keys), and a prompt that interpolates locale.outputLanguage and every input "
                    "bag key. Honor the selected shape ({{pickedShape}}): if choice/gate/ask/map, "
                    "include that control on the appropriate cell. Respond in {{locale.outputLanguage}}.\n\n"
                    "shape:\n{{pickedShape}}\n\nmove:\n{{move}}\n\ncapability:\n{{input.capability}}"
                ),
                "demo": (
                    "### c1 strip\n"
                    "- type: prose · inputs: input.brief\n"
                    "- intent: Rewrite the job req as blunt operating needs.\n"
                    "- prompt: includes the brief via template\n\n"
                    "### success-ask\n"
                    "- type: prose · ask · inputs: c1\n"
                    "- intent: Pause for what must be true in 90 days.\n\n"
                    "### c2 evidence\n"
                    "- type: table · inputs: c1, success\n\n"
                    "### c3 interview\n"
                    "- type: list · inputs: c2, success"
                ),
            },
            {
                "id": "quality",
                "title": "Quality gate",
                "intent": "If the draft would not teach anything as static text, send it back — runtime cannot rescue a thin notebook.",
                "inputs": ["cellDraft", "move", "pickedShape"],
                "output": {"name": "quality", "type": "gate"},
                "gate": {"to": "cells", "writes": "revision", "maxPasses": 2},
                "requires": "reasoning",
                "prompt": (
                    "Judge whether this notebook draft would be compelling as static text and correctly uses "
                    "the chosen shape. Verdict pass or revise. If revise, say what cell or input must change. "
                    "Respond in {{locale.outputLanguage}}.\n\n"
                    "draft:\n{{cellDraft}}\n\nmove:\n{{move}}\n\nshape:\n{{pickedShape}}"
                ),
                "demo": {
                    "verdict": "pass",
                    "reason": "The ask is load-bearing, intents explain why each cell exists, and the input is specific enough to run.",
                    "revision": "",
                },
            },
            {
                "id": "emit",
                "title": "Emit library JSON",
                "intent": "Paste-ready notebook object matching Throughline schema 1.2.0 — demos included.",
                "inputs": ["quality", "cellDraft", "move", "pickedShape", "input.capability"],
                "output": {"name": "notebookJson", "type": "markdown"},
                "requires": "reasoning",
                "prompt": (
                    "Emit a single Throughline notebook as a markdown fenced json block. Required fields: "
                    "id, schemaVersion (1.2.0), realm, concept, persona, title, blurb, teaches, tags, "
                    "input {{id,label,placeholder,seed}}, cells[{{id,title,intent,inputs,output,requires,prompt,demo}}]. "
                    "Include choice/gate/ask/map keys where the shape needs them. Demos must match output types. "
                    "Prompts must interpolate every declared input. Respond in {{locale.outputLanguage}}.\n\n"
                    "gate:\n{{quality}}\n\ndraft:\n{{cellDraft}}\n\nmove:\n{{move}}\n\nshape:\n{{pickedShape}}\n\n"
                    "capability:\n{{input.capability}}"
                ),
                "demo": (
                    "```json\n"
                    "{\n"
                    '  "id": "role-operating-needs",\n'
                    '  "schemaVersion": "1.2.0",\n'
                    '  "realm": "business",\n'
                    '  "concept": "extract",\n'
                    '  "persona": "people",\n'
                    '  "title": "What This Role Actually Needs",\n'
                    '  "blurb": "Strip job-ad language to operating needs, ask what 90-day success looks like, then draft interview prompts.",\n'
                    '  "teaches": "Extract — then ask before you hire",\n'
                    '  "tags": ["hiring", "people"],\n'
                    '  "input": {"id": "brief", "label": "Job req and team state", "placeholder": "Paste the JD and what is failing today.", "seed": "…"},\n'
                    '  "cells": []\n'
                    "}\n"
                    "```"
                ),
            },
        ],
    }


def apply_featured(lib: list[dict]) -> None:
    featured_set = set(FEATURED)
    for nb in lib:
        if nb["id"] in featured_set:
            nb["featured"] = True
        elif "featured" in nb:
            # Only the curated set should carry the badge.
            if nb["id"] != "until-it-holds":
                nb.pop("featured", None)


def merge_realms(lib: list[dict]) -> None:
    for nb in lib:
        if nb.get("realm") in REALM_MERGE:
            nb["realm"] = REALM_MERGE[nb["realm"]]


def update_html_realms(html: str) -> str:
    new_realms = """const REALMS = {
  business:   {name:'Business',      icon:'◆'},
  tech:       {name:'Technology',    icon:'▦'},
  design:     {name:'Design',        icon:'◐'},
  writing:    {name:'Writing',       icon:'✎'},
  craft:      {name:'Craft & Media', icon:'✦'},
  life:       {name:'Home & Body',   icon:'✚'},
  learning:   {name:'Learning',      icon:'◈'},
  money:      {name:'Money & Legal', icon:'§'},
  science:    {name:'Science',       icon:'∿'}
};"""
    html2, n = re.subn(
        r"const REALMS = \{.*?\n\};",
        new_realms,
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("failed to replace REALMS block")
    return html2


def update_featured_ui(html: str) -> str:
    """Replace single featured hero with a curated shelf of featured notebooks."""
    old = """    ${featured ? `<section class="feature">
      <div class="feature-body">
        <p class="eyebrow">Start here</p>
        <h2>${esc(featured.title)}</h2>
        <p>${esc(featured.blurb)}</p>
        <button class="btn" data-nb="${featured.id}">Open ${esc(featured.title)}</button>
      </div>
      <div class="feature-aside">
        <p class="eyebrow">What makes it different</p>
        <p>Most notebooks run top to bottom once. This one has a <b>gate</b>: a cell
        that judges the work and, if it does not hold, sends the run back to an
        earlier cell with a revision — up to three times, every pass visible.
        A loop is still a cell type, not a canvas.</p>
      </div>
    </section>` : ''}"""

    new = """    ${(() => {
      const shelf = NOTEBOOKS.filter(n => n.featured);
      if (!shelf.length) return '';
      const lead = shelf.find(n => n.id === 'until-it-holds') || shelf[0];
      const rest = shelf.filter(n => n.id !== lead.id);
      return `<section class="feature">
      <div class="feature-body">
        <p class="eyebrow">Start here</p>
        <h2>${esc(lead.title)}</h2>
        <p>${esc(lead.blurb)}</p>
        <button class="btn" data-nb="${lead.id}">Open ${esc(lead.title)}</button>
      </div>
      <div class="feature-aside">
        <p class="eyebrow">What makes it different</p>
        <p>Most notebooks run top to bottom once. This one has a <b>gate</b>: a cell
        that judges the work and, if it does not hold, sends the run back to an
        earlier cell with a revision — up to three times, every pass visible.
        A loop is still a cell type, not a canvas.</p>
      </div>
    </section>
    ${rest.length ? `<section class="collection">
      <div class="collection-head">
        <h2>Curated shelf</h2>
        <p>Hand-picked for distinct capabilities — critique, choice, ask, map, and authorship.</p>
      </div>
      <div class="shelf">${rest.map((n,i) => cardHTML(n, i)).join('')}</div>
    </section>` : ''}`;
    })()}"""

    if old not in html:
        raise SystemExit("featured UI block not found for replacement")
    html = html.replace(old, new, 1)

    # featured variable still used? change find to keep for nothing — remove unused
    html = html.replace(
        "  const featured = NOTEBOOKS.find(n=>n.featured);\n  const results = NOTEBOOKS.filter(matches).sort(SORTS[F.sort].fn);",
        "  const results = NOTEBOOKS.filter(matches).sort(SORTS[F.sort].fn);",
        1,
    )
    return html


def rebuild_seed(html: str, lib: list[dict]) -> str:
    by = {n["id"]: n for n in lib}
    # Seed: lead featured + one per persona coverage for offline first paint
    seed_ids = []
    for fid in FEATURED:
        if fid in by and fid not in seed_ids:
            seed_ids.append(fid)
    # Keep seed modest — featured set is enough if ≤10
    seed = [deepcopy(by[i]) for i in seed_ids if i in by]
    seed_json = json.dumps(seed, ensure_ascii=False, separators=(",", ":"))
    # re.sub treats backslashes in the replacement as escapes — use a callable.
    html2, n = re.subn(
        r"const SEED_NOTEBOOKS = \[.*?\]\.map\(hydrateNotebook\);",
        lambda _m: "const SEED_NOTEBOOKS = " + seed_json + ".map(hydrateNotebook);",
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("failed to replace SEED_NOTEBOOKS")
    return html2


def strengthen_check(html_check_path: Path) -> None:
    """Add prompt-interpolation check to check.sh library validation."""
    text = html_check_path.read_text(encoding="utf-8")
    needle = "        if cell.get('gate'):\n"
    insert = """        # Every declared input.* must appear in the prompt — otherwise live runs ignore the user.
        for ref in cell.get('inputs') or []:
            if ref.startswith('input.') and ('{{'+ref+'}}') not in (cell.get('prompt') or ''):
                issues.append(f"{nb['id']}/{cell.get('id')}: prompt never interpolates {{{{ {ref} }}}}")
            if ('.' in ref) and (not ref.startswith('input.')):
                issues.append(f"{nb['id']}/{cell.get('id')}: input ref {ref} looks like a nested path — use bag key only")

        # Ban alternate template dialects the runtime cannot resolve
        for var in re.findall(r'\\{\\{([\\w.]+)\\}\\}', cell.get('prompt') or ''):
            if var == 'locale.outputLanguage' or var.startswith('input.'):
                continue
            if '.output' in var or var.endswith('.picked'):
                issues.append(f"{nb['id']}/{cell.get('id')}: template {{{{ {var} }}}} is not a bag key")

        if cell.get('gate'):
"""
    if "prompt never interpolates" in text:
        return
    if needle not in text:
        raise SystemExit("check.sh gate block not found")
    html_check_path.write_text(text.replace(needle, insert, 1), encoding="utf-8")


def main() -> None:
    lib = json.loads(LIB_PATH.read_text(encoding="utf-8"))

    # Remove prior write-a-notebook if re-run
    lib = [n for n in lib if n.get("id") != "write-a-notebook"]

    # Drop one learning notebook? No — add dogfood and rebalance personas.
    # scholar currently 7; adding write-a-notebook keeps ≥6.
    # householder/maker realms move via merge.

    merge_realms(lib)

    for nb in lib:
        deepen_input(nb)
        deepen_intents(nb)
        fix_teaches(nb)
        fix_prompts(nb)
        if nb["id"] in UPGRADES:
            UPGRADES[nb["id"]](nb)
            # re-fix prompts after structural change
            fix_prompts(nb)

    lib.append(make_write_a_notebook())
    apply_featured(lib)

    # Persona balance: write-a-notebook is scholar. Ensure no realm empty.
    LIB_PATH.write_text(
        json.dumps(lib, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    html = HTML_PATH.read_text(encoding="utf-8")
    html = update_html_realms(html)
    html = update_featured_ui(html)
    html = rebuild_seed(html, lib)
    HTML_PATH.write_text(html, encoding="utf-8")

    strengthen_check(ROOT / "check.sh")

    # Summary
    from collections import Counter

    rc = Counter(n["realm"] for n in lib)
    feat = [n["id"] for n in lib if n.get("featured")]
    behavior = []
    for n in lib:
        kinds = []
        for c in n["cells"]:
            for k in ("gate", "choice", "map", "ask"):
                if c.get(k):
                    kinds.append(k)
        if kinds:
            behavior.append((n["id"], kinds))
    print(f"notebooks: {len(lib)}")
    print(f"realms: {dict(rc)}")
    print(f"featured: {feat}")
    print(f"behavioral: {len(behavior)}")
    for b in behavior:
        print(" ", b)


if __name__ == "__main__":
    main()
