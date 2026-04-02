# Architecture: policy-eval (OPA + workspace + proposed changes)

## What is what

| Piece | Role |
|-------|------|
| **`policy_eval` (Python package)** | Indexes workspace, applies proposed edits (unified diff), merges `input`, runs `opa eval`, enriches findings from **`<workspace>/.clawtfup/feedback/`**. Shipped **without** your rules; install only. |
| **Your project** | Under the workspace root: **`.clawtfup/policies/`** (manifest + Rego) and **`.clawtfup/feedback/`** (remediation YAML/JSON). You own every file. |

There is **one** layout: policies and feedback live under **`.clawtfup/`** for that workspace. No alternate “bundle path” or feedback next to the manifest.

## Purpose (LLM grounding)

Compare a **baseline** tree with **proposed edits** (internally a unified diff, e.g. from `git`).

- **Default CLI:** baseline = **committed files at `git HEAD`** (+ untracked on disk); proposed edits = **`git diff HEAD`** (with **`.clawtfup/`** excluded from that diff so config edits do not go through the patch applier). Report: `inputs.index_baseline: "git_head"`.
- **`--diff-file` / stdin:** baseline = **working tree** on disk. `inputs.index_baseline: "working_tree"`.

**`--diff-file`** = file of proposed edits; **`--patch`** is a deprecated alias.

## Layout (from workspace root)

| Path | Contents |
|------|----------|
| `.clawtfup/policies/` | `policy_eval.yaml` / `policy_eval.yml`, `rego/` (OPA `-d` target) |
| `.clawtfup/feedback/` | Any `*.yaml` / `*.yml` / `*.json` (sorted by name; later files override the same violation `code`) |

Workspace indexing **skips** `.git/` and `.clawtfup/` so policy config is not treated as product source.

**Sample policy themes** (see `rego/code_edits.rego`; all apply to **changed** hunks via `combined_after`): unsafe **eval** (allows `literal_eval`), **exec**, **os.system**, **shell=True**, **pickle** / **marshal**, **yaml.load**, **breakpoint**, **\_\_import\_\_** (warning), bare **`except:`**, **`== None` / `!= None`** (warnings), optional **anchor** on changed `.py` when enabled, plus **requirements** fragments. Pair each `code` with entries under `.clawtfup/feedback/`.

**Fixture for tests:** `tests/fixtures/sample_project/` mirrors this layout.

## OPA `input` document

Merge order into Rego `input`:

1. Workspace fragment (`workspace`, `change`, default `requirements`, `policy`).
2. `--input-json` (if root has `"input"`, merge inner object; else merge whole file).
3. Inline overlay (`EvaluateOptions.input_overlay`).

## Local contact surfaces

No HTTP server. Use **CLI** (`policy-eval evaluate`) or **`evaluate(EvaluateOptions(...))`** on the machine that has the workspace.

## CLI

```bash
policy-eval evaluate
```

- **Workspace** — cwd, or `--workspace <dir>`.
- **Policies** — always **`<workspace>/.clawtfup/policies/`** (no override flag).
- **Proposed changes** — **`git diff HEAD`** by default, or **`--diff-file`** / **`--diff-file -`**.

Example with explicit workspace + diff file:

```bash
python -m policy_eval evaluate \
  --workspace tests/fixtures/sample_project \
  --diff-file tests/fixtures/patches/app_eval.patch
```

Flags: `--input-json`, `--query`, `--max-files`, `--max-file-bytes`, `--exclude-glob`, `--no-gitignore`, `--pretty`.

**Exit codes:** by default (**strict**), exit **2** if `allow` is false or any finding has `severity` **error** (JSON is still printed on stdout). **`--no-strict`** forces exit **0** so scripts can parse `allow` / `findings` without a failing process. The hidden **`--strict`** flag is accepted as a no-op for older invocations.

## Python API

`EvaluateOptions.workspace` — project root.  
`EvaluateOptions.bundle_root` — **must** be the policies directory (normally `workspace / ".clawtfup" / "policies"`). Feedback is read only from `workspace / ".clawtfup" / "feedback"`.

## Tests

```bash
pip install -r requirements.txt
pytest
```

OPA on `PATH` or `tools/opa` for e2e.

## Workspace indexing

- **`max_files` / `max_file_bytes`** — defaults + **`0` = no cap** (CLI: `--max-files`, `--max-file-bytes`).
- **Skipped** — `.git/`, `.clawtfup/`.
- **Non-text** — NUL in first 8KiB or non–UTF-8 → skipped (see report).
- **Bad diff** — error + stderr JSON.

## OPA `-d` and `rego/`

Non-Rego files under `-d` become OPA **`data`**. Keep YAML manifests **out** of `rego/` unless you intend that. See [OPA `opa eval`](https://www.openpolicyagent.org/docs/latest/cli/#opa-eval).
