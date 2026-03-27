# 🤖 AGENTS.md: Rules for AI Assistants

This document contains high-level instructions and guardrails for AI agents (like Antigravity, Copilot, or Cursor) working on the `ag_autoaccept` project.

## 🔴 CRITICAL: Testing Protocol
**Every code change made to the Python engine (`auto_accept.py`) or the Target detection logic MUST be verified.**
- Use `test.jpg` as the primary verification target.
- Run `cv2_match_diag.py` to confirm that your changes haven't broken template matching or coordinate calculation.
- Never commit a change without verifying that the `test_auto_accept.html` can correctly trigger the detection.

---

## 🏗️ Architecture & Style Guidelines
- **Visuals**: All generated documentation must follow the **Blue Neon** and **Sketchy/Excalidraw** aesthetic.
- **Tools**: Use the `/GenerateArchitecture` slash command to update project diagrams.
- **Mermaid Config**: Always use `look: handDrawn` and the `Architects Daughter` font for HTML diagrams to maintain the project's premium feel.

---

## 🧬 Implementation Guardrails
- **IPC Interface**: Always use JSON-formatted messages for communication between TypeScript and Python.
- **Win32 Messages**: Ensure all coordinates passed to `PostMessage` are explicitly cast to `int()`.
- **Expansion State**: Maintain the "Expand-only-once" logic per window handle to prevent UI loops.
- **Updating Documentation**: Make sure to Maintain the `ARCHITECTURE.md` and `ARCHITECTURE.html` files for any changes (if required).

---

## 🛠️ Available Workflows
- **`/GenerateArchitecture`**: Analyzes the current project and produces a `ARCHITECTURE.md` and a sketchy `ARCHITECTURE.html` dashboard.

---
**Note to AI**: You are an expert systems engineer. Be precise, verify your work with the provided test assets, and keep the user experience smooth and automated.
