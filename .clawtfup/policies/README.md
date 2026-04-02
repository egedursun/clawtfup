**Policies:** `policy_eval.yaml` + `rego/code_edits.rego`. Full project documentation: **[`README.md`](../../README.md)** (repository root).

Rules use **changed hunks** (`combined_after`) and, for many architecture/style checks, **per-file content** under `changed_paths` (`files_after[path]`).

**Categories (summary):** security (code execution, SQL/TLS/JWT, cookies/CORS/CSRF, templates, frontend XSS, secrets filenames), layering (routes vs persistence, domain purity, frontend vs DB), design (mutable defaults, imports, error handling), syntax/types (async/TS/Python lint suppressions), formatting (tabs, length, whitespace), and maintainability (TODO, print/input/sleep/assert in app code). Optional **anchor** line and **requirements** fragments when `input.policy` / `input.requirements` say so.

Remediation text: **`.clawtfup/feedback/feedback.yaml`** (one entry per `code` recommended).
