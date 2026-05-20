from backend.ep_selector import select_providers, AVAILABLE_PROVIDERS

def test_returns_at_least_cpu():
    providers = select_providers()
    assert "CPUExecutionProvider" in providers

def test_priority_order():
    providers = AVAILABLE_PROVIDERS
    cuda_idx = providers.index("CUDAExecutionProvider") if "CUDAExecutionProvider" in providers else 999
    dml_idx = providers.index("DmlExecutionProvider") if "DmlExecutionProvider" in providers else 999
    cpu_idx = providers.index("CPUExecutionProvider")
    assert cuda_idx < cpu_idx
    assert dml_idx < cpu_idx
