# Changelog

本文件记录项目所有重要变更。
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/),
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 修复
- 兼容 Zilliz JSON 元数据读取，确保参考文献 URL 可用
- 强制脚注使用数字编号，避免输出 [n] 占位符
- 参考文献按标题与 URL 去重

## [0.1.0] - 2026-01-19

### 新增
- RAG 回答增加脚注引用与参考文献（标题/URL）
- Graph retrieval 节点支持直接输出 RAG 结果用于调试

### 变更
- Notion 索引元数据补充 title 以支持引用


