# Policy bundles: what is fixed vs what you own

## The evaluator is not a black box

The **`policy_eval` Python package** only:

1. Indexes the workspace (excluding `.git/` and `.clawtfup/`), applies **proposed edits** as a unified diff (default source: `git diff HEAD` in the CLI), merges `--input-json` into OPA’s `input`.
2. Runs `opa eval` for each query in **your** `policy_eval.yaml` (or `--query`).
3. Enriches `findings[]` from **your** feedback files: optional `feedback.yaml` in the bundle root, plus optional **`<workspace>/.clawtfup/feedback/*`**.

It does **not** ship secret rules inside the wheel. **All policy text lives in paths you control.**

## Default on disk (no CLI flags)

**Workspace** is **not** inferred from `.clawtfup`. It is **`--workspace`** or the **current working directory**. **`.clawtfup` must live under that workspace:** `<workspace>/.clawtfup/policies/`, `<workspace>/.clawtfup/feedback/`. Run from the repo root (or pass `--workspace` to it) so those paths resolve correctly.

From the project root:

- **Policies (bundle root):** `.clawtfup/policies/` — put `policy_eval.yaml` and `rego/` here (and optional `feedback.yaml`).
- **Extra feedback:** `.clawtfup/feedback/` — any number of `.yaml` / `.yml` / `.json` files (sorted by name; later files override the same violation `code`).

Then run **`policy-eval evaluate`** — workspace = cwd, policies = `.clawtfup/policies/`, proposed changes = **`git diff HEAD`**.

## What you can change without touching this repository

**Everything under your bundle directory** (or under `.clawtfup/policies/`), including:

- All `.rego` files.
- `policy_eval.yaml`.
- `feedback.yaml` in the bundle, and/or files under `.clawtfup/feedback/`.

Override the bundle path with `--policies` when not using the default.

## What is fixed by convention (under the bundle root)

| Name | Purpose |
|------|---------|
| `policy_eval.yaml` or `policy_eval.yml` | Query list + optional `findings_query`. Missing → you must pass `--query`. |
| `feedback.yaml` / `.yml` / `feedback.json` | Optional enrichment at bundle root. |
| `rego/` subdirectory | If present, `opa eval -d` uses **only** this folder. If absent, `-d` is the bundle root. |

## Reference copy in this repository

[`bundles/reference/`](bundles/reference/) is an **example** tree for tests and docs. **It is not imported by Python source code.** Copy it into `.clawtfup/policies/` to try the defaults.
