# Project Goals & Motivation

## Problem Statement

The malware/loader technique landscape is **chaotic**:
- Hundreds of techniques scattered across blog posts, GitHub repos, conference talks
- No standardized way to classify or compare them
- Students and junior researchers have no structured learning path
- Blue teamers lack a systematic mapping between techniques and detection methods

## Solution

A **unified 6-stage model** that decomposes any shellcode loader into discrete, composable stages. Think of it as **MITRE ATT&CK, but specifically for the internal mechanics of a loader**.

## Educational Purpose — NOT an Offensive Tool

This project exists to **teach and systematize knowledge**, not to create undetectable malware.

Key principles:
- Every technique is documented with clear explanations
- Code is readable and well-structured, not obfuscated
- The platform tests against security products to **understand detection**, not to evade it
- Blue team detection mapping is equally important as red team technique implementation

## Research Goals

### Red Team Perspective
- Build a comprehensive library of loader techniques, organized by stage
- Enable systematic experimentation: change one variable, observe the effect
- Understand which technique combinations trigger detection and why

### Blue Team Perspective
- For every technique, document:
  - What telemetry/artifacts it produces
  - Which log sources capture it (ETW, Sysmon, kernel callbacks)
  - How to write detection rules (Sigma, YARA)
- Build a detection knowledge base that maps 1:1 with techniques
- Enable defenders to understand attacker tradecraft at a granular level

### Academic Perspective
- Provide a formal model for describing and classifying loaders
- Enable reproducible experiments in controlled environments
- Support research papers with structured methodology

## Long-term Vision

Any loader in the wild can be **decomposed and mapped** to this model:

```
Real-world Loader → Analysis → L0.T? + L1.T? + L2.T? + L3.T? + L4.T? + L5.T?
                                  ↓       ↓       ↓       ↓       ↓       ↓
                              Detection Detection Detection Detection Detection Detection
                               Rule      Rule      Rule      Rule      Rule      Rule
```

This creates a **two-dimensional knowledge base**:
- Horizontal axis: Techniques (offensive)
- Vertical axis: Detections (defensive)
- Every cell: "Technique X is detected by Rule Y using Telemetry Z"
