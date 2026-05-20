from __future__ import annotations
import logging
import onnxruntime as ort

logger = logging.getLogger(__name__)

AVAILABLE_PROVIDERS = [
    "CUDAExecutionProvider",
    "DmlExecutionProvider",
    "OpenVINOExecutionProvider",
    "CPUExecutionProvider",
]


def select_providers() -> list[str]:
    """Return ordered list of EPs actually available on this machine, ending with CPU."""
    runtime_available = set(ort.get_available_providers())
    selected = [p for p in AVAILABLE_PROVIDERS if p in runtime_available]
    if "CPUExecutionProvider" not in selected:
        selected.append("CPUExecutionProvider")
    logger.info("Selected ONNX providers: %s", selected)
    return selected
