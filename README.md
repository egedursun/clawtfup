# policy-eval

**OPA-backed evaluation of proposed code changes** against Rego policies and workspace-local remediation text. Compare a baseline tree with a unified diff (for example `git diff HEAD`), run Open Policy Agent, and get a single JSON report suitable for CI, humans, or agent loops.

The Python package ships **without** your organization’s rules. You add **`.clawtfup/policies/`** (manifest + Rego) and **`.clawtfup/feedback/`** (YAML/JSON keyed by violation `code`) per repository or workspace.

---

## Requirements

| Component | Notes |
|-----------|--------|
| **Python** | 3.11+ |
| **OPA** | On `PATH`, or place a binary at **`tools/opa`** (see [OPA releases](https://github.com/open-policy-agent/opa/releases)) |
| **Git** | Optional for default `git diff HEAD` workflow |

---

## Installation

From the repository root (or install the published package the same way once released):

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Confirm the CLI:

```bash
policy-eval --help
# or: python -m policy_eval --help
```

---

## Quick start

From your **workspace root** (the project you want to check):

```bash
policy-eval evaluate --pretty
```

- **Baseline:** committed tree at **`git HEAD`** (plus untracked files on disk), and proposed edits from **`git diff HEAD`**. Paths under **`.clawtfup/`** are excluded from that diff so policy edits do not go through the patch applier.
- **Strict by default:** exit code **2** if `allow` is false or any finding has severity **error** (JSON is still printed on stdout).
- **`--no-strict`:** exit **0** so scripts can parse the report even when policy denies; use only when you explicitly want a non-failing process.

Evaluate a specific diff file against a fixture-style tree:

```bash
python -m policy_eval evaluate \
  --workspace tests/fixtures/sample_project \
  --diff-file tests/fixtures/patches/app_eval.patch \
  --pretty
```

Agent expectations for this repo are documented in **[`AGENTS.md`](AGENTS.md)**.

---

## How it works

1. **Index** the workspace (text files under the root; **`.git/`** and **`.clawtfup/`** are skipped so policy config is not treated as product source).
2. **Apply** the unified diff to produce **`files_after`** and **`changed_paths`**.
3. **Build** an OPA `input` document: workspace fragment (`combined_after` from changed hunks, full file contents for changed paths, optional `policy` / `requirements`).
4. **Merge** optional **`--input-json`** and programmatic overlays in the order documented below.
5. **Run** `opa eval` for each query listed in **`policy_eval.yaml`** (typically `data.code_edits.report`).
6. **Enrich** violations with entries from **`.clawtfup/feedback/`** when the violation `code` matches.

There is **no HTTP server**. Use the CLI or import **`evaluate(EvaluateOptions(...))`** in Python on the machine that has the workspace.

---

## Workspace layout

From the repository or application root:

| Path | Purpose |
|------|---------|
| **`.clawtfup/policies/`** | **`policy_eval.yaml`** (or `.yml`): `queries` and optional `findings_query`. Subfolder **`rego/`**: Rego modules passed to OPA (`-d`). |
| **`.clawtfup/feedback/`** | Any **`*.yaml`**, **`*.yml`**, **`*.json`**; merged by sorted filename (later files override the same violation **`code`**). OPA does **not** read these; they supply human/agent remediation text. |

Bundled reference policies and feedback for this repo live under **`.clawtfup/`** at the project root. **`tests/fixtures/sample_project/`** mirrors that layout for tests.

Policy rule categories (summary) are described in **[`.clawtfup/policies/README.md`](.clawtfup/policies/README.md)**.

---

## OPA input merge order

The document passed to Rego as **`input`** is built as follows (later wins on key conflicts):

1. Workspace fragment: **`workspace`** (root, `files_before`, `files_after`, `changed_paths`, `combined_after`), **`change`**, default **`requirements`**, default **`policy`**.
2. **`--input-json`**: if the file’s root has **`"input"`**, that object is merged; otherwise the whole file is merged.
3. Inline overlay from **`EvaluateOptions.input_overlay`** when using the Python API.

Use **`input.policy`** (for example `enforce_anchor_on_changed_python`) and **`input.requirements`** (`must_contain` / `must_not_contain`) when your Rego expects them.

---

## CLI reference

```text
policy-eval evaluate [--workspace DIR] [--diff-file PATH|-] [--input-json PATH]
  [--query Q] [--max-files N] [--max-file-bytes N] [--exclude-glob G] [--no-gitignore]
  [--pretty] [--no-strict]
```

| Flag | Meaning |
|------|---------|
| **`--workspace`** | Project root; default current directory. Policies: **`<workspace>/.clawtfup/policies/`** (no override). |
| **`--diff-file`** | Unified diff of proposed edits; **`-`** reads stdin. Default: run **`git diff HEAD`** in **`--workspace`**. |
| **`--patch`** | Deprecated alias for **`--diff-file`**. |
| **`--input-json`** | JSON merged into OPA input after the workspace fragment. |
| **`--query`** | Repeatable; overrides manifest queries. |
| **`--max-files` / `--max-file-bytes`** | Index limits; **`0`** means no cap (defaults apply otherwise). |
| **`--no-gitignore`** | Do not respect `.gitignore` when indexing. |
| **`--pretty`** | Pretty-print JSON on stdout. |
| **`--no-strict`** | Always exit **0** when the tool completes successfully. |
| **`--strict`** | Hidden no-op for older scripts. |

**Exit codes:** **0** — evaluation completed and (in strict mode) policy allowed with no error-level findings. **2** — strict failure (`allow` false or error findings), or CLI usage error as implemented. **Non-zero** may also indicate patch apply errors or OPA failures (see stderr / report).

---

## Python API

```python
from pathlib import Path
from policy_eval.evaluate import EvaluateOptions, evaluate

report = evaluate(
    EvaluateOptions(
        workspace=Path("/path/to/project"),
        bundle_root=Path("/path/to/project/.clawtfup/policies"),
        patch_text=Path("changes.patch").read_text(encoding="utf-8"),
        use_gitignore=True,
        change_source="diff_file",
    )
)
```

- **`bundle_root`** must be the **policies directory** (contains **`policy_eval.yaml`** and **`rego/`**).
- Feedback is always loaded from **`<workspace>/.clawtfup/feedback/`**.

---

## Indexing behavior

- Skipped paths: **`.git/`**, **`.clawtfup/`**.
- Files with NUL in the first 8 KiB or invalid UTF-8 are skipped; the report can include index warnings and skip counts.
- A malformed unified diff surfaces as an error with details suitable for tooling.

---

## Development

```bash
pip install -r requirements.txt   # editable install + pytest
pytest
```

End-to-end tests expect **OPA** on `PATH` or **`tools/opa`**.

---

## OPA data layout

Only **`rego/`** should contain **`*.rego`** files you intend as policy. Other files under the OPA `-d` directory become **`data`** in OPA. See the official **[OPA eval CLI](https://www.openpolicyagent.org/docs/latest/cli/#opa-eval)** documentation.

---

## License and versioning

Package metadata lives in **`pyproject.toml`** (`policy-eval`, version **0.1.0** at time of writing). Add a license file and PyPI classifiers when you publish.
