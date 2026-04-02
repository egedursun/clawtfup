**Policies only** (what OPA runs):

| Path | Role |
|------|------|
| `policy_eval.yaml` | Queries + optional `findings_query`. |
| `rego/*.rego` | Rego for `opa eval -d` (keep YAML out of `rego/`). |

**Feedback / remediation** does **not** live here — use **`.clawtfup/feedback/`** (see that folder’s README).

If you pass a custom `--policies` path elsewhere, you may still put an optional `feedback.yaml` next to that manifest; the default layout keeps feedback out of this directory.
