# Policy for this repo: Python + security + maintainability signals we can see from text.
# Input: ARCHITECTURE.md (workspace.combined_after, files_after, changed_paths, policy, requirements).

package code_edits

default allow := false

report := {
	"allow": allow,
	"violations": [v | some v in violation],
}

allow if {
	count(violation) == 0
}

combined := input.workspace.combined_after

# --- Dynamic execution & injection (errors) ---

violation contains {
	"code": "UNSAFE_EVAL",
	"message": "Do not introduce eval(); it executes arbitrary code. (Allows ast.literal_eval.)",
	"path": "",
	"severity": "error",
} if {
	# Avoid false positive on literal_eval(
	regex.match(`[\s\S]*[^a-zA-Z0-9_]eval\(`, combined)
}

violation contains {
	"code": "UNSAFE_EXEC",
	"message": "Do not introduce exec(); it executes arbitrary code.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "exec(")
}

violation contains {
	"code": "OS_SYSTEM_CALL",
	"message": "Do not use os.system(); use subprocess with a fixed argv and no shell.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "os.system(")
}

violation contains {
	"code": "SUBPROCESS_SHELL_TRUE",
	"message": "Avoid subprocess with shell=True (injection and quoting hazards).",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "shell=True")
}

violation contains {
	"code": "UNSAFE_PICKLE",
	"message": "Do not use pickle.load(s) on untrusted data (arbitrary code execution).",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "pickle.loads(")
}

violation contains {
	"code": "UNSAFE_PICKLE_FILE",
	"message": "pickle.load( can execute code from streams; avoid for untrusted inputs.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "pickle.load(")
}

violation contains {
	"code": "UNSAFE_MARSHAL",
	"message": "marshal.loads is not a safe interchange format for untrusted bytes.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "marshal.loads(")
}

violation contains {
	"code": "UNSAFE_YAML_LOAD",
	"message": "Use yaml.safe_load, not yaml.load (unsafe constructors).",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "yaml.load(")
}

violation contains {
	"code": "DEBUG_BREAKPOINT",
	"message": "Remove breakpoint() before shipping.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "breakpoint(")
}

violation contains {
	"code": "DYNAMIC_IMPORT",
	"message": "Avoid __import__ with dynamic strings; use normal imports or importlib.import_module with care.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "__import__(")
}

# --- Python style / correctness (errors where unambiguous) ---

violation contains {
	"code": "BARE_EXCEPT",
	"message": "Do not use bare `except:`; catch Exception or a specific type.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)^\s*except\s*:\s*$`, combined)
}

violation contains {
	"code": "COMPARE_NONE",
	"message": "Compare None with `is` / `is not`, not == or !=.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`==\s*None\b`, combined)
}

violation contains {
	"code": "COMPARE_NOT_NONE",
	"message": "Compare None with `is not`, not !=.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`!=\s*None\b`, combined)
}

# --- Optional governed Python files (anchor line) ---

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

# --- Caller-driven requirements ---

violation contains {
	"code": "MISSING_FRAGMENT",
	"message": sprintf("missing required fragment: %s", [frag]),
	"path": "",
	"severity": "error",
} if {
	some frag in input.requirements.must_contain
	not contains(combined, frag)
}

violation contains {
	"code": "DISALLOWED_FRAGMENT",
	"message": sprintf("disallowed fragment present: %s", [frag]),
	"path": "",
	"severity": "error",
} if {
	some frag in input.requirements.must_not_contain
	contains(combined, frag)
}
