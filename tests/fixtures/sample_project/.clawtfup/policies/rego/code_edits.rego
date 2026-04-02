# Sample Rego for tests — expected input shape in ARCHITECTURE.md.

package code_edits

default allow := false

report := {
	"allow": allow,
	"violations": [v | some v in violation],
}

allow if {
	count(violation) == 0
}

violation contains {
	"code": "FORBIDDEN_PATTERN",
	"message": sprintf("forbidden pattern present: %s", [p]),
	"path": "",
	"severity": "error",
} if {
	p := ["eval(", "exec(", "os.system", "subprocess."][_]
	contains(input.workspace.combined_after, p)
}

violation contains {
	"code": "MISSING_ANCHOR",
	"message": msg,
	"path": path,
	"severity": "error",
} if {
	input.policy.enforce_anchor_on_changed_python == true
	some path in input.workspace.changed_paths
	regex.match(`.*\.py$`, path)
	content := input.workspace.files_after[path]
	not regex.match(`(?m)^# POLICY_ANCHOR_DO_NOT_REMOVE\s*$`, content)
	msg := sprintf("missing policy anchor line in %s", [path])
}

violation contains {
	"code": "MISSING_FRAGMENT",
	"message": sprintf("missing required fragment: %s", [frag]),
	"path": "",
	"severity": "error",
} if {
	some frag in input.requirements.must_contain
	not contains(input.workspace.combined_after, frag)
}

violation contains {
	"code": "DISALLOWED_FRAGMENT",
	"message": sprintf("disallowed fragment present: %s", [frag]),
	"path": "",
	"severity": "error",
} if {
	some frag in input.requirements.must_not_contain
	contains(input.workspace.combined_after, frag)
}
