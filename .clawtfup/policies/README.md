# Reference policy bundle (example only)

This directory is **not** part of the Python evaluator. It is a **copy-paste template** you can use or replace.

- **You do not fork `policy_eval` to customize rules.** Point `--policies` (or `bundle_root` in the API) at **your own directory** on disk—CI artifact, other repo, `/etc/…`, anything.
- **Files here are fully editable** in your deployment: add/remove Rego, change `policy_eval.yaml`, replace `feedback.yaml`, or delete `feedback.yaml` entirely (findings still work; only LLM-oriented remediation strings disappear).

## Layout (convention)

| File / dir | Role |
|------------|------|
| `policy_eval.yaml` | Which OPA queries to run; optional `findings_query` for normalized `findings[]`. |
| `feedback.yaml` | Optional. Maps violation **`code`** (from Rego) → `title` / `remediation` / `references`. Loaded by **Python** after OPA; OPA does not read this file. |
| `rego/*.rego` | Passed to `opa eval -d` only. Keep YAML/JSON **out** of this folder if you do not want OPA to load them as `data`. |

## What is hardcoded in the **library** (not here)

Only **conventional names** the code looks for under **your** bundle root:

- Manifest: `policy_eval.yaml` or `policy_eval.yml`
- Feedback: `feedback.yaml`, `feedback.yml`, or `feedback.json`
- OPA `-d` target: `rego/` if it exists, else the bundle root

Everything else is **your** policy content.

See repository root [`BUNDLE.md`](../BUNDLE.md) for the same contract in one place.
