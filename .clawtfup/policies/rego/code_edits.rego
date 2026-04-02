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
# Extended security: subprocess strings, legacy I/O, crypto foot-guns, debug
# -----------------------------------------------------------------------------

violation contains {
	"code": "OS_POPEN",
	"message": "os.popen is a shell wrapper; use subprocess.run(argv, shell=False).",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "os.popen(")
}

violation contains {
	"code": "PICKLE_DUMP",
	"message": "pickle.dump produces executable streams; treat as code export, not a data interchange format.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "pickle.dump(")
}

violation contains {
	"code": "MARSHAL_DUMP",
	"message": "marshal.dump is not a portable or safe interchange format for untrusted consumers.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "marshal.dump(")
}

violation contains {
	"code": "SHELVE_OPEN",
	"message": "shelve is pickle-backed; do not open shelves from untrusted paths or users.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "shelve.open(")
}

violation contains {
	"code": "IMPORT_IMP_MODULE",
	"message": "The imp module is removed in Python 3.12+; use importlib.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)^(?:from\s+imp\s+import|import\s+imp\b)`, combined)
}

violation contains {
	"code": "IMPORTLIB_RELOAD_IN_APP",
	"message": "importlib.reload in application code is usually a smell (hot reload hacks); prefer explicit lifecycle.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	not regex.match(`(?i)(^|/)tests?(/|$)`, path)
	content := files[path]
	contains(content, "importlib.reload(")
}

violation contains {
	"code": "COMPILE_DYNAMIC_WITH_REQUEST",
	"message": "compile() combined with request-derived text is code injection; do not build bytecode from HTTP input.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "compile(")
	contains(combined, "request.")
}

violation contains {
	"code": "EVAL_WITH_GLOBALS_LOCALS",
	"message": "eval/exec with explicit globals/locals widens effect; remove or replace with safe parsers.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*eval\s*\([^)]*globals\s*\(`, combined)
}

violation contains {
	"code": "EXEC_WITH_GLOBALS",
	"message": "exec with globals/locals is almost never appropriate for product code.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*(?m)(^|[^.\w])exec\s*\([^)]*globals\s*\(`, combined)
}

violation contains {
	"code": "OPEN_PATH_FROM_REQUEST",
	"message": "Opening files using request-derived paths enables LFI/path traversal; use allowlists and safe_join.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*open\s*\([^)]*request\.`, combined)
}

violation contains {
	"code": "PATH_FROM_REQUEST",
	"message": "Path(...) built from request data is unsafe without strict normalization and jail roots.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*Path\s*\([^)]*request\.`, combined)
}

violation contains {
	"code": "OS_UNLINK_FROM_REQUEST",
	"message": "Deleting paths from request data is critical RCE/data-loss territory.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*os\.(unlink|remove|rmdir)\s*\([^)]*request\.`, combined)
}

violation contains {
	"code": "SEND_FILE_FROM_REQUEST",
	"message": "send_file/send_from_directory with request-controlled paths enables path traversal.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*(send_file|send_from_directory)\s*\([^)]*request\.`, combined)
}

violation contains {
	"code": "SQL_STRING_CONCAT_EXECUTE",
	"message": "String concatenation into SQL execute() is injection-prone; use parameters.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.\s*execute\s*\(\s*["'][^"']*["']\s*\+`, combined)
}

violation contains {
	"code": "XML_PARSE_UNTRUSTED_REQUEST",
	"message": "Parsing XML from request bodies risks billion-laughs/XXE unless parser is hardened.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "request.")
	regex.match(`[\s\S]*(ET\.fromstring|fromstring|parseString|XMLParser)\s*\(`, combined)
}

violation contains {
	"code": "JINJA_ENV_NO_AUTOESCAPE",
	"message": "Jinja2 Environment(autoescape=False) is XSS-prone for HTML contexts.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*autoescape\s*=\s*False`, combined)
	contains(combined, "Environment(")
}

violation contains {
	"code": "SSL_UNVERIFIED_CONTEXT",
	"message": "ssl._create_unverified_context() disables certificate verification.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "_create_unverified_context(")
}

violation contains {
	"code": "SSL_CERT_NONE",
	"message": "ssl.CERT_NONE on verify/verify_mode disables peer certificate validation.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*(verify_mode|verify)\s*=\s*ssl\.CERT_NONE`, combined)
}

violation contains {
	"code": "SSL_WRAP_SOCKET_LEGACY",
	"message": "ssl.wrap_socket is legacy; prefer create_default_context() and wrap_socket on the context.",
	"path": "",
	"severity": "warning",
} if {
	contains(combined, "ssl.wrap_socket(")
}

violation contains {
	"code": "FTP_CLIENT_USAGE",
	"message": "FTP is cleartext and brittle; prefer SFTP/HTTPS APIs.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*ftplib\.`, combined)
}

violation contains {
	"code": "TELNET_CLIENT_USAGE",
	"message": "telnetlib is cleartext and deprecated; do not use for sensitive operations.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "telnetlib")
}

violation contains {
	"code": "HTTP_CLIENT_PLAINTEXT",
	"message": "http.client.HTTPConnection sends traffic in cleartext; use HTTPS client stacks.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*HTTPConnection\s*\(`, combined)
	contains(combined, "http.client")
}

violation contains {
	"code": "REQUESTS_HTTP_URL",
	"message": "requests/httpx to http:// URLs is cleartext on the wire; use https:// or internal TLS.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*(requests|httpx)\.(get|post|put|patch|delete|request)\(\s*["']http://`, combined)
}

violation contains {
	"code": "RANDOM_FOR_SECRET_MATERIAL",
	"message": "random is not cryptographically secure; use secrets module for tokens/passwords.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*random\.(choice|getrandbits|randint|randrange)\s*\([\s\S]{0,240}(password|passwd|secret|token|csrf|nonce|salt)`, combined)
}

violation contains {
	"code": "RANDOM_SEED_CALL",
	"message": "random.seed weakens unpredictability for security-sensitive flows; avoid in servers handling secrets.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*random\.seed\s*\(`, combined)
}

violation contains {
	"code": "PDB_SET_TRACE",
	"message": "Remove pdb.set_trace / breakpoint hooks from committed code.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*pdb\.set_trace\s*\(`, combined)
}

violation contains {
	"code": "IPYTHON_EMBED",
	"message": "IPython.embed() must not ship in production entrypoints.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "IPython.embed(")
}

violation contains {
	"code": "PUDB_SET_TRACE",
	"message": "pudb.set_trace is an interactive debugger; remove before merge.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*pudb\.set_trace\s*\(`, combined)
}

violation contains {
	"code": "WARNINGS_GLOBAL_IGNORE",
	"message": "Globally ignoring warnings hides security deprecations (e.g. weak crypto); filter narrowly.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*warnings\.(filterwarnings|simplefilter)\s*\(`, combined)
}

violation contains {
	"code": "EXCEPT_BASE_EXCEPTION",
	"message": "except BaseException catches SystemExit/KeyboardInterrupt; almost always wrong outside top-level.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)except\s+BaseException\b`, combined)
}

violation contains {
	"code": "OS_CHDIR_IN_APP",
	"message": "os.chdir changes process-global CWD and breaks threaded servers; avoid in app code.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	not regex.match(`(?i)(^|/)tests?(/|$)`, path)
	not regex.match(`(?i)(^|/)scripts(/|$)`, path)
	content := files[path]
	contains(content, "os.chdir(")
}

violation contains {
	"code": "UMASK_ZERO_OR_PERMISSIVE",
	"message": "umask(0) or overly permissive umask weakens filesystem ACL expectations.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*umask\s*\(\s*0\s*\)`, combined)
}

violation contains {
	"code": "PARAMIKO_AUTO_ADD_POLICY",
	"message": "paramiko AutoAddPolicy disables host-key verification (MITM risk); use known_hosts or explicit keys.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "AutoAddPolicy")
}

violation contains {
	"code": "HARDCODED_COMMON_PASSWORD",
	"message": "Trivial hardcoded password strings are never acceptable.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*(password|passwd)\s*=\s*["'](password|123456|admin|secret|qwerty|letmein|changeme)["']`, combined)
}

violation contains {
	"code": "LONG_SECRET_LITERAL",
	"message": "Long alphanumeric secret/api key literals belong in secret managers, not source.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*(api[_-]?key|secret[_-]?key|access[_-]?token)\s*=\s*["'][A-Za-z0-9_\-]{32,}["']`, combined)
}

violation contains {
	"code": "FLASK_RUN_ALL_INTERFACES",
	"message": "Binding Flask/Werkzeug to 0.0.0.0 exposes dev servers broadly; restrict host in production.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*\.run\s*\([^)]*host\s*=\s*["']0\.0\.0\.0["']`, combined)
}

violation contains {
	"code": "DJANGO_ALLOWED_HOSTS_WILDCARD",
	"message": "ALLOWED_HOSTS with * disables Host header protection.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*ALLOWED_HOSTS\s*=\s*\[[^\]]*['\"]\*['\"]`, combined)
}

violation contains {
	"code": "PASSWORD_IN_LOG_MESSAGE",
	"message": "Logging statements that mention password/secret risk leaking credentials to aggregators.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*\.(info|debug|warning|error|exception|critical)\s*\([^)]*(password|passwd|secret|api[_-]?key)\s*[:=]`, combined)
}

violation contains {
	"code": "DJANGO_RAW_SQL_FORMAT",
	"message": "extra(raw=...) or RawSQL with format/percent interpolation is SQL injection prone.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*(RawSQL|extra)\s*\([^)]*%`, combined)
}

violation contains {
	"code": "DJANGO_EXTRA_RAW_UNSAFE",
	"message": "Avoid constructing raw SQL fragments from user input in .extra().",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.extra\s*\([^)]*request\.`, combined)
}

violation contains {
	"code": "FLASK_ENDPOINT_STRING_FORMAT",
	"message": "url_for/redirect with format % or f-string from user input can forge endpoints.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*(url_for|redirect)\s*\(\s*f["']`, combined)
}

violation contains {
	"code": "REQUEST_BINDING_TO_SHELL",
	"message": "Passing request values into shell=True or os.system is command injection.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "shell=True")
	contains(combined, "request.")
}

violation contains {
	"code": "OS_SYSTEM_WITH_REQUEST",
	"message": "os.system with request-derived strings is command injection.",
	"path": "",
	"severity": "error",
} if {
	contains(combined, "os.system(")
	contains(combined, "request.")
}

# -----------------------------------------------------------------------------
# Extended frontend / browser sinks
# -----------------------------------------------------------------------------

violation contains {
	"code": "JS_FUNCTION_CONSTRUCTOR",
	"message": "new Function() is eval-equivalent; never use with remote or user-controlled strings.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*new\s+Function\s*\(`, combined)
}

violation contains {
	"code": "JS_SET_TIMEOUT_STRING",
	"message": "setTimeout/setInterval with string code is implicit eval.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*set(Timeout|Interval)\s*\(\s*["']`, combined)
}

violation contains {
	"code": "WINDOW_POST_MESSAGE_WILDCARD",
	"message": "postMessage targetOrigin * leaks messages to any opener/frame; pass explicit origins.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*postMessage\s*\([^,]+,\s*["']\*["']`, combined)
}

violation contains {
	"code": "DOCUMENT_COOKIE_WRITE",
	"message": "Writing document.cookie from JS needs tight scoping; easy to leak session material.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*document\.cookie\s*=`, combined)
}

