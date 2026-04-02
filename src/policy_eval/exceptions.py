class PolicyEvalError(Exception):
    """Base error for policy evaluation."""


class ManifestError(PolicyEvalError):
    pass


class PatchApplyError(PolicyEvalError):
    pass


class OpaEngineError(PolicyEvalError):
    pass
