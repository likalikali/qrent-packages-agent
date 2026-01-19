# 数据模型

## 概述
以向量化知识库为主，使用 Milvus 存储向量与元数据。

---

## 数据表/集合

### qrent_notion
**描述:** Notion 运营知识库向量集合

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| embedding | vector | 必填 | 文本向量 |
| text | string | 可选 | 文本内容 |
| doc_id | string | 可选 | 文档标识 |
| metadata | json | 可选 | 标题/URL 等元数据 |