violation contains {
	"code": "DOM_OUTER_HTML_ASSIGN",
	"message": "outerHTML assignment is an HTML injection sink like innerHTML.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.outerHTML\s*=`, combined)
}

violation contains {
	"code": "DOM_INSERT_ADJACENT_HTML",
	"message": "insertAdjacentHTML parses HTML from strings; sanitize or avoid with untrusted data.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*insertAdjacentHTML\s*\(`, combined)
}

violation contains {
	"code": "LOCALSTORAGE_SECRET_KEY",
	"message": "Storing tokens/passwords in localStorage is readable by any XSS; prefer httpOnly cookies or secure memory patterns.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*localStorage\.setItem\s*\(\s*["'][^"']*(token|password|secret|jwt|refresh)[^"']*["']`, combined)
}

violation contains {
	"code": "SESSIONSTORAGE_SECRET_KEY",
	"message": "sessionStorage for credentials is XSS-readable; prefer hardened cookie/session patterns.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*sessionStorage\.setItem\s*\(\s*["'][^"']*(token|password|secret|jwt)[^"']*["']`, combined)
}

violation contains {
	"code": "JS_LOOSE_NULL_CHECK",
	"message": "== null / == undefined conflates null and undefined; use === or explicit checks.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*==\s*null\b`, combined)
}

