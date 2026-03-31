# AI Context — Read This First

This folder contains structured documentation designed to help AI assistants (ChatGPT, Claude, Copilot, etc.) quickly understand this project.

## Files — Read in This Order

| # | File | What you'll learn |
|---|------|-------------------|
| 1 | [OVERVIEW.md](OVERVIEW.md) | What the project is, who it's for, how it works, roadmap |
| 2 | [GOALS.md](GOALS.md) | Problem statement, motivation, research vision |
| 3 | [ARCHITECTURE.md](ARCHITECTURE.md) | Codebase structure, design patterns, implemented techniques |
| 4 | [CONVENTIONS.md](CONVENTIONS.md) | Naming conventions, how to add new techniques step-by-step |
| 5 | [DETECTION_ROADMAP.md](DETECTION_ROADMAP.md) | Blue team detection strategy, proposed structure, priorities |

## Key Points for AI Assistants

- This is an **educational/research** project, NOT a malware development tool
- The core concept is a **6-stage pipeline model** for decomposing shellcode loaders
- Both **red team** (technique implementation) and **blue team** (detection rules) perspectives matter equally
- When adding techniques, follow the existing patterns in `CONVENTIONS.md`
- The author's long-term vision is to create a **universal loader mapping framework** where any loader can be analyzed and mapped, with corresponding detection rules for each technique
