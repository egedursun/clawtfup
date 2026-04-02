# Agent rules: policy evaluation is mandatory

You are working in a repo that uses **clawtfup** (OPA + `.clawtfup/`). Treat this as a **hard gate**, not optional hygiene.

## Required behavior

1. **Before** you treat a coding task as finished, a batch of edits as safe to ship, or a change as “ready for review”, run the evaluator **from the repository root** (or pass `--workspace` to that root):

   ```bash
   clawtfup evaluate --pretty
   ```

   If `clawtfup` is not on `PATH`, use the project venv and module form:

   ```bash
   python -m policy_eval evaluate --pretty
   ```

   The CLI is **strict by default**: exit code **2** if `allow` is false or there are error-severity findings (the JSON report is still printed on stdout). You do **not** pass a flag to “turn strict on”—that is already the behavior.

2. **You do not skip this** because the diff is “small”, “only docs”, or “obviously fine”. If the command is missing or fails to run, **fix the environment** (e.g. `pip install -e .`, OPA on `PATH` or `tools/opa`) and re-run—do not silently continue.

3. **Only** use **`--no-strict`** when a human explicitly asked for a non-failing exit while inspecting a denied report (e.g. scripting that parses JSON regardless). **Agents must not use `--no-strict`** to avoid fixing policy violations.

4. **If evaluation fails** (non-zero exit), read `findings[]` and each item’s `feedback.remediation` (when present). **Implement fixes** that satisfy policy, then **run the command again** until exit **0**—or stop and say clearly that policy blocks the change and why.

5. **Default semantics:** the evaluator applies **`git diff HEAD`** (with `.clawtfup/` excluded from that diff) on top of the indexed baseline, then runs policy on the **entire indexed tree** by default (`inputs.scan_mode`: **`full_tree`**). Uncommitted edits still affect **`files_after`** for patched paths. To only lint diff-touched files (legacy), use **`--diff-only`**. **Committing solely to shrink the diff** does not hide committed code from policy anymore unless **`--diff-only`** is used—and agents must not use that to evade fixes unless the user asked.

6. **Do not edit** `.clawtfup/policies/` or `.clawtfup/feedback/` to weaken rules **unless the user explicitly asked** to change policy. Product code must meet policy; policy is not something you casually delete to green the tool.

## What success looks like

- Exit code **0**, JSON with **`"allow": true`** (and no error-level findings).
- You can summarize what you ran and the outcome in one line in your final message when relevant.
