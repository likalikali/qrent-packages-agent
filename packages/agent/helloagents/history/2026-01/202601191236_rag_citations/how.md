# 技术设计: RAG 引用标注与检索接入

## 技术方案
### 核心技术
- LangChain + ChatOpenAI
- LlamaIndex + MilvusVectorStore
- Notion 文档元数据

### 实现要点
- 检索阶段返回块文本与元数据（title/url）。
- 将检索块去重后编号，作为引用列表。
- 使用 LLM 生成回答，要求在句末追加脚注标记 [n]。
- 文末输出参考文献列表：标题 + URL。
- graph retrieval node 返回 RAG 最终答案，并在命中时直接结束流程。

## 安全与性能
- **安全:** 仅基于检索上下文生成；无上下文时明确告知未找到。
- **性能:** 使用 top_k 控制检索数量，避免过长上下文。

## 测试与部署
- **测试:** 运行 python -m tests.integration_tests.test_rag_tool 验证输出格式。
- **部署:** 如需引用标题/URL，需重建 Milvus 索引。