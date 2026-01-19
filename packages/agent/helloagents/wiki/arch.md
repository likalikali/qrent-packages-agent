# 架构设计

## 总体架构
`mermaid
flowchart TD
    A[用户请求] --> B[LangGraph Agent]
    B --> C[工具层]
    C --> D[RAG 检索]
    D --> E[Milvus/Notion 知识库]
    B --> F[LLM]
`

## 技术栈
- **后端:** Python
- **编排:** LangGraph
- **LLM:** LangChain + Provider
- **数据:** Milvus / Notion

## 核心流程
`mermaid
sequenceDiagram
    participant U as User
    participant G as Graph
    participant R as RAG
    participant L as LLM
    U->>G: 提问
    G->>R: 检索
    R->>L: 结合上下文生成
    L-->>G: 回答
    G-->>U: 输出
`

## 重大架构决策
完整的ADR存储在各变更的how.md中，本章节提供索引。

| adr_id | title | date | status | affected_modules | details |
|--------|-------|------|--------|------------------|---------|