violation contains {
	"code": "JS_LOOSE_UNDEFINED_CHECK",
	"message": "Loose equality with undefined is brittle; prefer typeof or ===.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*==\s*undefined\b`, combined)
}

violation contains {
	"code": "JS_VOID_ZERO_PATTERN",
	"message": "void 0 checks are archaic; prefer undefined or optional chaining.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*void\s+0\b`, combined)
}

violation contains {
	"code": "PROMISE_CATCH_SWALLOW",
	"message": "Empty or logging-only catch blocks hide failures; handle, rethrow, or surface to users.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*\.catch\s*\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)`, combined)
}

violation contains {
	"code": "FETCH_CREDENTIALS_OMIT_INSECURE",
	"message": "fetch credentials omit combined with cross-origin calls can confuse cookie/session models; document intent.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*fetch\s*\([^)]*credentials\s*:\s*["']omit["']`, combined)
}

# -----------------------------------------------------------------------------
# Extended Python portability / legacy / smells
# -----------------------------------------------------------------------------

violation contains {
	"code": "PYTHON2_PRINT_STATEMENT",
	"message": "Python 2 print statement is invalid in Python 3.",
	"path": path,
	"severity": "error",
} if {
	some path in changed
	regex.match(`.*\.py$`, path)
	regex.match(`(?m)^\s*print\s+[^(][^\n]*$`, files[path])
}

violation contains {
	"code": "PYTHON2_EXCEPT_COMMA",
	"message": "except Exception, e syntax is Python 2; use as.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)except\s+[^:]+:\s*[^\n]+,\s*\w+\s*:`, combined)
}

