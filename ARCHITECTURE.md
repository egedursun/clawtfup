# Architecture: policy-eval (OPA + workspace + proposed changes)

## Two separate things

| Layer | What it is | Can you replace it without editing this repo? |
|-------|------------|-----------------------------------------------|
| **`policy_eval` (Python package)** | Indexes workspace, applies **proposed edits** (unified diff), merges `input`, runs `opa eval`, optional feedback enrichment. | You only **install** it (`pip install` / wheel). Policy text is **not** inside it. |
| **Policy bundle** | Directory with `policy_eval.yaml`, `rego/`, optional `feedback.*`. **Default:** `<workspace>/.clawtfup/policies/`. | **Yes.** Or pass `--policies` to any path. |

**Authoritative contract for bundles:** **[`BUNDLE.md`](BUNDLE.md)**.

## Purpose (LLM grounding)

Compare a **baseline** tree with **proposed edits** (still represented internally as a unified diff—what `git` and most tools emit).

- **Default CLI:** baseline = **committed files at `git HEAD`** (plus untracked files on disk); proposed edits = **`git diff HEAD`**. The report includes `inputs.index_baseline: "git_head"` so this is explicit.
- **Explicit `--diff-file` / stdin:** baseline = **current working tree** on disk (`inputs.index_baseline: "working_tree"`).

You do not need to type “patch” on the command line unless you want the long flag name; **`--diff-file`** is the name for “file containing proposed edits.” **`--patch`** remains as a deprecated alias.

## Default layout (zero extra flags)

From the project root:

| Path | Role |
|------|------|
| `.clawtfup/policies/` | Bundle: `policy_eval.yaml`, `rego/`, optional `feedback.yaml` |
| `.clawtfup/feedback/` | Optional extra remediation YAML/JSON (merged; overrides bundle on same violation `code`) |

Workspace index **skips** `.git/` and `.clawtfup/` so repos and policy config are not fed as product source text.

## Reference bundle (example only)

| Path | Role |
|------|------|
| [`bundles/reference/README.md`](bundles/reference/README.md) | Explains the sample. |
| [`bundles/reference/`](bundles/reference/) | Copy into `.clawtfup/policies/` to try locally. |

## OPA `input` document

The `-i` JSON file’s **root** is Rego `input`. Merge order:

1. Workspace fragment (`workspace`, `change`, default `requirements`, `policy`).
2. `--input-json` (if root has `"input"`, merge that object; else merge whole file).
3. Inline overlay (library API).

## Local contact surfaces (no network server)

Paths are read **only by a process you start on your own machine** (or by your orchestrator via subprocess / import). There is **no** bundled HTTP API.

1. **CLI** — `policy-eval evaluate` (defaults below). JSON report on stdout.
2. **Python** — `from policy_eval.evaluate import EvaluateOptions, evaluate`.

Integrations should **subprocess the CLI** or **call `evaluate()` in-process** on the host where the workspace already lives.

## CLI

**Minimal (from repo root, after `git init` + commit baseline):**

```bash
policy-eval evaluate
```

Resolves:

- **Workspace** — current directory (override: `--workspace`).
- **Policies** — `.clawtfup/policies/` (override: `--policies`).
- **Proposed changes** — unified diff from **`git diff HEAD`** (override: `--diff-file path` or `--diff-file -` for stdin).

**Explicit paths (e.g. tests):**

```bash
python -m policy_eval evaluate \
  --workspace tests/fixtures/ws \
  --policies bundles/reference \
  --diff-file tests/fixtures/patches/app_eval.patch
```

`--patch` is accepted as a deprecated alias for `--diff-file`.

Flags: `--input-json`, `--query` (repeat), `--max-files`, `--max-file-bytes`, `--exclude-glob`, `--no-gitignore`, `--strict`, `--pretty`.

## Library conventions (under `--policies` / `.clawtfup/policies`)

- `policy_eval.yaml` / `policy_eval.yml` — manifest.
- `feedback.yaml` / `.yml` / `.json` — optional; bundle-level enrichment.
- `rego/` — if present, used as `opa eval -d` directory.

Additional feedback: **`.clawtfup/feedback/*.yaml`** (and `.yml` / `.json`).

## Tests

```bash
pip install -r requirements.txt
pytest
```

OPA on `PATH` or `tools/opa` for e2e.

## Workspace indexing

- **`--max-files` / `max_files` (library)** — default `10000`; **`0` = no file-count cap**.
- **`--max-file-bytes` / `max_file_bytes`** — default `524288`; **`0` = no per-file size cap**.
- **Skipped paths** — `.git/` and `.clawtfup/` are never indexed as workspace source.
- **Non-text files** — NUL in first 8KiB or invalid UTF-8 → skipped (see report `inputs`).
- **Bad diff** — malformed unified diff → error; CLI prints `{"error":"…"}` on stderr.

## OPA `-d` and `rego/`

OPA loads non-Rego files under `-d` as **`data`**. Use a `rego/` subfolder when the bundle also has YAML manifests. See [OPA CLI docs](https://www.openpolicyagent.org/docs/latest/cli/#opa-eval).
