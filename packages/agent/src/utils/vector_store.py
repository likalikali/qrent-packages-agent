import asyncio
import os
from typing import Callable, Set, TypeVar

from llama_index.vector_stores.milvus import MilvusVectorStore

TRUE_VALUES: Set[str] = {"1", "true", "yes", "y", "on"}
T = TypeVar("T")


def env_flag(key: str, default: str = "false") -> bool:
    """Return True if the environment variable represents a truthy value."""
    value = os.getenv(key, default)
    if value is None:
        return False
    return value.strip().lower() in TRUE_VALUES


def _build_with_running_loop(factory: Callable[[], T]) -> T:
    try:
        asyncio.get_running_loop()
        return factory()
    except RuntimeError:
        pass

    try:
        old_loop = asyncio.get_event_loop()
    except RuntimeError:
        old_loop = None

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)

        async def _runner() -> T:
            return factory()

        return loop.run_until_complete(_runner())
    finally:
        loop.close()
        if old_loop is not None:
            asyncio.set_event_loop(old_loop)
        else:
            asyncio.set_event_loop(None)


def build_milvus_vector_store(overwrite: bool = False) -> MilvusVectorStore:
    """Create a configured Milvus vector store instance."""
    metric = os.getenv("MILVUS_INDEX_METRIC", "IP").upper()
    index_type = os.getenv("MILVUS_INDEX_TYPE", "FLAT").upper()
    index_config = {"index_type": index_type, "metric_type": metric}

    use_secure = env_flag("MILVUS_USE_SECURE", "false")
    host = os.getenv("MILVUS_HOST", "127.0.0.1")
    port = int(os.getenv("MILVUS_PORT", "19530"))
    uri = os.getenv("MILVUS_URI", "").strip()
    if not uri:
        if host.startswith("http://") or host.startswith("https://"):
            if ":" not in host.split("//", 1)[1]:
                uri = f"{host}:{port}"
            else:
                uri = host
        else:
            scheme = "https" if use_secure else "http"
            uri = f"{scheme}://{host}:{port}"

    token = os.getenv("MILVUS_TOKEN", "").strip()
    user = os.getenv("MILVUS_USER", "").strip()
    password = os.getenv("MILVUS_PASSWORD", "").strip()
    if not token and user and password:
        token = f"{user}:{password}"
    if not token and not user and password and ":" in password:
        token = password

    timeout = os.getenv("MILVUS_TIMEOUT", "").strip()
    client_timeout = float(timeout) if timeout else None

    def _factory() -> MilvusVectorStore:
        return MilvusVectorStore(
            uri=uri,
            token=token,
            collection_name=os.getenv("MILVUS_COLLECTION", "qrent_notion"),
            dim=int(os.getenv("MILVUS_DIM", "1536")),
            overwrite=overwrite,
            similarity_metric=metric,
            index_config=index_config,
            timeout=client_timeout,
        )

    return _build_with_running_loop(_factory)
