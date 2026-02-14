from __future__ import annotations

from types import SimpleNamespace

import pytest

from appealpilot.models.model_c_aisuite import (
    ModelCConfig,
    ModelCGenerator,
    run_model_c_passthrough,
)


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


class _RetryStubCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self._call_count = 0

    def create(self, **kwargs):
        self.calls.append(kwargs)
        self._call_count += 1
        if self._call_count == 1:
            content = ""
            finish_reason = "length"
        else:
            content = '{"cover_letter":"ok"}'
            finish_reason = "stop"
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason=finish_reason,
                    message=SimpleNamespace(content=content),
                )
            ],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        )


class _RetryStubClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=_RetryStubCompletions())


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
    assert call["reasoning_effort"] == "low"


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


def test_gpt5_retries_once_when_first_response_is_empty() -> None:
    client = _RetryStubClient()
    generator = ModelCGenerator(
        config=ModelCConfig(model="openai:gpt-5-mini", max_tokens=300),
        client=client,
    )

    output = generator.generate(case_summary={}, retrieved_evidence=[])
    assert output["output"]["cover_letter"] == "ok"
    assert len(client.chat.completions.calls) == 2
    assert client.chat.completions.calls[0]["max_completion_tokens"] == 300
    assert client.chat.completions.calls[1]["max_completion_tokens"] == 2400


def test_passthrough_returns_text_and_usage() -> None:
    client = _StubClient()
    result = run_model_c_passthrough(
        prompt="Return JSON",
        model="openai:gpt-4o-mini",
        system_prompt="You are a test assistant.",
        max_tokens=123,
        temperature=0.4,
        top_p=0.8,
        client=client,
    )

    call = client.chat.completions.calls[0]
    assert call["model"] == "openai:gpt-4o-mini"
    assert call["max_tokens"] == 123
    assert call["temperature"] == 0.4
    assert call["top_p"] == 0.8
    assert result["output_text"] == '{"cover_letter":"ok"}'
    assert result["usage"]["total_tokens"] == 2


def test_passthrough_requires_prompt() -> None:
    with pytest.raises(ValueError):
        run_model_c_passthrough(
            prompt="   ",
            model="openai:gpt-4o-mini",
            client=_StubClient(),
        )
