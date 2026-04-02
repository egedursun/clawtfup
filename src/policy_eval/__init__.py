"""OPA-backed policy evaluation for workspace + patch (LLM grounding layer)."""

from .evaluate import EvaluateOptions, evaluate, opa_bundle_dir

__all__ = ["evaluate", "EvaluateOptions", "opa_bundle_dir"]
