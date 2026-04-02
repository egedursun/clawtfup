<div align="center">

<a href="logo.png"><img src="logo.png" alt="clawtfup — the policy gate with claws" width="300" /></a>

### **clawtfup**

#### *Open claws. Closed loopholes.*

**The diff walks in. OPA decides if it walks out.**
Your workspace, your Rego, one JSON verdict—no `eval` in prod unless you *like* talking to security.

<sub>Preview won’t show the art? The file is literally <code>logo.png</code> next to this README—open it from the repo root.</sub>

</div>

---

### Who this is for

**Bots first.** Humans welcome, but this doc is written so an LLM knows *exactly* what to run, what comes back, and what *not* to weasel out of. For the stricter house rules in *this* repo, see [`AGENTS.md`](AGENTS.md).

---

### The one-liner (what it does)

`clawtfup` is a tiny harness: index the tree, slap on `git diff HEAD` (`.clawtfup/` kept out of the patch text), hand the bundle to **OPA**, merge in your **`.clawtfup/policies/`** Rego, sweeten failures with **`.clawtfup/feedback/`** copy. **Default is a full-tree stare-down**—we’re not only judging the lines you touched; we’re judging the whole party you checked in.

- **CLI:** `clawtfup`
- **Python import:** `policy_eval`
- **Same thing, different shell:** `python -m policy_eval evaluate …`
- **No REST API.** This isn’t a microservice; it’s a bouncer.

---

### The ritual (agents: you actually have to do this)

1. From the **project root** (or `--workspace` that root):

   ```bash
   clawtfup evaluate --pretty
   ```

   No `clawtfup` on PATH? `pip install -e .` then `python -m policy_eval evaluate --pretty`. Still stuck? Install OPA or drop `tools/opa`—we’re not psychic.

2. **Stdout = one JSON object.** Always. Even when you’re in trouble. Stderr is for humans and grumpy stack traces.

3. **You’re only done when:** exit **0**, `"allow": true`, and zero findings with `"severity": "error"`. Anything else is “back to the editor, friend.”

4. **`findings[]` is your to-do list.** Read `code`, `message`, and `feedback.remediation` if present. Fix **product code**. Do **not** “fix” policy by nerfing `.clawtfup/` unless the **user** said so—that’s not clever, that’s cosplay.

5. **`--no-strict`** is for humans who want exit 0 while reading a train wreck. **Agents:** pretend that flag doesn’t exist unless the human typed the words.

6. **Need a smaller arena?** `--scan-prefix examples/blog` only loads that subtree. **`--diff-only`** if you’re in a hurry and only want the diff-touched paths (weaker, but sometimes the repo is the size of a small moon).

---

### JSON cheat sheet (the fields that matter)

| Path | Meaning |
|------|---------|
| `allow` | Policy said yes/no to this snapshot. |
| `findings[]` | What went wrong; empty is a good day. |
| `findings[].code` | Stable ID; pairs with feedback YAML keys. |
| `findings[].severity` | `"error"` fails strict; `"warning"` is side-eye. |
| `findings[].message` | Rego’s short story. |
| `findings[].path` | File, if the rule cares where you live. |
| `findings[].feedback` | Nicer words: `title`, `remediation`, `references`. |
| `inputs.changed_paths` | What got concatenated into the policy soup. |
| `inputs.scan_mode` | `full_tree` / `diff_only` / `prefix`. |
| `inputs.change_source` | `git_head` / `diff_file` / `stdin`. |
| `query_errors` | OPA blew up—don’t declare victory. |

---

### What you need in the room

- Python **≥ 3.11**
- **OPA** on PATH or **`tools/opa`**
- **Git** if you’re riding the default `git diff HEAD` train (else bring your own `--diff-file`)

```bash
pip install -e .
```

---

### Flags (the boring but accurate part)

```text
clawtfup evaluate [--workspace DIR] [--diff-file PATH|-] [--diff-only] [--scan-prefix PATH]
  [--input-json PATH] [--query Q] [--max-files N] [--max-file-bytes N] [--exclude-glob G]
  [--no-gitignore] [--pretty] [--no-strict]
```

| Flag | Effect |
|------|--------|
| `--workspace` | Where the code lives; policies = `<workspace>/.clawtfup/policies/`. |
| `--diff-file` / `-` | Your diff; default = `git diff HEAD` (minus `.clawtfup` in the pathspec). |
| `--diff-only` | Only diff paths—fast, forgetful. |
| `--scan-prefix` | Only one branch of the tree—surgical snacking. |
| `--input-json` | Extra OPA `input` merge. |
| `--pretty` | Pretty JSON (for carbon-based readers). |
| `--no-strict` | Exit 0 even when policy says “nuh-uh.” |

**Exits:** **0** = strict happiness. **2** = typical “you shall not merge.” Others = bad patch, missing bundle, OPA drama.

---

### Where files go

- **`.clawtfup/policies/policy_eval.yaml`** — queries + optional `findings_query`
- **`.clawtfup/policies/rego/*.rego`** — the actual law
- **`.clawtfup/feedback/*.{yaml,yml,json}`** — the “here’s how to be less wrong” layer (OPA ignores these; we attach them after)

Indexing skips `.git/` and `.clawtfup/` as *source*, skips binary-ish junk. Life’s too short to Rego your `node_modules`.

---

### OPA `input` merge (last writer wins)

1. Built-in `workspace` + `change` + `requirements` + `policy`
2. `--input-json` (wrap in `{ "input": { ... } }` if you like nesting)
3. `EvaluateOptions.input_overlay` in Python

---

### Python API (embed the bouncer)

```python
from pathlib import Path
from policy_eval.evaluate import EvaluateOptions, evaluate

report = evaluate(
    EvaluateOptions(
        workspace=Path("/path/to/project"),
        bundle_root=Path("/path/to/project/.clawtfup/policies"),
        patch_text="",
        change_source="git_head",
        index_from_git_head=True,
        full_scan=True,
    )
)
```

`full_scan` defaults **True**; **`False`** = same idea as `--diff-only`.

---

### Further reading (when you’re done being witty)

- [`AGENTS.md`](AGENTS.md) — non-optional behavior in this repo
- [`.clawtfup/policies/README.md`](.clawtfup/policies/README.md) — flavor of the bundled rules
- `pytest` + OPA for tests
- `pyproject.toml` — package name **`clawtfup`**
