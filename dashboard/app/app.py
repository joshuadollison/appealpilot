"""AppealPilot real-time dashboard (Streamlit)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from appealpilot.config.key_loader import DEFAULT_KEYS_PATH, load_local_keys
from appealpilot.models import build_model_c_config, run_model_c_passthrough
from appealpilot.retrieval import build_retrieval_config, rebuild_retrieval_index
from appealpilot.workflow import run_pipeline_once

DEFAULT_DENIAL_PATH = ROOT_DIR / "docs/examples/denial_sample.txt"
DEFAULT_CHART_NOTES_PATH = ROOT_DIR / "docs/examples/chart_notes_sample.txt"
EMBEDDING_PROVIDER_OPTIONS = ["sbert", "insurance_bert", "hash", "openai"]


def _load_example_text(path: Path) -> str:
    if path.exists():
        return path.read_text()
    return ""


def _render_key_status() -> None:
    status = load_local_keys()
    st.sidebar.subheader("Key Status")
    st.sidebar.caption(f"Local key config: `{DEFAULT_KEYS_PATH}`")
    st.sidebar.write(f"Config file found: `{status['path_exists']}`")
    st.sidebar.write(f"OPENAI_API_KEY loaded: `{status['openai']}`")
    st.sidebar.write(f"GROQ_API_KEY loaded: `{status['groq']}`")
    if st.sidebar.button("Reload Keys from Local Config"):
        status = load_local_keys(override_env=True)
        st.sidebar.success(
            f"Reloaded keys. OPENAI={status['openai']} GROQ={status['groq']}"
        )


def _load_default_embedding_provider() -> str:
    try:
        provider = build_retrieval_config().embedding_provider.strip().lower()
    except Exception:
        provider = "sbert"
    aliases = {
        "local": "sbert",
        "sentence_transformers": "sbert",
        "insurance": "insurance_bert",
        "industry_bert_insurance": "insurance_bert",
    }
    provider = aliases.get(provider, provider)
    if provider not in EMBEDDING_PROVIDER_OPTIONS:
        return "sbert"
    return provider


def _render_rebuild_panel(default_provider: str) -> None:
    st.subheader("Vector Store")
    st.caption("Use this to rebuild/refresh the Chroma collection used for retrieval.")

    col1, col2, col3 = st.columns(3)
    with col1:
        rebuild_limit = st.number_input("Rebuild row limit", min_value=1, value=2000, step=100)
    with col2:
        rebuild_provider = st.selectbox(
            "Embedding provider",
            EMBEDDING_PROVIDER_OPTIONS,
            index=EMBEDDING_PROVIDER_OPTIONS.index(default_provider),
        )
    with col3:
        reset_collection = st.checkbox("Reset collection first", value=True)

    collection_name = st.text_input("Collection name", value="dfs_appeals_cases")
    xlsx_path = st.text_input(
        "DFS XLSX path",
        value="data/raw/dfs_external_appeals/ny_dfs_external_appeals_all_years.xlsx",
    )

    if st.button("Rebuild Vector Store", type="primary"):
        with st.spinner("Rebuilding vector store..."):
            try:
                rebuild_overrides: dict[str, str] = {
                    "embedding_provider": rebuild_provider,
                }
                if collection_name.strip():
                    rebuild_overrides["collection_name"] = collection_name.strip()

                result = rebuild_retrieval_index(
                    xlsx_path=Path(xlsx_path),
                    limit=int(rebuild_limit),
                    reset=reset_collection,
                    overrides=rebuild_overrides,
                )
                st.success("Vector store rebuild complete.")
                st.json(result)
            except Exception as exc:
                st.error(f"Failed to rebuild vector store: {exc}")


def _render_generation_panel(default_provider: str) -> None:
    st.subheader("Generate Appeal Packet")
    st.caption("Run full denial -> classify -> retrieve -> generate workflow in real time.")

    default_denial = _load_example_text(DEFAULT_DENIAL_PATH)
    default_chart_notes = _load_example_text(DEFAULT_CHART_NOTES_PATH)

    denial_text = st.text_area("Denial Text", value=default_denial, height=200)
    chart_notes = st.text_area("Chart Notes", value=default_chart_notes, height=180)

    col1, col2, col3 = st.columns(3)
    with col1:
        top_k = st.number_input("Top K retrieval", min_value=1, max_value=20, value=5)
    with col2:
        generation_runtime = st.selectbox("Generation runtime", ["auto", "template", "aisuite"], index=0)
    with col3:
        query_provider = st.selectbox(
            "Retrieval provider",
            EMBEDDING_PROVIDER_OPTIONS,
            index=EMBEDDING_PROVIDER_OPTIONS.index(default_provider),
        )

    collection_name = st.text_input("Retrieval collection", value="dfs_appeals_cases")
    output_dir = st.text_input("Output directory", value="")

    if st.button("Run Appeal Workflow"):
        if not denial_text.strip():
            st.warning("Denial text is required.")
            return

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        resolved_output_dir = (
            Path(output_dir).expanduser()
            if output_dir.strip()
            else ROOT_DIR / "outputs" / "appeals" / f"dashboard_{timestamp}"
        )

        with st.spinner("Running workflow..."):
            try:
                retrieval_overrides: dict[str, str] = {
                    "embedding_provider": query_provider,
                }
                if collection_name.strip():
                    retrieval_overrides["collection_name"] = collection_name.strip()

                packet, export_dir = run_pipeline_once(
                    denial_text=denial_text,
                    chart_notes=chart_notes,
                    top_k=int(top_k),
                    generation_runtime=generation_runtime,
                    output_dir=resolved_output_dir,
                    retrieval_overrides=retrieval_overrides,
                )
            except Exception as exc:
                st.error(f"Workflow failed: {exc}")
                return

        st.success(f"Workflow complete. Exported to `{export_dir}`")
        st.markdown("### Classification")
        st.json(
            {
                "category": packet.classification.category,
                "confidence": packet.classification.confidence,
                "matched_terms": list(packet.classification.matched_terms),
            }
        )

        st.markdown("### Case Summary")
        st.json(packet.case_summary)

        st.markdown("### Retrieved Evidence")
        evidence_rows: list[dict[str, Any]] = []
        for item in packet.evidence_items:
            evidence_rows.append(
                {
                    "source_id": item.source_id,
                    "distance": item.distance,
                    "metadata": dict(item.metadata),
                    "snippet": item.snippet[:400],
                }
            )
        st.json(evidence_rows)

        generated = packet.generated_output.get("output", {})
        st.markdown("### Generated Appeal Output")
        st.text_area(
            "Cover Letter",
            value=generated.get("cover_letter", ""),
            height=140,
        )
        st.text_area(
            "Detailed Justification",
            value=generated.get("detailed_justification", ""),
            height=220,
        )
        st.markdown("#### Checklist")
        st.json(generated.get("evidence_checklist", []))
        st.markdown("#### Citations")
        st.json(generated.get("citations", []))

        st.markdown("### Exported Files")
        export_paths = sorted(path for path in Path(export_dir).glob("*") if path.is_file())
        exported_files = [str(path.relative_to(ROOT_DIR)) for path in export_paths]
        st.code("\n".join(exported_files))

        artifact_map = {path.name: path for path in export_paths}
        letter_path = artifact_map.get("appeal_letter.md")
        checklist_path = artifact_map.get("evidence_checklist.md")

        if letter_path or checklist_path:
            st.markdown("### Markdown Artifacts")
            markdown_paths = [path for path in (letter_path, checklist_path) if path is not None]
            markdown_tabs = st.tabs([path.name for path in markdown_paths])
            for tab, path in zip(markdown_tabs, markdown_paths):
                with tab:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    st.markdown("#### Rendered")
                    st.markdown(content)
                    st.markdown("#### Raw Markdown")
                    st.code(content, language="markdown")
                    st.download_button(
                        label=f"Download {path.name}",
                        data=content,
                        file_name=path.name,
                        mime="text/markdown",
                        key=f"download_md_{path.stem}",
                    )

        if export_paths:
            st.markdown("### Artifact Explorer")
            explorer_tabs = st.tabs([path.name for path in export_paths])
            for tab, path in zip(explorer_tabs, export_paths):
                with tab:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    if path.suffix.lower() == ".json":
                        try:
                            st.json(json.loads(content))
                        except json.JSONDecodeError:
                            st.code(content, language="json")
                    elif path.suffix.lower() == ".md":
                        st.markdown(content)
                    else:
                        st.text(content)

                    st.download_button(
                        label=f"Download {path.name}",
                        data=content,
                        file_name=path.name,
                        mime="text/plain",
                        key=f"download_artifact_{path.name}",
                    )


def _load_default_model_c_values() -> tuple[str, int, float, float]:
    try:
        config = build_model_c_config()
        return config.model, int(config.max_tokens), float(config.temperature), float(config.top_p)
    except Exception:
        return "openai:gpt-5-mini", 1600, 0.2, 1.0


def _render_llm_passthrough_panel() -> None:
    st.subheader("LLM Pass-Through Test")
    st.caption("Send a direct prompt to your selected model and inspect the raw response.")

    default_model, default_max_tokens, default_temperature, default_top_p = (
        _load_default_model_c_values()
    )

    col1, col2 = st.columns(2)
    with col1:
        model = st.text_input("LLM model (provider:model)", value=default_model)
    with col2:
        max_tokens = st.number_input(
            "Max completion tokens",
            min_value=1,
            value=default_max_tokens,
            step=100,
        )

    col3, col4 = st.columns(2)
    with col3:
        temperature = st.number_input(
            "Temperature (non-GPT-5 models)",
            min_value=0.0,
            max_value=2.0,
            value=default_temperature,
            step=0.1,
            format="%.2f",
        )
    with col4:
        top_p = st.number_input(
            "Top P (non-GPT-5 models)",
            min_value=0.0,
            max_value=1.0,
            value=default_top_p,
            step=0.1,
            format="%.2f",
        )

    system_prompt = st.text_area(
        "System prompt",
        value="You are a concise assistant.",
        height=90,
    )
    prompt = st.text_area(
        "Prompt",
        value="",
        height=160,
        placeholder="Type a simple prompt here and click Run LLM Prompt...",
    )

    if st.button("Run LLM Prompt"):
        if not prompt.strip():
            st.warning("Prompt is required.")
            return

        with st.spinner("Calling model..."):
            try:
                result = run_model_c_passthrough(
                    prompt=prompt,
                    model=model.strip() or None,
                    system_prompt=system_prompt,
                    max_tokens=int(max_tokens),
                    temperature=float(temperature),
                    top_p=float(top_p),
                )
            except Exception as exc:
                st.error(f"LLM pass-through failed: {exc}")
                return

        st.success("LLM response received.")
        st.text_area(
            "Response",
            value=result.get("output_text", ""),
            height=220,
        )
        st.markdown("#### Metadata")
        st.json(
            {
                "provider": result.get("provider"),
                "model": result.get("model"),
                "usage": result.get("usage", {}),
            }
        )
        st.markdown("#### Raw Message")
        st.json(result.get("message", {}))


def main() -> None:
    st.set_page_config(page_title="AppealPilot Dashboard", layout="wide")
    st.title("AppealPilot Dashboard")
    st.caption(
        "Interactive denial appeal workflow: rebuild retrieval index, run pipeline, inspect outputs."
    )

    _render_key_status()
    default_provider = _load_default_embedding_provider()
    _render_rebuild_panel(default_provider=default_provider)
    st.divider()
    _render_generation_panel(default_provider=default_provider)
    st.divider()
    _render_llm_passthrough_panel()


if __name__ == "__main__":
    main()
