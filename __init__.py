"""LoopScope: a proof-carrying restricted-case infinite-loop analyser."""
from .analyzer import analyze, AnalysisResult
from .language import compile_source, LanguageError

__all__ = ["analyze", "AnalysisResult", "compile_source", "LanguageError"]
__version__ = "1.0.0"
