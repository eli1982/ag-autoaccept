---
description: GenerateArchitecture
---

Perform a comprehensive project architecture analysis and generate a standard documentation suite.

# 🧠 Core Reasoning:
- **Project Scan**: Analyze the folder structure, entry points (e.g., `src/index.ts`, `main.py`), and configuration files (`package.json`, `requirements.txt`).
- **Tech Identification**: Determine languages, frameworks, and IPC/API mechanisms used.
- **Component Mapping**: Identify major modules and their specific responsibilities (e.g., "Extension Driver", "CV Engine").

# 📄 ARCHITECTURE.md (Markdown Overview):
- **Structure**: Include "System Overview", "Main Components", "Technology Stack", and "Data Flow".
- **Visuals**: Embed a standard Mermaid diagram and an `ARCHITECTURE.png` image.
- **Footer**: Do NOT add any generation attribution or signatures.


# 🌐 ARCHITECTURE.html (Sketchy Dashboard):
- **Concept**: A "hand-drawn/Excalidraw" dashboard.
- **Visual Rules**:
    - **Background**: Deep Navy (#0a192f).
    - **Accents**: Cyan / Azure (#64ffda).
    - **Font**: Use 'Architects Daughter' (link via Google Fonts).
    - **Mermaid Config**: 
        - Must include `%%{init: {'theme': 'dark', 'look': 'handDrawn', 'fontFamily': 'Architects Daughter', 'themeVariables': { 'lineColor': '#64ffda', 'primaryColor': '#112240', 'nodeBorder': '#64ffda' }}}%%`
    - **CSS**: Implement rough borders (dashed or solid with shadows) and cards with a "paper" or "matte" texture.

# 🚀 Execution Flow:
1.  **Analyze**: Map the current project components.
2.  **Generate MD**: Build the structural `ARCHITECTURE.md`.
3.  **Create HTML**: Build the interactive sketchy dashboard using the provided visual rules.

