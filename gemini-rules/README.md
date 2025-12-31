# Gemini Rules

This directory contains **Gemini Rules**, which are markdown files defining prompt-level instructions and context for the Gemini agent.

## Overview

Unlike **Workflows** (which are procedural scripts), **Rules** are persistent instructions that guide the agent's behavior, style, and decision-making process. They are analogous to "System Instructions" or "Custom Instructions".

## Relationship to Claude Skills (`cc-skills`)

While `cc-skills` (Claude Code Skills) define how the agent uses specific tools or handles topics, **Gemini Rules** serve a similar purpose but are implemented differently:

| Feature        | Claude Skills (`cc-skills`)          | Gemini Rules (`gemini-rules`)                            |
| :------------- | :----------------------------------- | :------------------------------------------------------- |
| **Mechanism**  | "Tool Use" knowledge / Documentation | System Prompt Context Injection                          |
| **Activation** | Agent reads skill file specifically  | Configurable: Always On, Model Decision, or Manual (`@`) |
| **File Type**  | Markdown                             | Markdown                                                 |

## Usage

1.  **Create a Rule**: Add a markdown file (e.g., `vmem.md`) to this directory.
2.  **Define Behavior**: Write clear instructions on how the agent should behave or what it should know.
3.  **Activate**:
    - **Manual**: Reference it in chat via `@vmem`.
    - **Auto**: If configured in `.agent/rules` (workspace level), it can be set to "Always On" or "Model Decision".

## Migration from `cc-skills`

To migrate a skill from `cc-skills` to a Gemini Rule:

1.  **Copy** the logic from the skill file (e.g., `cc-skills/skills/vmem/SKILL.md`).
2.  **Simplify**: Remove the specific tool-definition syntax if it's strictly for Claude.
3.  **Focus on Instruction**: Tell Gemini _when_ and _why_ to use the underlying tools (like the `vmem` CLI), rather than just defining the tool schema.
