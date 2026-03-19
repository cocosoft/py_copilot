# 知识库系统测试报告

## 测试摘要
- 总测试数: 7
- 通过: 6
- 失败: 1
- 成功率: 85.71%

## 失败测试详情
### 搜索功能
**错误**: Page.press: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("input[type=\"search\"]")


## 测试详情
- 知识库管理功能: ✅ 通过
- 文档管理功能: ✅ 通过
- 知识图谱功能: ✅ 通过
- 实体管理功能: ✅ 通过
- 搜索功能: ❌ 失败
  - 错误: Page.press: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("input[type=\"search\"]")

- 批量操作功能: ✅ 通过
- 处理状态功能: ✅ 通过
