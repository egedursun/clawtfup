# Policy: security, architecture hints, design, syntax/style, quality (Python, JS/TS, templates).
# Primary signal: changed hunks (combined_after). Path-scoped rules use files_after[path] + changed_paths.
# See repository README.md and .clawtfup/policies/README.md.

package code_edits

import rego.v1

default allow := false

report := {
	"allow": allow,
	"violations": [v | some v in violation],
}

allow if {
	count(violation) == 0
}

combined := input.workspace.combined_after
changed := input.workspace.changed_paths
files := input.workspace.files_after

# -----------------------------------------------------------------------------
# Security: dynamic execution, deserialization, injection
# -----------------------------------------------------------------------------

violation contains {
	"code": "UNSAFE_EVAL",
	"message": "Do not use eval(); use safe parsing or ast.literal_eval for constants only.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*[^a-zA-Z0-9_]eval\(`, combined)
}

# Avoid .exec( in JS (child_process.exec, regex.exec) and attribute access.
violation contains {
	"code": "UNSAFE_EXEC",
	"message": "Do not use Python exec(); no runtime code strings.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)(^|[^.\w])exec\s*\(`, combined)
}

violation contains {
	"code": "OS_SYSTEM_CALL",
	"message": "Do not use os.system(); use subprocess with argv list, shell=False.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "os.system(")
}

violation contains {
	"code": "SUBPROCESS_SHELL_TRUE",
	"message": "subprocess shell=True enables injection; use argv lists.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "shell=True")
}

violation contains {
	"code": "UNSAFE_PICKLE",
	"message": "pickle.loads on untrusted data is unsafe.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "pickle.loads(")
}

violation contains {
	"code": "UNSAFE_PICKLE_FILE",
	"message": "pickle.load executes pickle streams; trust boundary only.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "pickle.load(")
}

violation contains {
	"code": "UNSAFE_MARSHAL",
	"message": "marshal.loads is not for untrusted bytes.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "marshal.loads(")
}

violation contains {
	"code": "UNSAFE_YAML_LOAD",
	"message": "Use yaml.safe_load, not yaml.load.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "yaml.load(")
}

violation contains {
	"code": "DEBUG_BREAKPOINT",
	"message": "Remove breakpoint() before commit.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "breakpoint(")
}

violation contains {
	"code": "DYNAMIC_IMPORT",
	"message": "Avoid __import__ with dynamic module names.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "__import__(")
}

violation contains {
	"code": "SQL_FSTRING_QUERY",
	"message": "Do not build SQL with f-strings; use bound parameters / ORM.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.\s*execute\s*\(\s*f["']`, combined)
}

violation contains {
	"code": "SQL_FSTRING_EXECUTEMANY",
	"message": "Do not build SQL with f-strings in executemany.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.\s*executemany\s*\(\s*f["']`, combined)
}

violation contains {
	"code": "TLS_VERIFY_DISABLED",
	"message": "Do not disable TLS verification (verify=False) for production clients.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "verify=False")
}

violation contains {
	"code": "JWT_VERIFY_DISABLED",
	"message": "jwt.decode(..., verify=False) disables signature verification.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "jwt.decode")
	contains(combined, "verify=False")
}

violation contains {
	"code": "OPEN_REDIRECT_REQUEST",
	"message": "Do not redirect to user-controlled URLs from request args/form without allowlist.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "redirect(")
	contains(combined, "request.")
	regex.match(`[\s\S]*redirect\s*\(\s*request\.`, combined)
}

violation contains {
	"code": "SSTI_RENDER_TEMPLATE_STRING",
	"message": "render_template_string with request/user input is SSTI risk; use render_template + static templates.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "render_template_string(")
	contains(combined, "request.")
}

violation contains {
	"code": "FLASK_DEBUG_ENABLED",
	"message": "Do not commit app.run(debug=True); gate debug with env (e.g. FLASK_DEBUG).",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.run\s*\([^)]*debug\s*=\s*True`, combined)
}

violation contains {
	"code": "DJANGO_OR_SETTINGS_DEBUG_TRUE",
	"message": "DEBUG = True must not ship in production settings.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)^\s*DEBUG\s*=\s*True\s*$`, combined)
}

violation contains {
	"code": "FLASK_WTF_CSRF_DISABLED",
	"message": "Do not disable CSRF (WTF_CSRF_ENABLED = False) without a documented exception.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*WTF_CSRF_ENABLED\s*=\s*False`, combined)
}

violation contains {
	"code": "SESSION_COOKIE_HTTPONLY_OFF",
	"message": "SESSION_COOKIE_HTTPONLY should stay True for session cookies.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*SESSION_COOKIE_HTTPONLY\s*=\s*False`, combined)
}

violation contains {
	"code": "SESSION_COOKIE_SECURE_OFF",
	"message": "Prefer SESSION_COOKIE_SECURE = True behind HTTPS in production.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*SESSION_COOKIE_SECURE\s*=\s*False`, combined)
}

violation contains {
	"code": "CORS_ALLOW_ALL_ORIGINS",
	"message": "CORS allow_origins=['*'] is unsafe with credentials; narrow origins.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*allow_origins\s*=\s*\[\s*['\"]\*['\"]\s*\]`, combined)
}

violation contains {
	"code": "CORS_ADD_ALL_HEADER",
	"message": "Access-Control-Allow-Origin: * with credentialed APIs is wrong; list explicit origins.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*Access-Control-Allow-Origin['\"]\s*,\s*['\"]\*['\"]`, combined)
}

violation contains {
	"code": "DJANGO_CSRF_EXEMPT",
	"message": "@csrf_exempt on state-changing routes needs explicit security review.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "@csrf_exempt")
}

violation contains {
	"code": "HARDCODED_SECRET_MATERIAL",
	"message": "Possible PEM or embedded secret material; use env/secret manager.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*-----BEGIN [A-Z ]+PRIVATE KEY-----`, combined)
}

violation contains {
	"code": "AWS_ACCESS_KEY_IN_DIFF",
	"message": "AWS access key id pattern in diff; rotate keys and use env/IAM roles.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`AKIA[0-9A-Z]{16}`, combined)
}

violation contains {
	"code": "DOM_INNERHTML_ASSIGN",
	"message": "innerHTML with untrusted data causes XSS; use textContent or sanitize.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.innerHTML\s*=`, combined)
}

violation contains {
	"code": "REACT_DANGEROUS_INNER_HTML",
	"message": "dangerouslySetInnerHTML requires trusted/sanitized HTML only.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "dangerouslySetInnerHTML")
}

violation contains {
	"code": "DOCUMENT_WRITE",
	"message": "document.write is brittle and XSS-prone; avoid.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "document.write(")
}

violation contains {
	"code": "HTML_JAVASCRIPT_URL",
	"message": "javascript: URLs in href/src are XSS vectors.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*href\s*=\s*["']javascript:`, combined)
}

violation contains {
	"code": "HTML_INLINE_EVENT_TEMPLATE",
	"message": "Inline handlers mixing {{ }} output can cause XSS; prefer addEventListener + escaped data.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*on\w+\s*=\s*["'][^"']*\{\{`, combined)
}

violation contains {
	"code": "DJANGO_MARK_SAFE",
	"message": "mark_safe disables escaping; only for truly trusted static HTML.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "mark_safe(")
}

violation contains {
	"code": "JINJA_AUTOESCAPE_DISABLED",
	"message": "Do not disable Jinja autoescape globally.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\{\%\s*autoescape\s+false`, combined)
}

violation contains {
	"code": "JINJA_SAFE_FILTER",
	"message": "|safe skips escaping; verify input is trusted or sanitized.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*\|\s*safe\b`, combined)
}

violation contains {
	"code": "WEAK_HASH_MD5",
	"message": "md5 is not for passwords or MACs; use bcrypt/argon2 or hmac+sha256+compare_digest.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "hashlib.md5(")
}

violation contains {
	"code": "WEAK_HASH_SHA1_PASSWORD",
	"message": "sha1 is weak for passwords; use modern KDFs.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*(password|passwd|secret).{0,200}hashlib\.sha1\(`, combined)
}

violation contains {
	"code": "CHMOD_WORLD_WRITABLE",
	"message": "chmod 0o777 is world-writable; use least privilege.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*chmod\s*\(\s*[^,]+,\s*0o777`, combined)
}

violation contains {
	"code": "TEMPFILE_MKTEMP",
	"message": "tempfile.mktemp is race-prone; use NamedTemporaryFile/delete=False or mkstemp.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "mktemp(")
}

violation contains {
	"code": "SSL_LEGACY_CONTEXT",
	"message": "ssl.PROTOCOL_TLSv1 or PROTOCOL_SSLv23 is legacy; use ssl.create_default_context().",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*ssl\.PROTOCOL_(TLSv1|TLSv1_1|SSLv2|SSLv3|SSLv23)`, combined)
}

violation contains {
	"code": "URLLIB3_DISABLE_WARNINGS",
	"message": "urllib3.disable_warnings hides TLS problems; fix verify/roots instead.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "urllib3.disable_warnings")
}

violation contains {
	"code": "HARDCODED_DATABASE_URL",
	"message": "DATABASE_URL-style literals belong in env/secret store, not source.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?i)[\s\S]*DATABASE_URL\s*=\s*["'][^"']+["']`, combined)
}

# -----------------------------------------------------------------------------
# Architecture & layering (path + content)
# -----------------------------------------------------------------------------

violation contains {
	"code": "ENV_OR_SECRETS_FILE_COMMITTED",
	"message": "Environment/secret files should not be versioned; use samples (.env.example) only.",
	"path": path,
	"severity": "error",
} if {
	some path in changed
	regex.match(`(?i)(^|/)\.env($|\.)`, path)
}

violation contains {
	"code": "CREDENTIAL_FILENAME_IN_DIFF",
	"message": "Credential-like path in change set; confirm it is not a real secret.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i)(^|/)(credentials\.json|google-services\.json|service-account.*\.json|id_rsa$|\.ppk$)`, path)
}

violation contains {
	"code": "SQL_IN_HTTP_HANDLER_LAYER",
	"message": "Raw SQL/cursors in route/view modules blur HTTP vs persistence; prefer repository/service layer.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i).*\.py$`, path)
	regex.match(`(?i)(routes?|views?|handlers?|controllers?|blueprints?|api)/`, path)
	content := files[path]
	contains(content, "execute(")
	not regex.match(`(?i)(repositories?|repos?|dao|persistence|db|models|stores?)/`, path)
}

violation contains {
	"code": "SQLITE_IN_FRONTEND_PATH",
	"message": "SQLite (or similar) in a frontend path suggests wrong layering or unsafe bundling.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i)(^|/)(frontend|client|web|src/components)(/|$)`, path)
	regex.match(`(?i).*\.(tsx|ts|jsx|js|vue|svelte)$`, path)
	regex.match(`(?i)[\s\S]*(sqlite3|better-sqlite3|sql\.js)`, combined)
}

violation contains {
	"code": "SUBPROCESS_IN_DOMAIN_LAYER",
	"message": "subprocess/os.system in domain/entity layer couples core logic to the host; isolate in infra/adapters.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i).*\.py$`, path)
	regex.match(`(?i)(^|/)(domain|entities|core/model)(/|$)`, path)
	content := files[path]
	regex.match(`[\s\S]*(subprocess\.|os\.system\()`, content)
}

violation contains {
	"code": "HTTP_CLIENT_IN_DOMAIN_LAYER",
	"message": "requests/httpx in domain layer couples business rules to IO; move to services/clients.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i).*\.py$`, path)
	regex.match(`(?i)(^|/)(domain|entities)(/|$)`, path)
	content := files[path]
	regex.match(`(?m)^(?:from|import)\s+(requests|httpx)\b`, content)
}

violation contains {
	"code": "OVERSIZED_MODULE",
	"message": "Very large modules are hard to review and violate single-responsibility; split by feature.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i).*\.(py|ts|tsx|js|jsx)$`, path)
	content := files[path]
	strings.count(content, "\n") > 500
}

violation contains {
	"code": "DEEP_RELATIVE_IMPORT",
	"message": "Deep relative imports (..) signal package layout debt; prefer absolute package imports.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	content := files[path]
	regex.match(`(?m)^from\s+\.{2,}`, content)
}

# -----------------------------------------------------------------------------
# Design & API hygiene
# -----------------------------------------------------------------------------

violation contains {
	"code": "MUTABLE_DEFAULT_ARGUMENT",
	"message": "Mutable default args (list/dict) are shared across calls; use None + factory inside the function.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)def\s+\w+\([^)]*=\s*\[\s*\]`, combined)
}

violation contains {
	"code": "MUTABLE_DEFAULT_DICT",
	"message": "Mutable default dict in def is a shared singleton; use None and instantiate in the body.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)def\s+\w+\([^)]*=\s*\{\s*\}`, combined)
}

violation contains {
	"code": "STAR_IMPORT",
	"message": "Wildcard imports pollute namespaces and confuse static analysis; import explicit symbols.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)^from\s+\S+\s+import\s+\*\s*$`, combined)
}

violation contains {
	"code": "RAISE_GENERIC_EXCEPTION",
	"message": "Raise specific exceptions (ValueError, HTTPException, etc.) instead of bare Exception.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*raise\s+Exception\s*\(`, combined)
}

violation contains {
	"code": "NOT_IMPLEMENTED_IN_RUNTIME",
	"message": "NotImplementedError in product code will surface at runtime; finish or gate behind tests.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*raise\s+NotImplementedError`, combined)
}

violation contains {
	"code": "EMPTY_EXCEPT_PASS",
	"message": "except: pass / except Exception: pass swallows failures; log, handle, or re-raise.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)except\s*:\s*\n\s*pass\b`, combined)
}

violation contains {
	"code": "EMPTY_EXCEPT_EXCEPTION_PASS",
	"message": "Broad except Exception with pass hides bugs; narrow the type or handle explicitly.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)except\s+Exception\s*:\s*\n\s*pass\b`, combined)
}

violation contains {
	"code": "COMPARE_BOOLEAN_TO_TRUE",
	"message": "Use `if flag:` not `== True` (PEP 8 / readability).",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*==\s*True\b`, combined)
}

violation contains {
	"code": "COMPARE_BOOLEAN_TO_FALSE",
	"message": "Use `if not flag:` or `is False` only when identity matters.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*==\s*False\b`, combined)
}

violation contains {
	"code": "USELESS_COMPARISON_LITERAL",
	"message": "Comparing to True/False/None with == is usually redundant or wrong; prefer `is None`.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*!=\s*False\b`, combined)
}

# -----------------------------------------------------------------------------
# Syntax & static checks (textual)
# -----------------------------------------------------------------------------

violation contains {
	"code": "PYTHON2_STYLE_SUPER",
	"message": "super(Class, self) is Python 2 style; use super().",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*super\s*\(\s*\w+\s*,\s*self\s*\)`, combined)
}

violation contains {
	"code": "DEPRECATED_ASYNCIO_COROUTINE",
	"message": "@asyncio.coroutine is deprecated; use async def.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "@asyncio.coroutine")
}

violation contains {
	"code": "SETATTR_DYNAMIC_NAME",
	"message": "setattr combined with request/dynamic data obscures API surface; prefer explicit attributes.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "setattr(")
	regex.match(`[\s\S]*(request\.|kwargs\[|locals\()`, combined)
}

violation contains {
	"code": "GLOBAL_STATEMENT",
	"message": "global statement makes flow hard to follow; refactor to smaller scope or class state.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)^\s*global\s+\w+`, combined)
}

violation contains {
	"code": "TS_IGNORE",
	"message": "@ts-ignore and @ts-nocheck hide type errors; fix types or narrow suppression.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*@(ts-ignore|ts-nocheck)`, combined)
}

violation contains {
	"code": "TS_ESLINT_DISABLE_FILE",
	"message": "File-level eslint-disable is broad; prefer line-scoped rules with justification.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)^\s*/\*\s*eslint-disable\s`, combined)
}

violation contains {
	"code": "JS_VAR_DECLARATION",
	"message": "Prefer const/let over var (block scope, TDZ).",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)^\s*var\s+\w+`, combined)
}

violation contains {
	"code": "PYTHON_TYPE_IGNORE",
	"message": "# type: ignore without code silences mypy; use specific error codes.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)# type:\s*ignore\s*$`, combined)
}

violation contains {
	"code": "RUFF_NOQA_FILE",
	"message": "ruff: noqa on whole file is heavy-handed; scope rules or fix violations.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)# ruff: noqa`, combined)
}

# -----------------------------------------------------------------------------
# Style (PEP 8-ish, formatting)
# -----------------------------------------------------------------------------

violation contains {
	"code": "TAB_INDENTATION",
	"message": "Use spaces for indentation in Python (PEP 8).",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	regex.match(`(?m)^\t+`, files[path])
}

violation contains {
	"code": "TRAILING_WHITESPACE",
	"message": "Trailing whitespace adds noisy diffs; strip end-of-line spaces.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?m) +\n`, files[path])
}

violation contains {
	"code": "MULTIPLE_STATEMENTS_SEMICOLON",
	"message": "Multiple statements on one line (semicolons) hurt readability.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	regex.match(`(?m)^[^#\"']*;[^#\"']*;`, files[path])
}

violation contains {
	"code": "BACKSLASH_LINE_CONTINUATION",
	"message": "Backslash line continuations are fragile; use parentheses for implicit continuation.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	regex.match(`(?m)\\\s*$`, files[path])
}

violation contains {
	"code": "LONG_LINE_OVER_120",
	"message": "Lines over ~120 chars are hard to review in diffs; wrap expressions.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i).*\.(py|ts|tsx|js|jsx|css|scss)$`, path)
	regex.match(`(?m)^.{121,}$`, files[path])
}

violation contains {
	"code": "IF_NOT_NONE_ANTIPATTERN",
	"message": "Use `if x is not None` instead of `if not x is None` (PEP 8).",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*if\s+not\s+\w+\s+is\s+None`, combined)
}

# -----------------------------------------------------------------------------
# Quality & maintainability
# -----------------------------------------------------------------------------

violation contains {
	"code": "TECH_DEBT_TODO",
	"message": "TODO left in changed code; track in issue tracker or resolve before merge.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?i)[\s\S]*(TODO|FIXME|HACK|XXX)(\s|:|\(|$)`, combined)
}

violation contains {
	"code": "PRINT_IN_APP_MODULE",
	"message": "print() in application modules; prefer logging.getLogger(__name__).",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	not regex.match(`(?i)(^|/)tests?(/|$)`, path)
	not regex.match(`(?i)(^|/)examples(/|$)`, path)
	not regex.match(`(?i)(^|/)scripts(/|$)`, path)
	not regex.match(`(?i)test_[^/]+\.py$`, path)
	not regex.match(`(?i)(^|/)conftest\.py$`, path)
	content := files[path]
	contains(content, "print(")
}

violation contains {
	"code": "BLOCKING_INPUT_CALL",
	"message": "input() blocks the event loop / request thread; avoid in servers and UIs.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	not regex.match(`(?i)(^|/)tests?(/|$)`, path)
	not regex.match(`(?i)(^|/)scripts(/|$)`, path)
	content := files[path]
	contains(content, "input(")
}

violation contains {
	"code": "TIME_SLEEP_IN_APP",
	"message": "time.sleep in app code usually belongs in jobs/tests; use scheduling or async waits.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	not regex.match(`(?i)(^|/)tests?(/|$)`, path)
	content := files[path]
	contains(content, "time.sleep(")
}

violation contains {
	"code": "ASSERT_IN_RUNTIME_MODULE",
	"message": "assert can be stripped with python -O; use explicit checks in production paths.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	not regex.match(`(?i)(^|/)tests?(/|$)`, path)
	not regex.match(`(?i)test_[^/]+\.py$`, path)
	content := files[path]
	regex.match(`(?m)^\s*assert\s+`, content)
}

violation contains {
	"code": "PYLINT_BROAD_DISABLE",
	"message": "pylint: disable=file-wide or overly broad; narrow to symbols and document why.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)# pylint:\s*disable=\s*[^#\n]*\b(all|W|E)\b`, combined)
}

violation contains {
	"code": "ANY_CAST_TYPESCRIPT",
	"message": "as any / : any erases types; narrow with generics or unknown + guards.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*\bas\s+any\b`, combined)
}

violation contains {
	"code": "TYPESCRIPT_ANY_TYPE",
	"message": "Explicit any in TypeScript defeats static safety.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*:\s*any\b`, combined)
}

violation contains {
	"code": "REACT_KEY_INDEX",
	"message": "key={index} in lists is unstable when order changes; prefer stable ids.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*key=\{?\s*index\s*\}?`, combined)
}

# -----------------------------------------------------------------------------
# Python style (existing)
# -----------------------------------------------------------------------------

violation contains {
	"code": "BARE_EXCEPT",
	"message": "No bare except:; catch Exception or specific types.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)^\s*except\s*:\s*$`, combined)
}

violation contains {
	"code": "COMPARE_NONE",
	"message": "Use `is None`, not ==.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`==\s*None\b`, combined)
}

violation contains {
	"code": "COMPARE_NOT_NONE",
	"message": "Use `is not None`, not !=.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`!=\s*None\b`, combined)
}

# -----------------------------------------------------------------------------
# Optional anchor & caller requirements
# -----------------------------------------------------------------------------

violation contains {
	"code": "MISSING_ANCHOR",
	"message": msg,
	"path": path,
	"severity": "error",
} if {
	input.policy.enforce_anchor_on_changed_python == true
	some path in changed
	regex.match(`.*\.py$`, path)
	content := files[path]
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
