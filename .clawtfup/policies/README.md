# Policy bundle

Full repository documentation: **[`README.md`](../../README.md)**. Agent rules: **[`AGENTS.md`](../../AGENTS.md)**.

---

## Structure

```
.clawtfup/policies/
├── policy_eval.yaml        # Manifest: which OPA queries to run
└── rego/
    └── code_edits.rego     # Policy rules (extend or replace)
```

```
.clawtfup/feedback/
└── feedback.yaml           # Remediation text keyed by violation code
```

---

## Manifest (`policy_eval.yaml`)

```yaml
queries:
  - data.code_edits.report        # list of OPA queries to run

findings_query: data.code_edits.report  # which result holds {allow, violations[]}
```

- `queries` — each entry is evaluated; results appear under `results` in the JSON report.
- `findings_query` — must be one of the queries. Its result is parsed into `findings[]`.

---

## OPA input contract

clawtfup builds the following input document and passes it to every query. Your Rego can reference any field here.

```json
{
  "workspace": {
    "root": "/absolute/path/to/workspace",
    "files_before": { "relative/path.py": "file content before patch" },
    "files_after":  { "relative/path.py": "file content after patch"  },
    "changed_paths": ["relative/path.py"],
    "combined_after": "--- FILE: relative/path.py ---\nfile content\n\n..."
  },
  "change": {
    "format": "unified",
    "text": "--- a/relative/path.py\n+++ b/relative/path.py\n..."
  },
  "requirements": {
    "must_contain":     [],
    "must_not_contain": []
  },
  "policy": {
    "enforce_anchor_on_changed_python": false
  }
}
```

### Key fields explained

| Field | When to use |
|:------|:------------|
| `workspace.combined_after` | Full content of all changed files concatenated. Fast for single-pass substring/regex checks across everything touched. |
| `workspace.files_after[path]` | Per-file content after the patch. Use with `workspace.changed_paths` to write path-scoped rules (e.g. "no DB calls in views/"). |
| `workspace.files_before[path]` | Content before the patch. Useful for "was this field present before?" checks. |
| `workspace.changed_paths` | List of POSIX-relative paths touched by the diff. Iterate these for per-file rules. |
| `change.text` | The raw unified diff text, if you need line-level heuristics. |
| `requirements.must_contain` | Optional list of strings that `combined_after` must include (caller-supplied anchors). |
| `requirements.must_not_contain` | Optional list of strings that `combined_after` must not include. |
| `policy.enforce_anchor_on_changed_python` | When `true`, each changed `.py` file must contain a sentinel comment (`# POLICY_ANCHOR_DO_NOT_REMOVE`). |

---

## Required output shape

The `findings_query` result must be a Rego object with exactly this shape:

```rego
report := {
    "allow": allow,                             # bool
    "violations": [v | some v in violation],    # collected violation set
}

allow if { count(violation) == 0 }
```

Each element of `violation` must be an object with at minimum:

| Field | Type | Required | Notes |
|:------|:-----|:---------|:------|
| `code` | string | yes | Stable identifier. Must match a key in `feedback.yaml` to get remediation text. |
| `message` | string | yes | Short explanation shown to the agent. |
| `severity` | string | yes | `"error"` triggers exit 2 in strict mode; `"warning"` does not. |
| `path` | string | yes | Relative POSIX path when the rule is file-scoped; `""` for global/combined checks. |

---

## Writing a new rule

### Pattern 1 — global (combined_after)

Use this for content that could appear in any changed file:

```rego
violation contains {
    "code":     "MY_RULE",
    "message":  "Describe the problem and what to do instead.",
    "path":     "",
    "severity": "error",
} if {
    contains(input.workspace.combined_after, "dangerous_function(")
}
```

### Pattern 2 — path-scoped (per-file)

Use this when the rule depends on where the code lives (e.g. layering constraints):

```rego
violation contains {
    "code":     "DB_IN_VIEW",
    "message":  "Database queries must not appear in view modules.",
    "path":     path,
    "severity": "warning",
} if {
    some path in input.workspace.changed_paths
    regex.match(`^views/`, path)
    contains(input.workspace.files_after[path], "db.session")
}
```

### Pattern 3 — before/after comparison

Use this to detect newly introduced patterns:

```rego
violation contains {
    "code":     "INTRODUCED_TODO",
    "message":  "A TODO comment was introduced in this change.",
    "path":     path,
    "severity": "warning",
} if {
    some path in input.workspace.changed_paths
    not contains(input.workspace.files_before[path], "TODO")
    contains(input.workspace.files_after[path], "TODO")
}
```

---

## Adding feedback for a new rule

Add an entry to `.clawtfup/feedback/feedback.yaml` with the same key as your violation `code`:

```yaml
MY_RULE:
  severity: error                  # optional override; OPA severity wins if omitted
  title: Short human-readable title
  remediation: >
    Explain what the agent (or developer) should do to fix this. Be specific.
    Mention safer alternatives and point to docs when relevant.
  references:
    - https://example.com/docs/safe-alternative
```

Entries in later files (sorted by name) override earlier ones, so you can ship overrides in a separate `feedback_overrides.yaml` without touching the base file.

---

## Rule categories in `code_edits.rego`

| Category | Signal used | Examples |
|:---------|:------------|:---------|
| Security | `combined_after` (global) | `UNSAFE_EVAL`, `SQL_FSTRING_QUERY`, `TLS_VERIFY_DISABLED`, `UNSAFE_PICKLE` |
| Serialisation / deserialization | `combined_after` | `UNSAFE_YAML_LOAD`, `UNSAFE_MARSHAL` |
| Injection / auth | `combined_after` | `SSTI_RENDER_TEMPLATE_STRING`, `JWT_VERIFY_DISABLED`, `OPEN_REDIRECT_REQUEST` |
| Secrets | `combined_after` | `SECRET_IN_CODE`, `AWS_KEY_IN_CODE` |
| Python portability | `combined_after` | `PYTHON2_PRINT_STATEMENT`, `PYTHON2_EXCEPT_SYNTAX`, `PYTHON2_HAS_KEY` |
| Architecture / layering | `files_after[path]` + `changed_paths` | `DB_QUERY_IN_VIEW`, `HTTP_CLIENT_IN_DOMAIN` |
| Design anti-patterns | `files_after[path]` + `changed_paths` | `MUTABLE_DEFAULT_ARGUMENT`, `GLOBAL_STATEMENT_IN_FUNCTION` |
| Style / formatting | `files_after[path]` + `changed_paths` | `LINE_TOO_LONG`, `LEADING_TABS` |
| Optional requirements | `combined_after` + `input.requirements` | `MISSING_ANCHOR`, `MISSING_FRAGMENT`, `DISALLOWED_FRAGMENT` |

---

## Adding a new `.rego` file

OPA loads the entire `rego/` directory as a bundle. You can add additional `.rego` files with a different package name and add their query to `policy_eval.yaml`:

```rego
# .clawtfup/policies/rego/my_team_rules.rego
package my_team_rules

import rego.v1

default allow := false

report := {
    "allow": allow,
    "violations": [v | some v in violation],
}

allow if { count(violation) == 0 }

violation contains { ... } if { ... }
```

```yaml
# policy_eval.yaml
queries:
  - data.code_edits.report
  - data.my_team_rules.report
findings_query: data.code_edits.report   # or whichever you want parsed into findings[]
```

If you want findings from both packages merged, combine them in a single report rule or extend `code_edits.rego` with additional violations.
