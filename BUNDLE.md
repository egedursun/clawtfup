# Policy bundles: what is fixed vs what you own

## The evaluator is not a black box

The **`policy_eval` Python package** only:

1. Indexes the workspace (excluding `.git/` and `.clawtfup/`), applies **proposed edits** as a unified diff (default source: `git diff HEAD` in the CLI), merges `--input-json` into OPA’s `input`.
2. Runs `opa eval` for each query in **your** `policy_eval.yaml` (or `--query`).
3. Enriches `findings[]` from **your** feedback files: under the default layout, **`<workspace>/.clawtfup/feedback/*`**; if you use a custom `--policies` path, an optional **`feedback.yaml`** next to the manifest is also loaded (then merged with `.clawtfup/feedback/`, which wins on duplicate codes).

It does **not** ship secret rules inside the wheel. **All policy text lives in paths you control.**

## Default on disk (no CLI flags)

**Workspace** is **not** inferred from `.clawtfup`. It is **`--workspace`** or the **current working directory**. **`.clawtfup` must live under that workspace:** `<workspace>/.clawtfup/policies/`, `<workspace>/.clawtfup/feedback/`. Run from the repo root (or pass `--workspace` to it) so those paths resolve correctly.

From the project root:

- **Policies:** `.clawtfup/policies/` — **`policy_eval.yaml` + `rego/` only** (OPA bundle root). No feedback files here by default.
- **Feedback:** `.clawtfup/feedback/` — remediation YAML/JSON (`*.yaml`, `*.yml`, `*.json`; sorted by name; later overrides same `code`).

Then run **`policy-eval evaluate`** — workspace = cwd, policies = `.clawtfup/policies/`, proposed changes = **`git diff HEAD`**.

## What you can change without touching this repository

**Everything under your bundle directory** (or under `.clawtfup/policies/`), including:

- All `.rego` files.
- `policy_eval.yaml`.
- Files under `.clawtfup/feedback/`, and/or (if you use another `--policies` path) `feedback.yaml` beside that manifest.

Override the bundle path with `--policies` when not using the default.

## What is fixed by convention (under the bundle root)

| Name | Purpose |
|------|---------|
| `policy_eval.yaml` or `policy_eval.yml` | Query list + optional `findings_query`. Missing → you must pass `--query`. |
| `feedback.yaml` / `.yml` / `feedback.json` | Optional enrichment at bundle root. |
| `rego/` subdirectory | If present, `opa eval -d` uses **only** this folder. If absent, `-d` is the bundle root. |

## Reference copy in this repository

[`bundles/reference/`](bundles/reference/) is an **example** tree for tests and docs. **It is not imported by Python source code.** Copy it into `.clawtfup/policies/` to try the defaults.
