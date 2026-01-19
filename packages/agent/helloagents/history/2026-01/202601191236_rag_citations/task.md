# 任务清单: RAG 引用标注与检索接入

目录: helloagents/plan/202601191236_rag_citations/

---

## 1. RAG 引用生成
- [√] 1.1 在 src/tools/build_knowledge_base.py 增补 Notion 文档元数据（title/url），验证 why.md#需求-rag-回答标注引用-场景-运营知识库问答
- [√] 1.2 在 src/tools/rag_tool.py 组装检索块、去重并调用 LLM 生成带脚注与参考文献的答案，验证 why.md#需求-rag-回答标注引用-场景-运营知识库问答

## 2. Graph 接入
- [√] 2.1 在 src/agent/graph.py 中使 retrieval node 直接输出 RAG 最终答复，验证 why.md#需求-graph-retrieval-直出-场景-rag-调试

## 3. 安全检查
- [√] 3.1 执行安全检查（按G9: 输入验证、敏感信息处理、权限控制、EHRB风险规避）

## 4. 文档更新
- [√] 4.1 更新 helloagents/wiki/modules/tools.md
- [√] 4.2 更新 helloagents/wiki/modules/agent.md
- [√] 4.3 更新 helloagents/CHANGELOG.md

## 5. 测试
- [-] 5.1 运行 python -m tests.integration_tests.test_rag_tool 验证输出包含脚注与参考文献
> 备注: 未运行，需配置 LLM/Milvus 等环境并允许联网。
