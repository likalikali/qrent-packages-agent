import os

import dotenv
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from llama_index.core import StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.settings import Settings
from llama_index.embeddings.dashscope import DashScopeEmbedding

from src.config.path import PATHS
from src.utils.vector_store import build_milvus_vector_store, env_flag

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

if BACKEND == "milvus":
    vector_store = build_milvus_vector_store()
    milvus_client = vector_store.client
    index = None
else:
    persist_dir = PATHS["KNOWLEDGE_BASE_DIR"]
    storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
    index = load_index_from_storage(storage_context)

if index is not None:
    if USE_LLM:
        query_engine = index.as_query_engine(similarity_top_k=similarity_top_k)
        retriever = None
    else:
        query_engine = None
        retriever = index.as_retriever(similarity_top_k=similarity_top_k)
else:
    query_engine = None
    retriever = None


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


def _internal_search(query: str) -> str:
    """
    执行真实的知识库向量检索。

    参数:
        query (str): 自然语言问题
    返回:
        str: 检索结果或错误信息
    """
    try:
        if milvus_client is not None:
            embedding = Settings.embed_model.get_query_embedding(query)
            res = milvus_client.search(
                collection_name=os.getenv("MILVUS_COLLECTION", "qrent_notion"),
                data=[embedding],
                limit=similarity_top_k,
                output_fields=["text", "doc_id"],
                search_params={
                    "metric_type": os.getenv("MILVUS_INDEX_METRIC", "COSINE").upper(),
                    "params": {},
                },
                timeout=milvus_timeout,
                anns_field=os.getenv("MILVUS_EMBEDDING_FIELD", "embedding"),
            )
            if not res or not res[0]:
                return "No relevant results found."
            blocks = []
            for hit in res[0]:
                entity = hit.get("entity") or {}
                text = entity.get("text") or ""
                if text:
                    blocks.append(text.strip())
            if not blocks:
                return "No relevant results found."
            if USE_LLM:
                llm = _build_llm()
                if llm is None:
                    return "LLM is not configured. Set RAG_LLM_PROVIDER and API key."
                context = "\n\n".join(blocks)
                system = "You are the Qrent assistant. Answer using the provided context only."
                user = (
                    "问题：{query}\n\n"
                    "请仅根据以下资料回答，如资料中没有答案请说明未找到。\n\n"
                    "资料：\n{context}"
                ).format(query=query, context=context)
                response = llm.invoke(
                    [SystemMessage(content=system), HumanMessage(content=user)]
                )
                return response.content
            return "\n\n".join(blocks)
        if retriever is not None:
            nodes = retriever.retrieve(query)
            if not nodes:
                return "No relevant results found."
            return "\n\n".join(node.node.get_text().strip() for node in nodes)
        response = query_engine.query(query)
        return str(response)
    except Exception as e:
        return f"Error searching the Qrent KB: {e}"


@tool
def search_qrent_knowledge(query: str) -> str:
    """
    使用运营维护的 Notion + Milvus 知识库检索关键信息。

    参数:
    - query (str): 必填，用户提出的问题。

    返回:
    - str: 最相关的知识库内容。
    """
    return _internal_search(query)
