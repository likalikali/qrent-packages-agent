# Qrent Agent

> 本文件包含项目级别的核心信息。详细的模块文档见 modules/ 目录。

---

## 1. 项目概述

### 目标与背景
为租房场景提供基于知识库的智能问答与生成能力。

### 范围
- **范围内:** RAG 检索、工具调用、租房信件生成
- **范围外:** 业务系统写入、支付与交易处理

### 干系人
- **负责人:** 研发团队

---

## 2. 模块索引

| 模块名称 | 职责 | 状态 | 文档 |
|---------|------|------|------|
| agent | LangGraph 入口与流程编排 | 开发中 | [modules/agent](modules/agent.md) |
| tools | 工具与 RAG 能力 | 开发中 | [modules/tools](modules/tools.md) |
| utils | 通用辅助与校验 | 开发中 | [modules/utils](modules/utils.md) |
| config | 配置与路径管理 | 开发中 | [modules/config](modules/config.md) |
| schemas | 数据结构与输入模型 | 开发中 | [modules/schemas](modules/schemas.md) |
| pipeline | 业务流水线逻辑 | 开发中 | [modules/pipeline](modules/pipeline.md) |
| prompts | 系统与任务提示词 | 开发中 | [modules/prompts](modules/prompts.md) |

---

## 3. 快速链接
- [技术约定](../project.md)
- [架构设计](arch.md)
- [API 手册](api.md)
- [数据模型](data.md)
- [变更历史](../history/index.md)