violation contains {
	"code": "PYTHON2_ITERITEMS",
	"message": ".iteritems/.iterkeys/.itervalues are Python 2; use .items() etc.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.(iteritems|iterkeys|itervalues)\s*\(`, combined)
}

violation contains {
	"code": "PYTHON2_HAS_KEY",
	"message": "dict.has_key is Python 2; use in.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\.has_key\s*\(`, combined)
}

violation contains {
	"code": "PYTHON2_UNICODE_BUILTIN",
	"message": "unicode(...) builtin is Python 2; use str in Python 3.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)(^|[^\w.])unicode\s*\(`, combined)
}

violation contains {
	"code": "PYTHON2_BASESTRING",
	"message": "basestring is Python 2 only.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)(^|[^\w.])basestring\b`, combined)
}

violation contains {
	"code": "PYTHON2_XRANGE",
	"message": "xrange is Python 2; use range.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)(^|[^\w.])xrange\s*\(`, combined)
}

violation contains {
	"code": "PYTHON2_RAW_INPUT",
	"message": "raw_input is Python 2; use input() in Python 3 (still avoid in servers).",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)(^|[^\w.])raw_input\s*\(`, combined)
}

violation contains {
	"code": "PYTHON2_APPLY_EXECFILE",
	"message": "apply/execfile are Python 2; refactor for Python 3.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?m)(^|[^\w.])(apply|execfile)\s*\(`, combined)
}

violation contains {
	"code": "PYTHON2_LONG_SUFFIX",
	"message": "123L long literal suffix is Python 2.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*\b[0-9]+L\b`, combined)
}

