"""Foundation slice for the NormaDepo legal documents pipeline."""

from .config import PipelineConfig, apply_cli_overrides, load_pipeline_config

__all__ = [
    "PipelineConfig",
    "apply_cli_overrides",
    "load_pipeline_config",
]
