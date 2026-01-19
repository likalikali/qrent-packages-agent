# 变更提案: RAG 引用标注与检索接入

## 需求背景
现有 RAG 结果缺少明确引用，影响可追溯性；同时需要在 graph 中快速验证 RAG 输出。

## 变更内容
1. RAG 回答内加入脚注标记，并在文末输出参考文献（标题+URL）。
2. 按检索块/段落去重引用来源。
3. graph retrieval node 直接输出 RAG 最终答案用于调试。

## 影响范围
- **模块:** tools / agent
- **文件:** src/tools/rag_tool.py, src/tools/build_knowledge_base.py, src/agent/graph.py, tests/integration_tests/test_rag_tool.py
- **API:** tool search_qrent_knowledge 输出格式变化
- **数据:** Milvus 元数据字段（title/url）

## 核心场景

### 需求: RAG 回答标注引用
**模块:** tools
用户提问后输出答案，正文内带脚注标记并附参考文献列表。

#### 场景: 运营知识库问答
已命中检索块时，回答中对应事实标注 [1][2]，参考文献列出标题与 URL。
- 若知识库无答案，明确说明未找到

### 需求: graph retrieval 直出
**模块:** agent
在调试阶段，retrieval node 直接返回 RAG 最终答案。

#### 场景: RAG 调试
当 RAG 返回答案时，graph 直接输出该结果，不再进入 agent 推理。
- 输出保持脚注与参考文献格式

## 风险评估
- **风险:** 旧索引缺少标题/URL 元数据，引用为空
- **缓解:** 重新执行知识库构建，将元数据写入向量库