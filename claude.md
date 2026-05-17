# CLAUDE.md

# Project Overview

This project is an AI-based medication identification and accessibility system designed for visually impaired users.

The system combines:
- Braille label printing
- NFC-based medication identification
- AI-powered medication information analysis
- Voice accessibility support
- Public medical data integration

The primary goal is to improve medication accessibility and safety for visually impaired individuals.

---

# Core Principles

## Accessibility First

Accessibility is mandatory in every feature.

Prioritize:
- Voice guidance
- Large touch targets
- Minimal UI complexity
- Screen reader compatibility
- Simple workflows
- Fast interaction
- Reliable medication identification

Never sacrifice accessibility for visual design.

---

## Safety First

This project handles medication-related information.

Always prioritize:
- Reliability
- Information accuracy
- User safety
- Clear explanations

Never generate misleading medical claims.

Never hallucinate medication information.

Always verify medication-related information using trusted sources.

---

# Development Workflow

Always follow this workflow before implementation.

## Step 1 — Analysis

Before writing code:
- Analyze the problem
- Understand user requirements
- Identify risks
- Explain the intended solution

Do not directly generate production code before analysis.

---

## Step 2 — Architecture Design

Before implementation:
- Design the system structure
- Define API flow
- Define database structure
- Define file structure
- Define error handling strategy

Architecture must be explained before implementation.

---

## Step 3 — Incremental Implementation

Implement features incrementally.

Rules:
- Build one module at a time
- Test each module before continuing
- Avoid large untested implementations
- Keep changes isolated and reversible

Never attempt massive full-project rewrites.

---

# Explain Before Action

Before major actions:
- Explain the plan
- Explain which files will change
- Explain possible risks
- Explain expected outcomes

Do not modify core systems silently.

---

# File Safety Rules

Never:
- Delete important files automatically
- Overwrite critical logic without explanation
- Refactor entire systems without approval

Before modifying important systems:
1. Explain the reason
2. Explain the impact
3. Wait for approval if the change is large

Always preserve project stability.

---

# API & Secret Protection

Security is mandatory.

Rules:
- Never hardcode API keys
- Never expose secrets
- Always use environment variables (.env)
- Never print secrets in logs
- Never commit secrets to repositories

Sensitive keys include:
- OpenAI API keys
- Database credentials
- Authentication tokens
- Server secrets

---

# AI Usage Rules

AI should:
- Simplify complex medical information
- Improve accessibility
- Summarize important information
- Support voice interaction

AI must NOT:
- Pretend to diagnose users
- Invent medical facts
- Replace professional medical advice

Always distinguish:
- Official medical data
- AI-generated summaries

---

# Medication Information Pipeline

Preferred architecture:

NFC Tag
→ App reads medication ID
→ Backend server request
→ Public medication API lookup
→ AI analysis and summarization
→ Voice output to user

NFC tags should contain only:
- medication ID
- lightweight identifier

Do not store large medical information directly inside NFC tags.

---

# Public Data Usage

Preferred data sources:
- Korean MFDS public APIs
- Official medication databases
- Verified government datasets

Always prioritize official data over unofficial sources.

---

# AI Analysis Rules

AI analysis should focus on:
- Important precautions
- Easy-to-understand explanations
- Risk prioritization
- Accessibility-focused summaries
- Medication appearance descriptions

Example:
"Central nervous system suppression may occur"

↓

"Drowsiness or dizziness may occur."

---

# Medication Appearance Description

The system may use AI image analysis to describe medication appearance.

Example outputs:
- "White round tablet"
- "Yellow capsule"
- "Oval tablet with center line"

The goal is to help visually impaired users distinguish medications more safely.

---

# Error Recovery Rules

When errors occur:
1. Explain the cause
2. Explain possible fixes
3. Retry safely
4. Avoid infinite retry loops

Never repeatedly perform destructive operations.

---

# Self-Improvement Loop

After completing tasks:
1. Evaluate implementation quality
2. Identify weaknesses
3. Suggest improvements
4. Wait for approval before major refactors

Do not autonomously redesign the entire project.

---

# Logging & Documentation

Maintain development logs for:
- Completed tasks
- Failed attempts
- Known issues
- Future improvements

Documentation must remain updated.

---

# Code Quality Rules

Code should be:
- Modular
- Readable
- Maintainable
- Reusable
- Well-commented

Avoid:
- Overengineering
- Unnecessary abstractions
- Huge files
- Duplicate logic

---

# UI/UX Rules

The UI must:
- Be usable without vision
- Support voice interaction
- Support screen readers
- Minimize user confusion
- Reduce interaction steps

Accessibility is more important than visual complexity.

---

# Approval Rules

Always ask before:
- Large refactors
- Database schema destruction
- Authentication rewrites
- Massive dependency changes
- File deletions
- Core architecture redesigns

Small isolated improvements may proceed safely.

---

# Project Philosophy

This project is not simply an AI chatbot.

It is an accessibility-focused medication identification and information system designed to improve medication safety and accessibility for visually impaired users using:
- NFC
- Braille
- Public medical data
- AI summarization
- Voice interaction

Every implementation decision should support this mission.