import os
import shutil
from typing import Any, Iterable, List

import dotenv
import requests
try:
    from notion_client import Client
except Exception:
    Client = None
from slugify import slugify

from llama_index.core import (
    Document,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.settings import Settings
from llama_index.embeddings.dashscope import DashScopeEmbedding
from llama_index.readers.dashscope.base import DashScopeParse
from llama_index.readers.dashscope.utils import ResultType

from src.config.path import PATHS
from src.utils.vector_store import build_milvus_vector_store, env_flag


dotenv.load_dotenv()

BACKEND = os.getenv("KNOWLEDGE_BACKEND", "milvus").lower()
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DB_IDS = [
    db_id.strip()
    for db_id in os.getenv("NOTION_DATABASE_IDS", "").split(",")
    if db_id.strip()
]
NOTION_PAGE_SIZE = int(os.getenv("NOTION_PAGE_SIZE", "100"))
INCLUDE_LOCAL_DOCS = env_flag("INCLUDE_LOCAL_DOCS", "false")
NOTION_API_VERSION = os.getenv("NOTION_API_VERSION", "2022-06-28")
NOTION_API_BASE = "https://api.notion.com/v1"

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
Settings.text_splitter = SentenceSplitter(chunk_size=1024, chunk_overlap=256)


def _rich_text_to_plain(rich_text: Iterable[dict]) -> str:
    return "".join(part.get("plain_text", "") for part in rich_text).strip()


def _request_notion(
    method: str,
    path: str,
    payload: dict | None = None,
    params: dict | None = None,
) -> dict:
    if not NOTION_API_KEY:
        raise ValueError("NOTION_API_KEY is missing. Please update your .env file.")
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }
    response = requests.request(
        method,
        f"{NOTION_API_BASE}{path}",
        headers=headers,
        json=payload,
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _query_database(notion: Any, database_id: str, cursor: str | None) -> dict:
    payload = {"page_size": NOTION_PAGE_SIZE}
    if cursor:
        payload["start_cursor"] = cursor
    if notion is not None and hasattr(notion, "databases") and hasattr(notion.databases, "query"):
        return notion.databases.query(database_id=database_id, **payload)
    return _request_notion("POST", f"/databases/{database_id}/query", payload=payload)


def _list_block_children(notion: Any, block_id: str, cursor: str | None) -> dict:
    params = {"page_size": 100}
    if cursor:
        params["start_cursor"] = cursor
    if (
        notion is not None
        and hasattr(notion, "blocks")
        and hasattr(notion.blocks, "children")
        and hasattr(notion.blocks.children, "list")
    ):
        return notion.blocks.children.list(block_id=block_id, **params)
    return _request_notion("GET", f"/blocks/{block_id}/children", params=params)


def _format_block(
    notion: Any, block: dict, indent: int = 0, include_children: bool = True
) -> List[str]:
    block_type = block.get("type")
    data = block.get(block_type, {})
    lines: List[str] = []

    if block_type in {"heading_1", "heading_2", "heading_3"}:
        level = int(block_type.split("_")[-1])
        text = _rich_text_to_plain(data.get("rich_text", []))
        prefix = "#" * level
        lines.append(f"{prefix} {text}".strip())
    elif block_type in {"paragraph", "quote"}:
        text = _rich_text_to_plain(data.get("rich_text", []))
        prefix = "> " if block_type == "quote" else ""
        if text:
            lines.append(f"{' ' * indent}{prefix}{text}".rstrip())
    elif block_type == "bulleted_list_item":
        text = _rich_text_to_plain(data.get("rich_text", []))
        if text:
            lines.append(f"{' ' * indent}- {text}".rstrip())
    elif block_type == "numbered_list_item":
        text = _rich_text_to_plain(data.get("rich_text", []))
        if text:
            lines.append(f"{' ' * indent}1. {text}".rstrip())
    elif block_type == "to_do":
        text = _rich_text_to_plain(data.get("rich_text", []))
        checkbox = "x" if data.get("checked") else " "
        if text:
            lines.append(f"{' ' * indent}- [{checkbox}] {text}".rstrip())
    elif block_type == "code":
        language = data.get("language", "")
        text = _rich_text_to_plain(data.get("rich_text", []))
        lines.append(f"```{language}".strip())
        lines.append(text)
        lines.append("```")
    elif block_type == "callout":
        text = _rich_text_to_plain(data.get("rich_text", []))
        icon = data.get("icon", {})
        emoji = icon.get("emoji") if isinstance(icon, dict) else ""
        prefix = f"{emoji} " if emoji else ""
        if text:
            lines.append(f"{' ' * indent}{prefix}{text}".rstrip())
    elif block_type == "divider":
        lines.append("---")
    elif block_type == "child_page":
        title = block.get("child_page", {}).get("title", "Untitled")
        lines.append(f"## {title}".strip())
    elif block_type == "image":
        caption = _rich_text_to_plain(data.get("caption", []))
        lines.append(f"![Image]({caption})" if caption else "![Image]")
    else:
        text = _rich_text_to_plain(data.get("rich_text", []))
        if text:
            lines.append(f"{' ' * indent}{text}".rstrip())

    if include_children and block.get("has_children"):
        lines.extend(_collect_block_lines(notion, block["id"], indent + 2))

    return [line for line in lines if line]


def _collect_block_lines(notion: Any, parent_id: str, indent: int = 0) -> List[str]:
    cursor = None
    lines: List[str] = []
    while True:
        response = _list_block_children(notion, parent_id, cursor)
        for block in response.get("results", []):
            lines.extend(_format_block(notion, block, indent=indent))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return lines


def _get_page_title(page: dict) -> str:
    for value in page.get("properties", {}).values():
        if value.get("type") == "title":
            title = _rich_text_to_plain(value.get("title", []))
            if title:
                return title
    return page.get("id", "untitled")


def load_notion_documents() -> List[Document]:
    if not NOTION_API_KEY or not NOTION_DB_IDS:
        return []

    notion = Client(auth=NOTION_API_KEY) if Client else None
    documents: List[Document] = []
    for database_id in NOTION_DB_IDS:
        cursor = None
        while True:
            response = _query_database(notion, database_id, cursor)
            for page in response.get("results", []):
                page_id = page["id"]
                title = _get_page_title(page)
                body_lines = _collect_block_lines(notion, page_id)
                if not body_lines:
                    continue
                body = f"# {title}\n\n" + "\n".join(body_lines)
                doc_id = slugify(f"{title}-{page_id[:8]}")
                documents.append(
                    Document(
                        text=body,
                        doc_id=doc_id or page_id,
                        metadata={
                            "source": "notion",
                            "database_id": database_id,
                            "notion_page_id": page_id,
                            "url": page.get("url"),
                            "last_edited_time": page.get("last_edited_time"),
                        },
                    )
                )
            if not response.get("has_more"):
                break
            cursor = response.get("next_cursor")
    print(f"Loaded {len(documents)} Notion documents.")
    return documents


def load_local_documents() -> List[Document]:
    parse = DashScopeParse(result_type=ResultType.DASHSCOPE_DOCMIND, api_key=API_KEY)
    reader = SimpleDirectoryReader(
        PATHS["DOCS_DIR"],
        file_extractor={
            ".pdf": parse,
            ".md": parse,
            ".docx": parse,
        },
    )
    docs = reader.load_data()
    print(f"Loaded {len(docs)} local documents from docs/.")
    return docs


def build_local_storage(documents: List[Document]) -> None:
    persist_dir = PATHS["KNOWLEDGE_BASE_DIR"]
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
    os.makedirs(persist_dir, exist_ok=True)

    index = VectorStoreIndex.from_documents(
        documents,
        embed_model=Settings.embed_model,
        show_progress=True,
    )
    index.storage_context.persist(persist_dir)
    print(f"Local vector store written to {persist_dir}")


def build_milvus_storage(documents: List[Document]) -> None:
    vector_store = build_milvus_vector_store(
        overwrite=env_flag("MILVUS_OVERWRITE", "false")
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=Settings.embed_model,
        show_progress=True,
    )
    print(
        f"Pushed {len(documents)} documents to Milvus collection "
        f"{vector_store.collection_name}"
    )


def main() -> None:
    documents: List[Document] = []
    documents.extend(load_notion_documents())
    if INCLUDE_LOCAL_DOCS or (not documents):
        documents.extend(load_local_documents())

    if not documents:
        raise ValueError("No documents available for indexing.")

    if BACKEND == "milvus":
        build_milvus_storage(documents)
    elif BACKEND == "local":
        build_local_storage(documents)
    else:
        raise ValueError(f"Unknown KNOWLEDGE_BACKEND: {BACKEND}")


if __name__ == "__main__":
    main()