violation contains {
	"code": "PYTHON2_OLD_OCTAL_LITERAL",
	"message": "Old-style octal literals (0644) are invalid in Python 3.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[^\w]0[0-7]{3,}\b`, combined)
}

violation contains {
	"code": "RANGE_LEN_ANTIPATTERN",
	"message": "range(len(x)) is usually wrong; iterate the sequence or use enumerate().",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*range\s*\(\s*len\s*\(`, combined)
}

violation contains {
	"code": "DICT_KEYS_IN_FOR_LOOP",
	"message": "for k in d.keys() is redundant in Python 3; iterate d directly.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*for\s+\w+\s+in\s+\w+\.keys\s*\(\s*\)\s*:`, combined)
}

violation contains {
	"code": "IS_TRUE_OR_FALSE_LITERAL",
	"message": "Never compare or test with is True / is False; use truthiness or is / is not with None only.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*\bis\s+(True|False)\b`, combined)
}

violation contains {
	"code": "STRINGIFY_EXCEPTION",
	"message": "str(exc) loses traceback context; log with exc_info=True or raise from.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*(str|unicode)\s*\(\s*\w+\s*\)\s*.*except`, combined)
}

violation contains {
	"code": "TRY_EXCEPT_IMPORT_ERROR_PASS",
	"message": "except ImportError: pass hides optional dependency mistakes; narrow or re-raise.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)except\s+ImportError\s*:\s*\n\s*pass\b`, combined)
}

violation contains {
	"code": "LBYL_FILE_EXISTS",
	"message": "os.path.exists before open is TOCTOU; prefer open try/except or pathlib exists for UI only.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*os\.path\.exists\s*\([^)]+\)[\s\S]{0,200}open\s*\(`, combined)
}

violation contains {
	"code": "THREADING_THREAD_DAEMON_TRUE",
	"message": "daemon threads die abruptly on shutdown; avoid for work that must flush IO.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*Thread\s*\([^)]*daemon\s*=\s*True`, combined)
}

violation contains {
	"code": "DATACLASS_UNSAFE_HASH",
	"message": "dataclass unsafe_hash=True with mutable fields is a foot-gun for dict/set keys.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*@dataclass\s*\([^)]*unsafe_hash\s*=\s*True`, combined)
}

violation contains {
	"code": "FLASK_SECRET_KEY_LITERAL",
	"message": "Flask secret_key must come from environment or secret store in production.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*secret_key\s*=\s*["'][^"']{8,}["']`, combined)
	not regex.match(`[\s\S]*environ`, combined)
}

violation contains {
	"code": "DJANGO_SECRET_KEY_INLINE",
	"message": "SECRET_KEY should not be a long inline string in committed settings.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*SECRET_KEY\s*=\s*["'][^"']{20,}["']`, combined)
	not regex.match(`(?i)[\s\S]*os\.environ`, combined)
}

violation contains {
	"code": "GUNICORN_WORKERS_ONE",
	"message": "gunicorn workers=1 defeats horizontal scaling hints; document if intentional for dev.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*gunicorn[^\n]*-w\s*1\b`, combined)
}

violation contains {
	"code": "UVICORN_RELOAD_PRODUCTION",
	"message": "uvicorn --reload is for development only.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`[\s\S]*uvicorn[^\n]*--reload`, combined)
}

violation contains {
	"code": "DOCKER_RUN_PRIVILEGED",
	"message": "docker --privileged removes container isolation; avoid in production images.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*docker\s+run[^\n]*--privileged`, combined)
}

violation contains {
	"code": "KUBECTL_UNSAFE_ADMIN",
	"message": "kubectl commands with cluster-admin or wildcard RBAC are high risk in automation.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?i)[\s\S]*kubectl[^\n]*(cluster-admin|clusterrolebinding)`, combined)
}

violation contains {
	"code": "CHMOD_ON_SECRET_FILE",
	"message": "chmod on key/credential paths in app code is suspicious; prefer umask and package perms.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?i)[\s\S]*chmod\s*\([^)]*(id_rsa|\.pem|credential|secret)`, combined)
}

violation contains {
	"code": "ENVIRON_MUTATION",
	"message": "Mutating os.environ at runtime affects the whole process; prefer contextvars or explicit config.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*os\.environ\[[^\]]+\]\s*=`, combined)
}

violation contains {
	"code": "SYS_PATH_APPEND_RUNTIME",
	"message": "sys.path.insert/append at import/runtime hides packaging problems; use proper installs.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*sys\.path\.(insert|append)\s*\(`, combined)
}

violation contains {
	"code": "MOCK_PATCH_UNQUALIFIED",
	"message": "patch('module.name') string targets are brittle; prefer patch.object or import-and-patch.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`[\s\S]*@patch\s*\(\s*["'][^"']+["']`, combined)
}

# -----------------------------------------------------------------------------
# Flask / Jinja / HTML — common blog and app gaps (needs path context; use --scan-prefix)
# -----------------------------------------------------------------------------

violation contains {
	"code": "HTML_FORM_POST_MISSING_CSRF",
	"message": "POST forms must include CSRF tokens (Flask-WTF csrf_token(), SameSite cookies are not enough).",
	"path": path,
	"severity": "error",
} if {
	some path in changed
	regex.match(`(?i).*\.html$`, path)
	content := files[path]
	regex.match(`(?i)<form[^>]*\bmethod\s*=\s*["']post["']`, content)
	not regex.match(`(?i)csrf`, content)
}

violation contains {
	"code": "FLASK_SECRET_KEY_ENV_FALLBACK_LITERAL",
	"message": "Do not ship non-empty SECRET_KEY fallbacks in code; require env and fail closed in production.",
	"path": "",
	"severity": "error",
} if {
	regex.match(`(?i)[\s\S]*SECRET_KEY[\s\S]{0,320}environ\.get\s*\(\s*["'][^"']+["']\s*,\s*["'][^"']{6,}["']`, combined)
}

violation contains {
	"code": "FLASK_SQLALCHEMY_SQLITE_LITERAL",
	"message": "Defaulting SQLALCHEMY_DATABASE_URI to sqlite:/// in source ties deployments to local DB; use env-only DSN.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?i)[\s\S]*SQLALCHEMY_DATABASE_URI[\s\S]{0,400}sqlite://`, combined)
}

violation contains {
	"code": "FLASK_SESSION_COOKIE_SECURE_UNSET",
	"message": "Set SESSION_COOKIE_SECURE=True when serving over HTTPS (explicit in config).",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i).*\.py$`, path)
	content := files[path]
	contains(content, "Flask(")
	not regex.match(`(?i)[\s\S]*SESSION_COOKIE_SECURE\s*=\s*True`, content)
}

violation contains {
	"code": "BLUEPRINT_POST_NO_WTF_IMPORT",
	"message": "Blueprint defines POST routes using request.form but project shows no Flask-WTF/CSRF import in changed files.",
	"path": "",
	"severity": "warning",
} if {
	regex.match(`(?m)@\w+\.route\([^)]*methods\s*=\s*\[[^\]]*["']POST["']`, combined)
	contains(combined, "request.form")
	not regex.match(`(?i)[\s\S]*(flask_wtf|wtforms|csrf|CSRFProtect)`, combined)
}

violation contains {
	"code": "ROUTE_FILE_NAMED_ROUTES_PY",
	"message": "routes.py at app root often mixes HTTP and persistence; keep routes thin and delegate to services.",
	"path": path,
	"severity": "warning",
} if {
	some path in changed
	regex.match(`(?i)(^|/)routes\.py$`, path)
	content := files[path]
	contains(content, "@")
	contains(content, "route(")
	strings.count(content, "\n") > 80
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
	"message": "Very large modules are hard to review and violate single-responsibility; split by feature (target under ~400 lines per module).",
	"path": path,
	"severity": "error",
} if {
	some path in changed
	regex.match(`(?i).*\.(py|ts|tsx|js|jsx)$`, path)
	content := files[path]
	strings.count(content, "\n") > 400
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
	"severity": "error",
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
	"message": "TODO/FIXME/HACK/XXX in changed code must be tracked or removed before merge.",
	"path": "",
	"severity": "error",
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
