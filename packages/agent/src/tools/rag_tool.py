import json
import os
from dataclasses import dataclass
from typing import Any, List
from collections.abc import Mapping

import dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.embeddings.dashscope import DashScopeEmbedding

from src.config.path import PATHS
from src.utils.vector_store import build_milvus_vector_store

dotenv.load_dotenv()

API_KEY = os.getenv("BAILIAN_API_KEY")
if not API_KEY:
    raise ValueError("BAILIAN_API_KEY is missing. Please update your .env file.")

request_timeout = os.getenv("DASHSCOPE_REQUEST_TIMEOUT", "").strip()
embed_kwargs = {}
if request_timeout:
    embed_kwargs["request_timeout"] = float(request_timeout)

Settings.embed_model = DashScopeEmbedding(
    model_name="text-embedding-v2",
    api_key=API_KEY,
    **embed_kwargs,
)

BACKEND = os.getenv("KNOWLEDGE_BACKEND", "milvus").lower()
USE_LLM = os.getenv("RAG_USE_LLM", "true").lower()
LLM_PROVIDER = os.getenv("RAG_LLM_PROVIDER", "").strip().lower()
LLM_MODEL = os.getenv("RAG_LLM_MODEL", "").strip()
LLM_TIMEOUT = os.getenv("RAG_LLM_TIMEOUT", "").strip()
LLM_TIMEOUT = float(LLM_TIMEOUT) if LLM_TIMEOUT else None

milvus_client = None
similarity_top_k = int(os.getenv("RAG_TOP_K", "3"))
milvus_timeout = os.getenv("MILVUS_TIMEOUT", "").strip()
milvus_timeout = float(milvus_timeout) if milvus_timeout else None
chunk_max_chars = int(os.getenv("RAG_CHUNK_MAX_CHARS", "800"))

if BACKEND == "milvus":
    vector_store = build_milvus_vector_store()
    milvus_client = vector_store.client
    index = None
else:
    persist_dir = PATHS["KNOWLEDGE_BASE_DIR"]
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    index = load_index_from_storage(storage_context)

if index is not None:
    retriever = index.as_retriever(similarity_top_k=similarity_top_k)
else:
    retriever = None


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    title: str
    url: str


def _build_llm() -> ChatOpenAI | None:
    provider = LLM_PROVIDER
    if not provider:
        if os.getenv("DEEPSEEK_API_KEY"):
            provider = "deepseek"
        elif os.getenv("OPENAI_API_KEY"):
            provider = "openai"

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            return None
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        model = LLM_MODEL or "deepseek-chat"
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
            request_timeout=LLM_TIMEOUT,
        )

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None
        model = LLM_MODEL or "gpt-4o-mini"
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.2,
            request_timeout=LLM_TIMEOUT,
        )

    return None


def _normalize_text(text: str) -> str:
    return " ".join(text.split()).strip()


