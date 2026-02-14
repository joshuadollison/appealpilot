from __future__ import annotations

from types import SimpleNamespace

from appealpilot.models.model_c_aisuite import ModelCConfig, ModelCGenerator


class _StubCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content='{"cover_letter":"ok"}')
                )
            ],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        )


class _StubClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=_StubCompletions())


class _StructuredStubCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=[{"type": "output_text", "text": '{"cover_letter":"ok"}'}]
                    )
                )
            ],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        )


class _StructuredStubClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=_StructuredStubCompletions())


def test_gpt5_uses_max_completion_tokens() -> None:
    client = _StubClient()
    generator = ModelCGenerator(
        config=ModelCConfig(model="openai:gpt-5-mini", max_tokens=777),
        client=client,
    )

    generator.generate(case_summary={}, retrieved_evidence=[])
    call = client.chat.completions.calls[0]

    assert call["max_completion_tokens"] == 777
    assert "max_tokens" not in call
    assert "temperature" not in call
    assert "top_p" not in call


def test_non_gpt5_uses_max_tokens() -> None:
    client = _StubClient()
    generator = ModelCGenerator(
        config=ModelCConfig(model="openai:gpt-4o-mini", max_tokens=555),
        client=client,
    )

    generator.generate(case_summary={}, retrieved_evidence=[])
    call = client.chat.completions.calls[0]

    assert call["max_tokens"] == 555
    assert "max_completion_tokens" not in call
    assert call["temperature"] == 0.2
    assert call["top_p"] == 1.0


def test_structured_content_response_is_parsed() -> None:
    client = _StructuredStubClient()
    generator = ModelCGenerator(
        config=ModelCConfig(model="openai:gpt-5-mini", max_tokens=300),
        client=client,
    )

    output = generator.generate(case_summary={}, retrieved_evidence=[])
    assert output["output"]["cover_letter"] == "ok"
