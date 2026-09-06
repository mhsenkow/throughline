#!/usr/bin/env python3
"""Second deep pass — learning/life shelf, short seeds, more behavioral cells."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "library.json"
HTML = ROOT / "index.html"

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
    "feedback-usable",
    "who-bears-risk",
    "wrong-model",
    "burn-before-raise",
]


def C(id, title, intent, inputs, name, typ, requires, prompt, demo, **extra):
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


REWRITES = {
    "wrong-model": {
        "id": "wrong-model",
        "schemaVersion": "1.2.0",
        "realm": "learning",
        "concept": "teach",
        "persona": "scholar",
        "featured": True,
        "title": "The Wrong Model They Arrive With",
        "blurb": "Names the misconception model a learner brings in, maps why it feels true, and gives diagnostic prompts that surface it in the first ten minutes — before you teach the right model into a conflict.",
        "teaches": "Teach — diagnose the model before you deliver the lecture",
        "tags": ["pedagogy", "misconception", "learning"],
        "input": {
            "id": "brief",
            "label": "Topic and the wrong line students keep arriving with",
            "placeholder": "Name the topic, the exact wrong sentence, and where you hear it (exam, office hours, forum).",
            "seed": (
                "topic: Natural selection\n"
                "commonLine: \"Animals evolve because they need to survive.\"\n"
                "whereHeard: Intro bio midterm short answers; also office hours after lecture 4.\n"
                "whatYouTaught: Variation, heritability, differential survival — in that order.\n"
                "frustration: Students can recite the steps and still write the need-sentence on the exam."
            ),
        },
        "cells": [
            C(
                "c1",
                "Name the incoming model",
                "Not the wrong fact — the coherent wrong theory underneath it.",
                ["input.brief"],
                "c1",
                "prose",
                "reasoning",
                (
                    "Describe the misconception model behind the student statement — its internal logic, "
                    "not just that it is wrong. Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                (
                    "This is an intention model of adaptation: organisms change because need directs change, "
                    "the way a person practices a skill. Variation is treated as a response to pressure, not "
                    "as raw material that precedes it. The model feels moral and agentive — which is why "
                    "reciting \"variation then selection\" does not displace it."
                ),
            ),
            C(
                "c2",
                "Misconception map",
                "Belief, why it feels true, and the hinge that breaks it.",
                ["c1", "input.brief"],
                "c2",
                "table",
                "reasoning",
                (
                    "Table: student belief, why intuitive, corrective hinge (the smallest idea that breaks it). "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
                ),
                {
                    "cols": ["Student belief", "Why intuitive", "Corrective hinge"],
                    "rows": [
                        [
                            "Need causes traits",
                            "Agency feels natural; effort→improvement in daily life",
                            "Variation exists before pressure; need cannot invent alleles",
                        ],
                        [
                            "Individuals evolve within a lifetime",
                            "Personal growth analogy",
                            "Populations change frequencies; individuals live or die",
                        ],
                        [
                            "The best traits always win",
                            "Simple progress story",
                            "Fitness is relative to environment — and environments move",
                        ],
                        [
                            "Reciting steps means understanding",
                            "School rewards sequence memory",
                            "Ask them to predict a result when need and variation conflict",
                        ],
                    ],
                },
            ),
            C(
                "c3",
                "Diagnostic prompts",
                "Questions that make the wrong model speak out loud in the first ten minutes.",
                ["c2", "c1"],
                "c3",
                "list",
                "reasoning",
                (
                    "List five diagnostic prompts that surface this misconception early — usable in lecture or office hours. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
                ),
                [
                    "Did the trait appear before the pressure, or because of it — and how would you tell?",
                    "If an individual \"needs\" a trait and dies without offspring, what happened to the need?",
                    "Name a trait that is useful in one environment and harmful in another. Who \"decided\"?",
                    "A population has no useful variation for a new toxin. Does need create it? What happens instead?",
                    "Rewrite \"animals evolve because they need to survive\" without using need, want, or try.",
                ],
            ),
            C(
                "c4",
                "Which prompt first?",
                "Pick the opener for tomorrow's class — cost is minutes, payoff is who speaks.",
                ["c3", "c2"],
                "c4",
                "choice",
                "reasoning",
                (
                    "Offer three first prompts with time cost and what wrong answer you expect. Do not auto-select. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c3}}\n\n{{c2}}"
                ),
                {
                    "options": [
                        {
                            "id": "before",
                            "label": "Did the trait appear before the pressure?",
                            "cost": "3 min",
                            "note": "Fastest hinge into variation-first.",
                        },
                        {
                            "id": "toxin",
                            "label": "No useful variation for a new toxin — then what?",
                            "cost": "6 min",
                            "note": "Forces extinction vs magic adaptation.",
                        },
                        {
                            "id": "rewrite",
                            "label": "Rewrite the need-sentence without need/want/try",
                            "cost": "8 min writing",
                            "note": "Best for exams; slower in live class.",
                        },
                    ],
                    "selected": None,
                },
                choice={"writes": "picked"},
            ),
            C(
                "c5",
                "Tomorrow's open",
                "The exact words you say after taking attendance.",
                ["picked", "c3", "c1"],
                "c5",
                "prose",
                "reasoning",
                (
                    "Write the opening two minutes of class using the selected prompt, aimed at surfacing the wrong model. "
                    "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{c3}}\n\n{{c1}}"
                ),
                (
                    "Before we review last week: write one sentence — did camouflage in moths appear because soot "
                    "arrived, or was it already in the population? Do not use the words need, want, or try. "
                    "I am not grading correctness yet — I am listening for the model you brought in the door."
                ),
            ),
        ],
    },
    "question-testing": {
        "id": "question-testing",
        "schemaVersion": "1.2.0",
        "realm": "learning",
        "concept": "teach",
        "persona": "scholar",
        "title": "Does This Question Test That",
        "blurb": "Pressure-tests an exam question against the thinking skill you claim to measure, shows what it actually rewards, and rewrites it until a student cannot pass by pattern-matching.",
        "teaches": "Critique — most exam questions test memory wearing a reasoning costume",
        "tags": ["assessment", "exams", "learning"],
        "input": {
            "id": "brief",
            "label": "Target construct and the exam question",
            "placeholder": "Name the thinking skill, paste the question, and note the course level.",
            "seed": (
                "targetConstruct: Causal reasoning — can the student distinguish correlation claims from causal claims "
                "and name a confound.\n"
                "examQuestion: \"Define independent variable.\"\n"
                "course: Intro research methods, week 3.\n"
                "whyYouWroteIt: Fast to grade; shows they did the reading."
            ),
        },
        "cells": [
            C(
                "c1",
                "What it actually tests",
                "Separate the claimed construct from the behavior that earns points.",
                ["input.brief"],
                "c1",
                "prose",
                "reasoning",
                (
                    "State what thinking this question actually rewards, versus the target construct. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                (
                    "It rewards definition recall. A student can define \"independent variable\" perfectly and "
                    "still confuse correlation with causation on every applied item. The target construct — "
                    "causal reasoning — is not touched."
                ),
            ),
            C(
                "c2",
                "Validity critique",
                "Where the question leaks, cues, or lets pattern-matching through.",
                ["c1", "input.brief"],
                "c2",
                "table",
                "reasoning",
                (
                    "Table: Issue, Why it undermines the construct, How a weak student still scores. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
                ),
                {
                    "cols": ["Issue", "Why it undermines", "How a weak student still scores"],
                    "rows": [
                        ["Definition-only", "No application to a claim", "Flashcard the glossary"],
                        ["No confound demand", "Causal reasoning never invoked", "Skip the hard part entirely"],
                        ["No wrong-but-plausible lure", "Cannot see misconception", "Lucky phrasing matches lecture"],
                    ],
                },
            ),
            C(
                "c3",
                "Rewrite candidates",
                "Three questions that actually require the construct.",
                ["c2", "input.brief"],
                "c3",
                "list",
                "reasoning",
                (
                    "Write three replacement questions that require the target construct, graded in under two minutes each. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{input.brief}}"
                ),
                [
                    "A study finds ice cream sales and drowning rise together. Give one causal claim someone might make, and one confound that breaks it.",
                    "Researchers randomize a study app to half a class and compare final grades. What is the independent variable, and what causal claim is now more defensible than in an observational version?",
                    "\"Students who sit in front get higher grades.\" Is this causal? If not, name a confound and one design change that would test the causal version.",
                ],
            ),
            C(
                "c4",
                "Pick the replacement",
                "Choose the one you will put on the exam — cost is grading time and cueing risk.",
                ["c3", "c2"],
                "c4",
                "choice",
                "reasoning",
                (
                    "Offer the three rewrites as options with grading cost. Do not auto-select. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c3}}\n\n{{c2}}"
                ),
                {
                    "options": [
                        {
                            "id": "icecream",
                            "label": "Ice cream / drowning confound item",
                            "cost": "Fast grade",
                            "note": "Classic; some students have seen it.",
                        },
                        {
                            "id": "app",
                            "label": "Randomized study-app item",
                            "cost": "Medium",
                            "note": "Ties IV definition to causal warrant.",
                        },
                        {
                            "id": "seats",
                            "label": "Front-row grades item",
                            "cost": "Fast grade",
                            "note": "Closest to student life; high diagnostic value.",
                        },
                    ],
                    "selected": None,
                },
                choice={"writes": "picked"},
            ),
            C(
                "c5",
                "Scoring key",
                "What earns full credit — so you do not reintroduce memory theatre at grading time.",
                ["picked", "c3", "c1"],
                "c5",
                "markdown",
                "reasoning",
                (
                    "Write a short scoring key for the selected question: full credit, half, zero. "
                    "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{c3}}\n\n{{c1}}"
                ),
                (
                    "### Full\nNames a non-causal reading, a concrete confound, and a design change that "
                    "addresses it.\n### Half\nNames confound without design change, or design without confound.\n"
                    "### Zero\nRestates the correlation as causal, or defines terms without application."
                ),
            ),
        ],
    },
    "field-disagrees": {
        "id": "field-disagrees",
        "schemaVersion": "1.2.0",
        "realm": "learning",
        "concept": "extract",
        "persona": "scholar",
        "title": "Where the Field Disagrees",
        "blurb": "Reads an intro treatment against the live disputes in a field, inventories what the chapter smooths over, and builds a reading list that makes the disagreement legible instead of pretending consensus.",
        "teaches": "Extract — textbooks hide the argument that makes a field alive",
        "tags": ["scholarship", "reading", "learning"],
        "input": {
            "id": "brief",
            "label": "Topic, starting read, and what you suspect is smoothed",
            "placeholder": "Name the topic, the intro chapter/article, and the disagreement you think is being papered over.",
            "seed": (
                "topic: Theories of consciousness\n"
                "startingRead: Intro chapter presenting Global Workspace Theory and IIT as two \"leading accounts,\" "
                "each with a tidy paragraph, ending on \"research continues.\"\n"
                "suspicion: The chapter never says what would falsify either, or why some researchers call IIT unfalsifiable.\n"
                "reader: Advanced undergrad starting a seminar paper."
            ),
        },
        "cells": [
            C(
                "c1",
                "The smoothed story",
                "What the intro wants you to believe is settled.",
                ["input.brief"],
                "c1",
                "prose",
                "reasoning",
                (
                    "Summarize the consensus story the starting read sells — and what questions it quietly declines to ask. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                (
                    "The chapter sells a two-horse race: GWT vs IIT, both serious, both ongoing. It declines to ask "
                    "what evidence would retire either horse, how \"information integration\" is measured without "
                    "circularity, or why parts of the field treat the dispute as methodological rather than empirical."
                ),
            ),
            C(
                "c2",
                "Dispute inventory",
                "Live disagreements with stakes — not vibe disagreements.",
                ["c1", "input.brief"],
                "c2",
                "list",
                "reasoning",
                (
                    "List the live disputes a careful reader should know, with one line on why each matters. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
                ),
                [
                    "Falsifiability of IIT — is Φ a scientific quantity or a restatement of the phenomenon?",
                    "Whether GWT explains phenomenology or only reportability and access.",
                    "Whether NCC searches assume a theory of consciousness they claim to test.",
                    "How much \"leading account\" status is citation politics versus predictive success.",
                ],
            ),
            C(
                "c3",
                "Reading that exposes the fight",
                "A short stack that makes disagreement primary, not a footnote.",
                ["c2", "c1"],
                "c3",
                "table",
                "reasoning",
                (
                    "Table: Read, Side or role, What it exposes, How long. Prefer real citation-style titles when known. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
                ),
                {
                    "cols": ["Read", "Role", "What it exposes", "Length"],
                    "rows": [
                        [
                            "IIT primer + a sharp critique (e.g. unfalsifiability arguments)",
                            "Proponent vs skeptic",
                            "Whether the theory can fail",
                            "2–3 hrs",
                        ],
                        [
                            "GWT overview + phenomenology critique",
                            "Access vs experience",
                            "What \"workspace\" leaves out",
                            "2 hrs",
                        ],
                        [
                            "Methods paper on NCC identification problems",
                            "Meta",
                            "Theory smuggled into measurement",
                            "1–2 hrs",
                        ],
                    ],
                },
            ),
        ],
    },
    "method-cannot-see": {
        "id": "method-cannot-see",
        "schemaVersion": "1.2.0",
        "realm": "science",
        "concept": "diagnose",
        "persona": "scholar",
        "title": "What This Method Cannot See",
        "blurb": "Bounds a method against the question you want answered, tables the blind spots as if they were features, and upgrades the next design instead of overclaiming the current one.",
        "teaches": "Diagnose — methods fail silently when the question outruns them",
        "tags": ["methods", "research", "science"],
        "input": {
            "id": "brief",
            "label": "Method and the question you hope it can answer",
            "placeholder": "Name the method, the research question, and any constraints (time, access, ethics).",
            "seed": (
                "method: Cross-sectional survey of knowledge workers (n≈400), self-reported innovation behaviors.\n"
                "question: Does remote work improve team innovation?\n"
                "constraint: Six weeks, no experimental assignment, company will not share performance data.\n"
                "temptation: Report correlations as \"impact of remote work.\""
            ),
        },
        "cells": [
            C(
                "c1",
                "Bound the method",
                "What it can warrant — said tightly enough that overclaim becomes obvious.",
                ["input.brief"],
                "c1",
                "prose",
                "reasoning",
                (
                    "State what causal or descriptive claims this method can actually support for this question. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                (
                    "At best: associations between reported remoteness and reported innovation behaviors in this "
                    "sample, at one time, with all the usual self-report bias. It cannot warrant \"remote work "
                    "improves team innovation\" — no temporal order, no assignment, no team-level outcome, no "
                    "handling of who gets to be remote."
                ),
            ),
            C(
                "c2",
                "Blind spot table",
                "Each blind spot as a failure mode, not a caveat footnote.",
                ["c1", "input.brief"],
                "c2",
                "table",
                "reasoning",
                (
                    "Table: Blind spot, What you might falsely conclude, How it shows up in the data. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
                ),
                {
                    "cols": ["Blind spot", "False conclusion", "How it shows up"],
                    "rows": [
                        [
                            "Selection into remote",
                            "Remote causes innovation",
                            "High performers already remote-enriched",
                        ],
                        [
                            "Self-report innovation",
                            "Culture of claiming ideas",
                            "Social desirability, not output",
                        ],
                        [
                            "Cross-section",
                            "Direction of effect",
                            "Innovative teams may win remote flexibility",
                        ],
                        [
                            "No team outcome",
                            "Individual creativity = team innovation",
                            "Missing coordination failures",
                        ],
                    ],
                },
            ),
            C(
                "c3",
                "Next-method upgrade",
                "The smallest design change that buys a real warrant — given the constraints.",
                ["c2", "c1", "input.brief"],
                "c3",
                "list",
                "reasoning",
                (
                    "List upgrades ordered by constraint-fit: what to add, what claim becomes defensible, what still is not. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}\n\n{{input.brief}}"
                ),
                [
                    "Add a prior-wave or archival date of remote start → weak temporal order; still not causal.",
                    "Replace self-report innovation with counted shipped experiments / patents / RFCs → better outcome, still observational.",
                    "Compare matched teams differing in remote policy with difference-in-differences if a policy change exists → closer to causal.",
                    "If no design upgrade is possible: rewrite the question to \"how do remote workers describe innovation practices\" and stop.",
                ],
            ),
            C(
                "c4",
                "Claim you will publish",
                "Force the honest title — the capability is refusing the tempting one.",
                ["c3", "c1"],
                "c4",
                "choice",
                "reasoning",
                (
                    "Offer three paper-title claims with integrity cost. Do not auto-select. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c3}}\n\n{{c1}}"
                ),
                {
                    "options": [
                        {
                            "id": "honest",
                            "label": "Associations between remoteness and reported innovation practices",
                            "cost": "Lower hype",
                            "note": "Matches the method.",
                        },
                        {
                            "id": "stretch",
                            "label": "Remote work and innovation: correlational evidence",
                            "cost": "Medium — still cueing causal curiosity",
                            "note": "Borderline; needs loud limitations.",
                        },
                        {
                            "id": "lie",
                            "label": "Remote work improves team innovation",
                            "cost": "High integrity cost",
                            "note": "Unsupported — include only as the trap option.",
                        },
                    ],
                    "selected": None,
                },
                choice={"writes": "picked"},
            ),
            C(
                "c5",
                "Limitations paragraph",
                "Write it now — before results tempt you to soften it.",
                ["picked", "c2", "c1"],
                "c5",
                "prose",
                "reasoning",
                (
                    "Write the limitations paragraph for the selected claim. Blunt. "
                    "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{c2}}\n\n{{c1}}"
                ),
                (
                    "This cross-sectional self-report survey cannot identify the effect of remote work on team "
                    "innovation. Remoteness is not randomly assigned; innovation is not observed in behavior; "
                    "and reverse causality remains plausible. Readers should treat associations as descriptive "
                    "of this sample's reports, not as a mandate for workplace policy."
                ),
            ),
        ],
    },
    "three-depths": {
        "id": "three-depths",
        "schemaVersion": "1.2.0",
        "realm": "learning",
        "concept": "teach",
        "persona": "scholar",
        "title": "Explain It at Three Depths",
        "blurb": "Renders one idea for three audiences via a map, then checks which depth you cannot write — that gap is where your own understanding is thin.",
        "teaches": "Translate — the depth you cannot write is the depth you do not have",
        "tags": ["explanation", "teaching", "learning"],
        "input": {
            "id": "brief",
            "label": "Idea and the three audiences",
            "placeholder": "Name the idea and three readers from shallow to deep.",
            "seed": (
                "idea: Bayes' theorem — updating a belief when new evidence arrives.\n"
                "audiences: middle-school student; undergrad who has seen fractions but not formal probability; "
                "domain researcher who uses p-values casually and distrusts \"Bayesian\" as branding.\n"
                "goal: Find which depth I am faking."
            ),
        },
        "cells": [
            C(
                "c1",
                "Depth ladder",
                "What each audience is allowed to not know — and what they must still leave with.",
                ["input.brief"],
                "depths",
                "list",
                "reasoning",
                (
                    "Define three depth targets: what each audience must leave understanding, and what jargon is forbidden. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                [
                    "Middle school: beliefs can get stronger or weaker when new facts arrive; no formulas.",
                    "Undergrad: prior × likelihood → posterior intuition with a simple numeric example; minimal notation.",
                    "Researcher: when Bayesian updating changes a decision versus when it is theatre; address p-value habits directly.",
                ],
            ),
            C(
                "c2",
                "Depth mapping",
                "One pass per audience — map forces coverage instead of one middle-altitude waffle.",
                ["depths", "input.brief"],
                "explanations",
                "list",
                "reasoning",
                (
                    "For {{audience}}, explain the idea at that depth. Keep it self-contained. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                [
                    "Middle school: You thought your friend usually texts back fast. Today they did not. "
                    "That new fact should change how sure you are they are free — not prove anything alone.",
                    "Undergrad: Start with a prior odds. Multiply by how many times more likely the evidence is "
                    "under one hypothesis than the other. The result is your new odds — a number you can show on paper.",
                    "Researcher: If your decision threshold would not move under any plausible likelihood ratio from this "
                    "study, the Bayesian language is costume. If it would move, write the prior you are actually using.",
                ],
                map={"over": "depths", "as": "audience"},
            ),
            C(
                "c3",
                "Where you are thin",
                "Which depth was hardest to write — that is the diagnosis.",
                ["explanations", "depths"],
                "c3",
                "prose",
                "reasoning",
                (
                    "Diagnose which depth is weakest in the mapped explanations and what study would thicken it. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{explanations}}\n\n{{depths}}"
                ),
                (
                    "The researcher depth is the thinnest if it stays slogan-level about p-values without a concrete "
                    "decision threshold. Study: take one paper you like, write the prior odds you actually had, and "
                    "compute whether the likelihood ratio should have moved your next experiment. If you cannot, "
                    "you do not yet own Bayes at that altitude."
                ),
            ),
        ],
    },
    "show-thinking": {
        "id": "show-thinking",
        "schemaVersion": "1.2.0",
        "realm": "learning",
        "concept": "teach",
        "persona": "scholar",
        "title": "Show the Thinking, Not the Answer",
        "blurb": "Takes a worked problem and a common error, rebuilds the reasoning steps a learner should see, and adds error-proof checks that catch the mistake before the final number.",
        "teaches": "Teach — answers hide the moves students need to steal",
        "tags": ["worked-examples", "tutoring", "learning"],
        "input": {
            "id": "brief",
            "label": "Problem, correct approach, and common error",
            "placeholder": "Paste the problem, what good thinking looks like, and the wrong move students make.",
            "seed": (
                "problem: A car travels 120 km in 2 hours, then 90 km in 3 hours. What is average speed for the whole trip?\n"
                "commonError: Average the two speeds (60 and 30) to get 45 km/h.\n"
                "correct: Total distance / total time = 210/5 = 42 km/h.\n"
                "whyItMatters: The error is a concept error about what \"average\" means for rates, not arithmetic."
            ),
        },
        "cells": [
            C(
                "c1",
                "The wrong move named",
                "Name the mistaken concept — not \"they forgot the formula.\"",
                ["input.brief"],
                "c1",
                "prose",
                "reasoning",
                (
                    "Name the conceptual error in the common wrong approach. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                (
                    "Students treat average speed as the average of speeds, as if each segment counted equally "
                    "regardless of time. They are averaging rates without weighting by time — a category error "
                    "about what the average is an average of."
                ),
            ),
            C(
                "c2",
                "Worked steps",
                "Visible moves a learner can steal — including the check that rejects 45.",
                ["c1", "input.brief"],
                "c2",
                "table",
                "reasoning",
                (
                    "Table: Step, What to write, Why this step exists (including a trap check). "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
                ),
                {
                    "cols": ["Step", "What to write", "Why this step exists"],
                    "rows": [
                        ["1", "Total distance = 120+90=210 km", "Forces the numerator of the real average"],
                        ["2", "Total time = 2+3=5 h", "Forces the denominator — time is the weight"],
                        ["3", "Average speed = 210/5=42 km/h", "Definition for the whole trip"],
                        ["4", "Trap check: (60+30)/2=45 ≠ 42", "Makes the wrong concept fail out loud"],
                    ],
                },
            ),
            C(
                "c3",
                "Error-proof checks",
                "Questions that catch the mistake before the box is filled.",
                ["c2", "c1"],
                "c3",
                "list",
                "reasoning",
                (
                    "List four checks a student should run so the common error cannot survive. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
                ),
                [
                    "Before averaging any rates: \"Am I weighting by time, or treating segments as equal votes?\"",
                    "Units check: does my answer have distance/time for the whole trip?",
                    "Sanity: if more time was spent slow, average should sit closer to the slow speed — 42 is closer to 30 than 45 is.",
                    "Explain without numbers: average speed is total distance over total time — say it before calculating.",
                ],
            ),
        ],
    },
    "appointment-questions": {
        "id": "appointment-questions",
        "schemaVersion": "1.2.0",
        "realm": "life",
        "concept": "plan",
        "persona": "householder",
        "title": "Questions Before the Appointment",
        "blurb": "Turns a vague worry and a short visit into a prioritized question list, a what-to-ask-if-there's-time tier, and a record template so you leave with answers instead of adrenaline.",
        "teaches": "Plan — scarce clinical time rewards prepared questions",
        "tags": ["health", "appointments", "life"],
        "input": {
            "id": "brief",
            "label": "Visit type, symptoms, and constraints",
            "placeholder": "What the visit is for, what you need answered, and how long you get.",
            "seed": (
                "visit: 15-minute primary care follow-up.\n"
                "symptoms: Fatigue for 6 weeks, headaches after lunch, sleep fragmented (wake 3–4am).\n"
                "alreadyTried: Iron-rich food, earlier bedtime, caffeine cut after 2pm — no clear change.\n"
                "fear: Being told \"it's stress\" without a plan.\n"
                "mustLearn: What to rule out, what to track for 2 weeks, when to escalate."
            ),
        },
        "cells": [
            C(
                "c1",
                "What must be answered",
                "If the visit ends and these are unanswered, it failed — regardless of bedside manner.",
                ["input.brief"],
                "c1",
                "prose",
                "reasoning",
                (
                    "State the must-answer questions for this visit, given the time constraint. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                (
                    "Must answer: (1) Which serious causes are we ruling out first, and how? "
                    "(2) What should I track for two weeks that would change the next step? "
                    "(3) What is the escalate-sooner trigger — symptom, severity, or timeline?"
                ),
            ),
            C(
                "c2",
                "Prioritized ask list",
                "Order for a 15-minute clock — first questions earn the right to later ones.",
                ["c1", "input.brief"],
                "c2",
                "list",
                "reasoning",
                (
                    "List prioritized questions for the appointment, marked must / if-time. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
                ),
                [
                    "MUST: Given fatigue + fragmented sleep + afternoon headaches, what are the top three causes you want to rule out in what order?",
                    "MUST: What should I log for 14 days that would change your next recommendation?",
                    "MUST: What change would make you want me back sooner than the routine follow-up?",
                    "IF TIME: Could medications, iron, thyroid, or apnea screening be relevant — and what is the cheapest first check?",
                    "IF TIME: If this is stress-mediated, what is the concrete plan — not just the label?",
                ],
            ),
            C(
                "c3",
                "Leave-with template",
                "Fill-in lines so answers become a record, not a memory.",
                ["c2", "c1"],
                "c3",
                "table",
                "reasoning",
                (
                    "Table: Prompt line to fill during the visit, Why it matters later. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c2}}\n\n{{c1}}"
                ),
                {
                    "cols": ["Fill in during visit", "Why it matters later"],
                    "rows": [
                        ["Ruled out first: ___ via ___", "Stops the loop of vague reassurance"],
                        ["Track for 14 days: ___", "Makes the next visit empirical"],
                        ["Come back sooner if: ___", "Turns worry into a threshold"],
                        ["Next appointment / test date: ___", "Prevents \"we'll see\" with no calendar"],
                    ],
                },
            ),
        ],
    },
    "repair-replace": {
        "id": "repair-replace",
        "schemaVersion": "1.2.0",
        "realm": "life",
        "concept": "compare",
        "persona": "householder",
        "title": "Repair or Replace",
        "blurb": "Frames the broken thing against remaining life, forces a repair / replace / live-with choice with cost, and leaves a next-action card that includes the failure mode if you guess wrong.",
        "teaches": "Compare — the cheap repair is expensive when it fails twice",
        "tags": ["home", "money", "life"],
        "input": {
            "id": "brief",
            "label": "Broken thing, quotes, and constraints",
            "placeholder": "What failed, age, repair vs replace quotes, and how long you can live without it.",
            "seed": (
                "appliance: 8-year-old dishwasher; intermittent leak at door seal, sometimes puddles by morning.\n"
                "quotes: Repair (seal+labor) $280; mid replacement $780 installed; open-box unit $620.\n"
                "history: Same seal repaired 18 months ago for $190.\n"
                "constraint: Kitchen is primary; can hand-wash for ~5 days max before it becomes a fight.\n"
                "uncertainty: Tech says \"probably seal\" but won't warrant against a hidden pump issue."
            ),
        },
        "cells": [
            C(
                "c1",
                "Decision frame",
                "Remaining life, second-failure cost, and downtime — before money feelings take over.",
                ["input.brief"],
                "c1",
                "prose",
                "reasoning",
                (
                    "Frame repair vs replace using age, prior repairs, downtime tolerance, and second-failure cost. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{input.brief}}"
                ),
                (
                    "At eight years with a repeat seal repair, you are paying again for a failure mode that already "
                    "returned. Repair is rational only if you accept a real chance of a second bill inside a year. "
                    "Replacement costs more now but resets the clock; hand-wash tolerance is five days, so either "
                    "path needs scheduling, not hope."
                ),
            ),
            C(
                "c2",
                "Select a path",
                "Repair, replace, or live-with — cost includes the second failure.",
                ["c1", "input.brief"],
                "c2",
                "choice",
                "reasoning",
                (
                    "Present repair, replace, or live-with-with-monitoring. Do not auto-select. "
                    "Respond in {{locale.outputLanguage}}.\n\n{{c1}}\n\n{{input.brief}}"
                ),
                {
                    "options": [
                        {
                            "id": "repair",
                            "label": "Repair seal now ($280)",
                            "cost": "Low cash / high repeat risk",
                            "note": "Only if you can absorb another failure within a year.",
                        },
                        {
                            "id": "replace",
                            "label": "Replace (open-box $620 or mid $780)",
                            "cost": "Higher cash / lower repeat risk",
                            "note": "Best when prior repair already failed once.",
                        },
                        {
                            "id": "live",
                            "label": "Live with it 30 days + catch pans",
                            "cost": "Low cash / high annoyance",
                            "note": "Only to buy time for a sale — set a hard end date.",
                        },
                    ],
                    "selected": None,
                },
                choice={"writes": "picked"},
            ),
            C(
                "c3",
                "Next actions",
                "Calendar the path — including what you do if the guess is wrong.",
                ["picked", "c1"],
                "c3",
                "list",
                "reasoning",
                (
                    "List next actions for the selected path, including the failure contingency. "
                    "Respond in {{locale.outputLanguage}}.\n\npicked:\n{{picked}}\n\n{{c1}}"
                ),
                [
                    "If replace: measure bay + water line today; order unit with delivery ≤5 days; keep old unit until first cycle succeeds.",
                    "If repair: get written \"if not seal, diagnosis fee applies\" in quote; book within 48 hours.",
                    "If live-with: put a hard calendar date 30 days out; catch pans + humidity check each morning.",
                    "Either paid path: photograph leak area before work for warranty disputes.",
                ],
            ),
        ],
    },
    "until-it-holds": None,  # seed enrich only below
}

# Seed-only enrichments for short-but-good notebooks
SEED_ENRICH = {
    "until-it-holds": (
        "Remote work makes engineering teams less productive.\n"
        "context: Said in a leadership offsite; people nodded; nobody defined productive.\n"
        "want: A claim that can survive attack — or die cleanly."
    ),
    "chord-intent": (
        "Key of A minor. Progression: Am – F – C – E7 – Am.\n"
        "note: The E7 feels dramatic but the F before it feels like it arrives late — "
        "like the tension was supposed to start earlier.\n"
        "ask: What harmonic job is each chord doing, and which one is confused?"
    ),
    "hypothesis-audit": (
        "Hypothesis: our onboarding redesign improves user engagement.\n"
        "Test: compare engagement metrics for 3 weeks pre/post for users who saw the new flow.\n"
        "Worry: We called it an A/B but the assignment was messy and \"engagement\" means three different dashboards."
    ),
    "case-holds": (
        "case: Employee missed 3 deadlines; peer complaints mention poor handoff quality.\n"
        "managerDraft: \"Performance is below expectations on delivery and collaboration.\"\n"
        "evidenceOnHand: Ticket timestamps, two Slack threads, one peer note. No prior written warning.\n"
        "risk: HR will ask whether the claim is specific enough to stand."
    ),
    "what-must-be-true": (
        "strategyBet: Expand upmarket into regulated healthcare buyers next year.\n"
        "constraint: Current product has limited audit logging; sales wants logos for the raise.\n"
        "unknown: Whether two design partners will accept a security roadmap instead of features today."
    ),
    "edit-hiding": (
        "cutList: Jump from arrival shot to reveal shot; reaction shot removed; 40 frames of hallway trimmed.\n"
        "goal: Build tension before reveal without the audience feeling time was stolen.\n"
        "worry: The cut may hide the character's doubt — which was the point of the scene."
    ),
    "fight-boring": (
        "scene: Boss fight lasts 6 minutes, high VFX, low player excitement.\n"
        "playerNotes: Feels repetitive after the second phase; dodging is safe; punish window unclear.\n"
        "designIntent: Was supposed to teach the parry timing introduced in the prior room."
    ),
    "cook-from-there": (
        "inventory: eggs, spinach, half onion, rice, chickpeas, yogurt, lemon.\n"
        "constraints: 30 minutes, one pan, no store run.\n"
        "people: Two adults; one wants high protein, one hates \"sad bowl\" energy."
    ),
}


def add_behavior_why_now(nb):
    if any(c.get("choice") for c in nb["cells"]):
        return nb
    cells = nb["cells"]
    if len(cells) < 3:
        return nb
    # insert choice before last
    choice = C(
        "urgency-call",
        "Act now, wait, or drop",
        "Urgency without a call is just anxiety with adjectives.",
        [cells[1]["output"]["name"], cells[0]["output"]["name"]],
        "urgencyCall",
        "choice",
        "reasoning",
        (
            "Present act-now, wait-for-a-trigger, or drop-the-urgency-claim. Do not auto-select. "
            f"Respond in {{{{locale.outputLanguage}}}}.\n\n{{{{{cells[1]['output']['name']}}}}}\n\n{{{{{cells[0]['output']['name']}}}}}"
        ),
        {
            "options": [
                {"id": "now", "label": "Act now — the delay cost is real", "cost": "Attention + spend", "note": "Use when a dated cost is evidenced."},
                {"id": "wait", "label": "Wait for a named trigger", "cost": "Calendar risk", "note": "Trigger must be observable."},
                {"id": "drop", "label": "Drop the urgency claim", "cost": "Ego", "note": "When \"why now\" was theatre."},
            ],
            "selected": None,
        },
        choice={"writes": "picked"},
    )
    last = cells[-1]
    last["inputs"] = list(dict.fromkeys(["picked", *(last.get("inputs") or [])]))
    if "{{picked}}" not in (last.get("prompt") or ""):
        last["prompt"] = last["prompt"].rstrip() + "\n\npicked:\n{{picked}}"
    cells.insert(-1, choice)
    nb["schemaVersion"] = "1.2.0"
    return nb


def add_behavior_ticket(nb):
    if any(c.get("ask") for c in nb["cells"]):
        return nb
    cells = nb["cells"]
    ask = C(
        "repro-ask",
        "What did you already try?",
        "Without this, the notebook invents a debugging history you do not have.",
        [cells[0]["output"]["name"]],
        "tried",
        "prose",
        "fast",
        (
            f"If unanswered, ask what repro steps and fixes were already tried. Respond in {{{{locale.outputLanguage}}}}.\n\n{{{{{cells[0]['output']['name']}}}}}"
        ),
        "Restarted the app, cleared cache, tried another browser — still fails on SSO redirect only for this account.",
        ask={
            "label": "What have you already tried, and what was the result?",
            "placeholder": "Steps, environments, and what did not change…",
        },
    )
    # insert after first cell
    for later in cells[1:]:
        later["inputs"] = list(dict.fromkeys([*(later.get("inputs") or []), "tried"]))
        if "{{tried}}" not in (later.get("prompt") or ""):
            later["prompt"] = later["prompt"].rstrip() + "\n\ntried:\n{{tried}}"
    cells.insert(1, ask)
    nb["schemaVersion"] = "1.2.0"
    return nb


def add_behavior_sound(nb):
    if any(c.get("choice") for c in nb["cells"]):
        return nb
    cells = nb["cells"]
    if len(cells) < 3:
        return nb
    choice = C(
        "voice-call",
        "Ship, revise, or kill the line",
        "Voice scores without a call leave you with aesthetics.",
        [cells[1]["output"]["name"], cells[0]["output"]["name"]],
        "voiceCall",
        "choice",
        "reasoning",
        (
            f"Present ship-as-is, revise toward voice, or kill the line. Do not auto-select. "
            f"Respond in {{{{locale.outputLanguage}}}}.\n\n{{{{{cells[1]['output']['name']}}}}}\n\n{{{{{cells[0]['output']['name']}}}}}"
        ),
        {
            "options": [
                {"id": "ship", "label": "Ship — close enough to voice", "cost": "Low", "note": "Only if score is honestly high."},
                {"id": "revise", "label": "Revise toward the voice rules", "cost": "Medium", "note": "Default when tells are fixable."},
                {"id": "kill", "label": "Kill — too generic to save", "cost": "Restart", "note": "When the line could be anyone's."},
            ],
            "selected": None,
        },
        choice={"writes": "picked"},
    )
    last = cells[-1]
    last["inputs"] = list(dict.fromkeys(["picked", *(last.get("inputs") or [])]))
    if "{{picked}}" not in (last.get("prompt") or ""):
        last["prompt"] = last["prompt"].rstrip() + "\n\npicked:\n{{picked}}"
    cells.insert(-1, choice)
    nb["schemaVersion"] = "1.2.0"
    return nb


def rebuild_seed(html, lib):
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
        raise SystemExit("seed replace failed")
    return html2


def main():
    lib = json.loads(LIB.read_text(encoding="utf-8"))

    # Full rewrites
    for nid, body in REWRITES.items():
        if body is None:
            continue
        lib = [n for n in lib if n["id"] != nid]
        lib.append(deepcopy(body))

    # Seed enrichments
    by = {n["id"]: n for n in lib}
    for nid, seed in SEED_ENRICH.items():
        if nid in by:
            by[nid].setdefault("input", {})["seed"] = seed

    # Behavioral upgrades
    if "why-now" in by:
        add_behavior_why_now(by["why-now"])
    if "ticket-to-repro" in by:
        add_behavior_ticket(by["ticket-to-repro"])
    if "sound-like-us" in by:
        add_behavior_sound(by["sound-like-us"])
    if "shot-list" in by:
        by["shot-list"]["concept"] = "generate"

    # Featured flags
    feat = set(FEATURED)
    for n in lib:
        if n["id"] in feat:
            n["featured"] = True
        elif n.get("featured") and n["id"] not in feat:
            n.pop("featured", None)

    LIB.write_text(json.dumps(lib, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html = HTML.read_text(encoding="utf-8")
    HTML.write_text(rebuild_seed(html, lib), encoding="utf-8")

    from collections import Counter
    print("count", len(lib))
    print("realms", Counter(n["realm"] for n in lib))
    print("behavioral", sum(1 for n in lib if any(c.get(k) for c in n["cells"] for k in ("gate", "choice", "map", "ask"))))
    print("seed<120", sum(1 for n in lib if len((n.get("input") or {}).get("seed") or "") < 120))
    print("blurb<100", sum(1 for n in lib if len(n.get("blurb") or "") < 100))
    print("featured", [n["id"] for n in lib if n.get("featured")])


if __name__ == "__main__":
    main()
