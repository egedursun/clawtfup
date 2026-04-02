**Policies:** `policy_eval.yaml` + `rego/code_edits.rego`.

Rules apply to **changed content** (`combined_after` from the diff), plus optional anchor checks on changed `.py` when `input.policy.enforce_anchor_on_changed_python` is true.

**Categories (see Rego):** unsafe eval/exec, `os.system`, `subprocess` `shell=True`, pickle/marshal, `yaml.load`, `breakpoint`, dynamic `__import__` (warning), bare `except:`, `== None` / `!= None` (warnings), optional anchor line, caller `requirements` fragments.

Remediation text: **`.clawtfup/feedback/feedback.yaml`**.
