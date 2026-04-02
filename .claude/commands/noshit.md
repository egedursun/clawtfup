Execute the following task, then run the policy gate — no exceptions.

## Task

$ARGUMENTS

## After completing the task

Run from the repository root:

```bash
python -m policy_eval evaluate --pretty
```

If `clawtfup` is on PATH you can also use `clawtfup evaluate --pretty`.

**Enforce the result strictly:**

- Exit **0** + `"allow": true` → done.
- Any other outcome → read every item in `findings[]`, implement fixes that satisfy policy, and re-run until exit 0.
- Do **not** use `--no-strict` to paper over failures.
- Do **not** edit `.clawtfup/policies/` or `.clawtfup/feedback/` to weaken rules.
