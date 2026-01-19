# -*- coding: utf-8 -*-
import os
import dotenv
import asyncio

dotenv.load_dotenv()

from src.tools.rag_tool import search_qrent_knowledge

QUESTION = "请给我讲一下澳洲学生公寓的情况"


async def run():
    result = await search_qrent_knowledge.ainvoke({"query": QUESTION})
    print("\n===== RAG RESULT =====")
    print(result)
    print("======================\n")


if __name__ == "__main__":
    asyncio.run(run())

