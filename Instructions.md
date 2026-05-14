I want to build a **cookiecutter-like command line tool** for scaffolding MVP projects that will be developed using **Claude Code**. The tool must be implemented in **Python**.

### Core Requirements

1. The CLI tool must **only run in an empty directory**.
  
   * If the directory is not empty, the tool should exit with an appropriate error message.

2. The CLI should collect the following inputs:

   **1. Path to PRD**

   * Path to a Product Requirements Document file that will guide development.

   **2. Frontend Framework**

   * Options:

     * React (only option for now, but design the CLI so additional frameworks can be added later)

   **3. Frontend Language**

   * Options:

     * JavaScript
     * TypeScript

   **4. Backend Framework**

   * Options:

     * Django
     * FastAPI
     * Node

   **5. Backend Language**

   * This option should **only be shown if the backend framework is Node**.
   * Options:

     * JavaScript
     * TypeScript

3. After collecting inputs, the tool should **generate a monorepo project structure** in the current directory containing:

```
/frontend
/backend
/claude
```

4. The generated repository should include a **Claude.md** file at the root that enables **agentic development with Claude Code**.

The `Claude.md` should include:

* Project overview
* Instructions for Claude agents
* Reference to the provided PRD
* Guidelines for working inside the monorepo

5. The tool should be implemented as a **Python CLI application** (e.g., using `argparse`, `typer`, or `click`).

### Additional Goals

* The project structure should be **extensible for future frameworks**.
* Ensure the scaffolding logic is **cleanly modularized** so new frontend/backend frameworks can be added easily.

### Expected Output

Running the CLI should produce a **ready-to-use monorepo skeleton** configured for Claude Code–driven development.