def _truncate(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _safe_metadata(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            mapped = value.to_dict()
            if isinstance(mapped, Mapping):
                return dict(mapped)
        except Exception:
            pass
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _extract_title_from_text(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return ""


def _get_hit_field(hit: Any, key: str) -> Any:
    if isinstance(hit, dict):
        if key in hit:
            return hit.get(key)
        entity = hit.get("entity") or {}
        if isinstance(entity, dict):
            return entity.get(key)
        if hasattr(entity, "get"):
            try:
                return entity.get(key)
            except Exception:
                return None
        return None
    if hasattr(hit, "get"):
        try:
            return hit.get(key)
        except Exception:
            pass
    entity = getattr(hit, "entity", None)
    if isinstance(entity, dict):
        return entity.get(key)
    if hasattr(entity, "get"):
        try:
            return entity.get(key)
        except Exception:
            return None
    if hasattr(entity, key):
        return getattr(entity, key)
    if hasattr(hit, key):
        return getattr(hit, key)
    return None


def _build_chunks(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    seen: set[str] = set()
    deduped: List[RetrievedChunk] = []
    for chunk in chunks:
        normalized = _normalize_text(chunk.text)
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(chunk)
    return deduped


def _merge_chunks_by_source(chunks: List[RetrievedChunk]) -> List[RetrievedChunk]:
    merged: List[RetrievedChunk] = []
    grouped: dict[tuple[str, str], List[str]] = {}
    order: List[tuple[str, str]] = []
    for chunk in chunks:
        key = (chunk.title, chunk.url)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        normalized = _normalize_text(chunk.text)
        if not normalized:
            continue
        if normalized in grouped[key]:
            continue
        grouped[key].append(normalized)

    for key in order:
        combined = ""
        for text in grouped[key]:
            candidate = text if not combined else f"{combined}\n{text}"
            if len(candidate) <= chunk_max_chars:
                combined = candidate
                continue
            remaining = chunk_max_chars - len(combined)
            if remaining > 4:
                snippet = text[: remaining - 3].rstrip() + "..."
                combined = snippet if not combined else f"{combined}\n{snippet}"
            elif not combined:
                combined = text[: max(0, chunk_max_chars - 3)].rstrip() + "..."
            break
        merged.append(
            RetrievedChunk(
                text=combined,
                title=key[0],
                url=key[1],
            )
        )
    return merged


def _retrieve_from_milvus(query: str) -> List[RetrievedChunk]:
    if milvus_client is None:
        return []
    embedding = Settings.embed_model.get_query_embedding(query)
    res = milvus_client.search(
        collection_name=os.getenv("MILVUS_COLLECTION", "qrent_notion"),
        data=[embedding],
        limit=similarity_top_k,
        output_fields=["text", "doc_id", "metadata", "title", "url", "_node_content"],
        search_params={
            "metric_type": os.getenv("MILVUS_INDEX_METRIC", "COSINE").upper(),
            "params": {},
        },
        timeout=milvus_timeout,
        anns_field=os.getenv("MILVUS_EMBEDDING_FIELD", "embedding"),
    )


    if not res or not res[0]:
        return []
    raw_chunks: List[RetrievedChunk] = []
    for hit in res[0]:
        text = _get_hit_field(hit, "text")
        metadata_value = _get_hit_field(hit, "metadata")
        title_value = _get_hit_field(hit, "title")
        url_value = _get_hit_field(hit, "url")
        node_content_value = _get_hit_field(hit, "_node_content")
        text = (text or "").strip()
        if not text:
            continue
        metadata = _safe_metadata(metadata_value or {})
        node_content = _safe_metadata(node_content_value)
        node_metadata = _safe_metadata(node_content.get("metadata"))
        title = (
            title_value
            or metadata.get("title")
            or node_metadata.get("title")
            or _extract_title_from_text(text)
            or "未提供标题"
        )
        url = (
            url_value
            or metadata.get("url")
            or node_metadata.get("url")
            or "未提供URL"
        )
        raw_chunks.append(
            RetrievedChunk(
                text=_truncate(text, chunk_max_chars),
                title=title,
                url=url,
            )
        )
    return _build_chunks(raw_chunks)


def _retrieve_from_local(query: str) -> List[RetrievedChunk]:
    if retriever is None:
        return []
    nodes = retriever.retrieve(query)
    if not nodes:
        return []
    raw_chunks: List[RetrievedChunk] = []
    for node in nodes:
        node_obj = node.node
        text = (node_obj.get_text() or "").strip()
        if not text:
            continue
        metadata = _safe_metadata(getattr(node_obj, "metadata", None) or {})
        title = metadata.get("title") or _extract_title_from_text(text) or "未提供标题"
        url = metadata.get("url") or "未提供URL"
        raw_chunks.append(
            RetrievedChunk(
                text=_truncate(text, chunk_max_chars),
                title=title,
                url=url,
            )
        )
    return _build_chunks(raw_chunks)


def _format_sources(chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return "无"
    blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        blocks.append(
            "[{idx}] 标题: {title}\nURL: {url}\n内容: {text}".format(
                idx=idx, title=chunk.title, url=chunk.url, text=chunk.text
            )
        )
    return "\n\n".join(blocks)


def _format_references(chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return "参考文献:\n无"
    lines = ["参考文献:"]
    for idx, chunk in enumerate(chunks, start=1):
        lines.append(f"[{idx}] {chunk.title} - {chunk.url}")
    return "\n".join(lines)


def _answer_with_citations(query: str, chunks: List[RetrievedChunk]) -> str:
    chunks = _merge_chunks_by_source(chunks)
    if USE_LLM != "true":
        return "必须启用 LLM，请设置 RAG_USE_LLM=true。"
    llm = _build_llm()
    if llm is None:
        return "LLM 未配置，请设置 RAG_LLM_PROVIDER 并提供 API Key。"
    sources = _format_sources(chunks)
    system = "你是Qrent助手。只能使用提供的资料回答问题。"
    user = (
        "问题：{query}\n\n"
        "请仅根据资料回答，并在相关语句末尾添加脚注标记 [1]/[2]/[3]...\n"
        "脚注编号必须与资料编号对应，禁止使用 [n] 或其他占位符。\n"
        "如果资料中没有答案，请直接说明未找到。\n"
        "仅输出正文，不要输出参考文献列表。\n\n"
        "资料：\n{sources}"
    ).format(query=query, sources=sources)
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
    answer = str(response.content or "").strip()
    references = _format_references(chunks)
    if not answer:
        answer = "未找到相关答案。"
    return f"{answer}\n\n{references}"


def _internal_search(query: str) -> str:
    """
    执行真实的知识库向量检索。

    参数:
        query (str): 自然语言问题
    返回:
        str: 检索结果或错误信息
    """
    try:
        chunks: List[RetrievedChunk] = []
        if milvus_client is not None:
            chunks = _retrieve_from_milvus(query)
        elif retriever is not None:
            chunks = _retrieve_from_local(query)
        else:
            return "RAG 后端未配置。"
        return _answer_with_citations(query, chunks)
    except Exception as e:
        return f"检索知识库失败: {e}"


@tool
def search_qrent_knowledge(query: str) -> str:
    """
    使用运营维护的 Notion + Milvus 知识库检索并生成带引用的回答。

    参数:
    - query (str): 必填，用户提出的问题。

    返回:
    - str: 带脚注与参考文献的回答。
    """
    return _internal_search(query)
