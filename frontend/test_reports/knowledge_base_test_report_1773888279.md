# 知识库系统测试报告

## 测试摘要
- 总测试数: 7
- 通过: 3
- 失败: 4
- 成功率: 42.86%

## 失败测试详情
### 知识库管理功能
**错误**: Page.wait_for_selector: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"knowledge-base-list\"]") to be visible


### 文档管理功能
**错误**: Page.wait_for_selector: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"document-list\"]") to be visible


### 知识图谱功能
**错误**: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"knowledge-base-item\"]").first


### 实体管理功能
**错误**: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"knowledge-base-item\"]").first


## 测试详情
- 知识库管理功能: ❌ 失败
  - 错误: Page.wait_for_selector: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"knowledge-base-list\"]") to be visible

- 文档管理功能: ❌ 失败
  - 错误: Page.wait_for_selector: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"document-list\"]") to be visible

- 知识图谱功能: ❌ 失败
  - 错误: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"knowledge-base-item\"]").first

- 实体管理功能: ❌ 失败
  - 错误: Locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for locator("[data-testid=\"knowledge-base-item\"]").first

- 搜索功能: ✅ 通过
- 批量操作功能: ✅ 通过
- 处理状态功能: ✅ 通过
