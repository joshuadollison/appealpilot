"""Model C (appeal packet generator) powered by aisuite.

This module keeps provider/model selection configurable so we can switch between
OpenAI and Groq models without changing business logic.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

DEFAULT_SETTINGS_PATH = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"

DEFAULT_SYSTEM_PROMPT = (
    "You are AppealPilot, an insurance denial appeal copilot. "
    "Use only user-provided case facts and retrieved evidence. "
    "Do not invent facts. "
    "Return valid JSON only with keys: "
    "cover_letter, detailed_justification, evidence_checklist, "
    "missing_information, citations."
)

_JSON_CODE_BLOCK = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
DEFAULT_PASSTHROUGH_SYSTEM_PROMPT = "You are a concise assistant."


class ModelCConfigurationError(ValueError):
    """Raised when model configuration is invalid."""


class ModelCResponseError(RuntimeError):
    """Raised when the model response is missing or malformed."""


@dataclass(frozen=True)
class ModelCConfig:
    """Runtime configuration for the Model C generator."""

    model: str = "openai:gpt-5-mini"
    temperature: float = 0.2
    max_tokens: int = 1600
    top_p: float = 1.0

    @property
    def provider(self) -> str:
        return self.model.split(":", maxsplit=1)[0]

    def validate(self) -> None:
        if ":" not in self.model:
            raise ModelCConfigurationError(
                "Model C model must be 'provider:model_name' (e.g., openai:gpt-5-mini)."
            )
        if self.max_tokens < 1:
            raise ModelCConfigurationError("Model C max_tokens must be >= 1.")
        if not 0 <= self.temperature <= 2:
            raise ModelCConfigurationError("Model C temperature must be in [0, 2].")
        if not 0 <= self.top_p <= 1:
            raise ModelCConfigurationError("Model C top_p must be in [0, 1].")


def _to_float(value: Any, fallback: float) -> float:
    if value is None or value == "":
        return fallback
    return float(value)


def _to_int(value: Any, fallback: int) -> int:
    if value is None or value == "":
        return fallback
    return int(value)


def _load_model_c_from_settings(settings_path: Path) -> dict[str, Any]:
    if not settings_path.exists():
        return {}

    try:
        import yaml
    except ImportError as exc:
        raise ModelCConfigurationError(
            "PyYAML is required to read settings.yaml. Install with `pip install PyYAML`."
        ) from exc

    loaded = yaml.safe_load(settings_path.read_text()) or {}
    if not isinstance(loaded, dict):
        return {}

    model_c = loaded.get("model_c", {})
    if not isinstance(model_c, dict):
        raise ModelCConfigurationError("`model_c` in settings.yaml must be a mapping.")
    return model_c


def build_model_c_config(
    settings_path: Path = DEFAULT_SETTINGS_PATH,
    overrides: Mapping[str, Any] | None = None,
) -> ModelCConfig:
    """Build config from settings.yaml + env vars + explicit overrides."""

    base = _load_model_c_from_settings(settings_path)
    if overrides:
        base = {**base, **dict(overrides)}

    model = os.getenv("MODEL_C_MODEL", base.get("model", "openai:gpt-5-mini"))
    temperature = _to_float(
        os.getenv("MODEL_C_TEMPERATURE", base.get("temperature")), 0.2
    )
    max_tokens = _to_int(os.getenv("MODEL_C_MAX_TOKENS", base.get("max_tokens")), 1600)
    top_p = _to_float(os.getenv("MODEL_C_TOP_P", base.get("top_p")), 1.0)

    config = ModelCConfig(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
    )
    config.validate()
    return config


def _default_aisuite_client() -> Any:
    try:
        import aisuite as ai
    except ImportError as exc:
        raise RuntimeError(
            "aisuite is required. Install with `pip install \"aisuite[openai,groq]\"`."
        ) from exc

    provider_configs: dict[str, dict[str, str]] = {}
    if os.getenv("OPENAI_API_KEY"):
        provider_configs["openai"] = {"api_key": os.environ["OPENAI_API_KEY"]}
    if os.getenv("GROQ_API_KEY"):
        provider_configs["groq"] = {"api_key": os.environ["GROQ_API_KEY"]}

    if provider_configs:
        return ai.Client(provider_configs=provider_configs)
    return ai.Client()


def _strip_code_fence(text: str) -> str:
    match = _JSON_CODE_BLOCK.match(text.strip())
    if match:
        return match.group(1).strip()
    return text.strip()


def _coerce_text_payload(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, Mapping):
        for key in ("text", "content", "value", "output_text", "refusal"):
            if key in value:
                candidate = _coerce_text_payload(value.get(key))
                if candidate:
                    return candidate
        return ""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        parts = [_coerce_text_payload(item) for item in value]
        joined = "\n".join(part for part in parts if part)
        return joined.strip()

    for attr in ("text", "content", "value", "output_text", "refusal"):
        if hasattr(value, attr):
            candidate = _coerce_text_payload(getattr(value, attr))
            if candidate:
                return candidate
    return ""


def _extract_text_content(response: Any) -> str:
    try:
        message = response.choices[0].message
    except Exception as exc:
        raise ModelCResponseError("Could not read content from model response.") from exc

    content = _coerce_text_payload(getattr(message, "content", None))
    if content:
        return content

    # Some providers expose fallback fields when content is empty.
    fallback = _coerce_text_payload(message)
    if fallback:
        return fallback

    raise ModelCResponseError("Model returned empty content.")


def _usage_as_dict(response: Any) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}

    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def _uses_openai_gpt5_model(model: str) -> bool:
    if ":" not in model:
        return False
    provider, model_name = model.split(":", maxsplit=1)
    return provider.strip().lower() == "openai" and model_name.strip().lower().startswith("gpt-5")


def _build_generation_parameters(config: ModelCConfig) -> dict[str, Any]:
    if _uses_openai_gpt5_model(config.model):
        # OpenAI GPT-5 models currently only support default sampling params.
        return {
            "max_completion_tokens": config.max_tokens,
            "reasoning_effort": "low",
        }

    return {
        "temperature": config.temperature,
        "top_p": config.top_p,
        "max_tokens": config.max_tokens,
    }


def _run_chat_with_retry(
    *,
    client: Any,
    config: ModelCConfig,
    messages: Sequence[Mapping[str, str]],
) -> tuple[Any, str]:
    params = _build_generation_parameters(config)
    response = client.chat.completions.create(
        model=config.model,
        messages=list(messages),
        **params,
    )

    try:
        return response, _extract_text_content(response)
    except ModelCResponseError as exc:
        # Retry once for GPT-5 if it consumed budget on reasoning and produced no visible text.
        if not _uses_openai_gpt5_model(config.model):
            raise exc

        retry_params = dict(params)
        retry_tokens = int(retry_params.get("max_completion_tokens", config.max_tokens))
        retry_params["max_completion_tokens"] = max(retry_tokens, 2400)
        retry_params["reasoning_effort"] = "low"
        response = client.chat.completions.create(
            model=config.model,
            messages=list(messages),
            **retry_params,
        )
        return response, _extract_text_content(response)


def run_model_c_passthrough(
    prompt: str,
    *,
    model: str | None = None,
    system_prompt: str = DEFAULT_PASSTHROUGH_SYSTEM_PROMPT,
    max_tokens: int | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    client: Any | None = None,
) -> dict[str, Any]:
    """Run a direct prompt against the selected LLM and return raw text + usage."""

    prompt_text = prompt.strip()
    if not prompt_text:
        raise ValueError("Prompt is required.")

    overrides: dict[str, Any] = {}
    if model:
        overrides["model"] = model
    if max_tokens is not None:
        overrides["max_tokens"] = int(max_tokens)
    if temperature is not None:
        overrides["temperature"] = float(temperature)
    if top_p is not None:
        overrides["top_p"] = float(top_p)

    config = build_model_c_config(overrides=overrides or None)
    active_client = client or _default_aisuite_client()
    messages = [
        {"role": "system", "content": (system_prompt or DEFAULT_PASSTHROUGH_SYSTEM_PROMPT).strip()},
        {"role": "user", "content": prompt_text},
    ]
    response, output_text = _run_chat_with_retry(
        client=active_client,
        config=config,
        messages=messages,
    )

    message = response.choices[0].message
    return {
        "provider": config.provider,
        "model": config.model,
        "usage": _usage_as_dict(response),
        "output_text": output_text,
        "message": {
            "content": getattr(message, "content", None),
            "refusal": getattr(message, "refusal", None),
            "reasoning_content": getattr(message, "reasoning_content", None),
        },
    }


class ModelCGenerator:
    """Provider-agnostic Model C wrapper using aisuite."""

    def __init__(
        self,
        config: ModelCConfig | None = None,
        client: Any | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ):
        self.config = config or build_model_c_config()
        self.config.validate()
        self.client = client or _default_aisuite_client()
        self.system_prompt = system_prompt

    def generate(
        self,
        case_summary: Mapping[str, Any],
        retrieved_evidence: Sequence[Mapping[str, Any]],
        required_attachments: Sequence[str] | None = None,
        additional_instructions: str | None = None,
    ) -> dict[str, Any]:
        """Generate a structured appeal packet payload."""

        payload = {
            "task": "Generate an appeal letter packet JSON for the denial case.",
            "output_contract": {
                "cover_letter": "string",
                "detailed_justification": "string",
                "evidence_checklist": [
                    {
                        "item": "string",
                        "status": "present|missing",
                        "notes": "string",
                    }
                ],
                "missing_information": ["string"],
                "citations": [
                    {
                        "claim": "string",
                        "source_id": "string",
                        "source_excerpt": "string",
                    }
                ],
            },
            "grounding_rules": [
                "Use only provided facts and evidence.",
                "If evidence is missing, add it to missing_information.",
                "Every factual claim should map to at least one citation.",
                "Do not include PHI not provided in inputs.",
            ],
            "case_summary": dict(case_summary),
            "retrieved_evidence": list(retrieved_evidence),
            "required_attachments": list(required_attachments or []),
            "additional_instructions": additional_instructions or "",
        }

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
        ]
        response, raw_text = _run_chat_with_retry(
            client=self.client,
            config=self.config,
            messages=messages,
        )

        normalized = _strip_code_fence(raw_text)

        try:
            parsed = json.loads(normalized)
        except json.JSONDecodeError as exc:
            raise ModelCResponseError(
                "Model C did not return valid JSON. "
                "Adjust prompt/model or inspect `raw_text`."
            ) from exc

        if not isinstance(parsed, dict):
            raise ModelCResponseError("Model C output must be a JSON object.")

        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "usage": _usage_as_dict(response),
            "output": parsed,
            "raw_text": raw_text,
        }
