# 前端单元测试设置文档

## 概述

本文档描述了为Py Copilot前端项目设置的完整单元测试框架，包括测试环境配置、测试工具、示例测试和最佳实践。

## 测试框架

- **测试运行器**: Jest
- **组件测试**: Testing Library React
- **用户交互模拟**: Testing Library User Event
- **DOM测试工具**: @testing-library/jest-dom
- **测试环境**: jsdom

## 项目结构

```
frontend/
├── jest.config.cjs          # Jest配置文件
├── .babelrc                 # Babel转换配置
├── tests/
│   ├── setup.js             # 测试环境设置
│   └── __mocks__/
│       ├── styleMock.js     # CSS文件模拟
│       └── fileMock.js      # 静态文件模拟
└── src/
    ├── components/UI/
    │   └── __tests__/       # UI组件测试
    ├── stores/
    │   └── __tests__/       # 状态管理测试
    ├── hooks/
    │   └── __tests__/       # 自定义Hook测试
    └── utils/
        └── __tests__/       # 工具函数测试
```

## 测试命令

### 基础测试命令
```bash
# 运行所有测试
npm test

# 监听模式运行测试
npm run test:watch

# 生成覆盖率报告
npm run test:coverage

# CI环境测试（无监听模式）
npm run test:ci

# 清除Jest缓存
npm run test:clear
```

## 示例测试

### 1. 组件测试 (ModelSelector.test.jsx)

测试了ModelSelector组件的以下功能：
- 组件渲染
- 搜索和过滤功能
- 模型选择交互
- 键盘导航
- 无障碍功能

### 2. 状态管理测试 (rootStore.test.jsx)

测试了Root Store的以下功能：
- Store Provider和Context
- Store状态管理
- 中间件集成
- 数据持久化
- 错误处理
- 性能监控

### 3. Hook测试 (useApi.test.jsx)

测试了useApi Hook的以下功能：
- 数据获取
- 错误处理
- 缓存管理
- 重试逻辑
- 乐观更新

## 测试配置详情

### Jest配置要点

1. **测试环境**: jsdom
2. **转换**: babel-jest处理JS/JSX文件
3. **模拟**: CSS和静态文件使用模拟
4. **覆盖率**: 收集代码覆盖率，设置阈值
5. **超时**: 10秒测试超时时间

### Babel配置

支持现代JavaScript语法和React JSX转换。

### 全局设置

- 模拟IntersectionObserver和ResizeObserver
- 模拟localStorage和sessionStorage
- 模拟window.matchMedia
- 设置HTMLElement.offsetParent
- 配置测试环境console输出

## 测试最佳实践

### 1. 组件测试
- 使用语义化查询（getByRole, getByLabelText）
- 测试用户交互而非实现细节
- 模拟外部依赖
- 测试无障碍功能

### 2. 状态管理测试
- 测试状态更新逻辑
- 验证中间件功能
- 测试异步操作
- 验证数据持久化

### 3. Hook测试
- 使用renderHook
- 测试异步操作
- 模拟API调用
- 验证副作用

## 覆盖率要求

- **分支覆盖率**: 70%
- **函数覆盖率**: 80%
- **行覆盖率**: 80%
- **语句覆盖率**: 80%

## 注意事项

1. 测试文件名规范：`*.test.jsx` 或 `*.spec.jsx`
2. 测试文件应与源文件放在同一目录的`__tests__`文件夹中
3. 使用描述性测试名称
4. 每个测试用例应该独立，不依赖其他测试
5. 适当使用mock来隔离测试单元

## 故障排除

### 常见问题

1. **ES模块错误**: 使用.cjs扩展名的配置文件
2. **CSS导入错误**: 使用styleMock模拟CSS文件
3. **异步测试**: 使用async/await和act()包装
4. **内存泄漏**: 在每个测试后清理mock和组件

### 调试技巧

1. 使用`--verbose`标志获得详细输出
2. 使用`--no-coverage`禁用覆盖率以加速测试
3. 使用`--testNamePattern`运行特定测试
4. 在Jest配置中启用`verbose: true`

## 扩展指南

### 添加新测试

1. 在对应目录创建`__tests__`文件夹
2. 创建测试文件（遵循命名规范）
3. 导入必要的测试工具和组件
4. 编写测试用例
5. 运行测试验证

### 自定义匹配器

可以在`tests/setup.js`中添加自定义Jest匹配器：

```javascript
import '@testing-library/jest-dom';

// 添加自定义匹配器
expect.extend({
  toBeWithinRange(received, floor, ceiling) {
    const pass = received >= floor && received <= ceiling;
    if (pass) {
      return {
        message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
        pass: true,
      };
    } else {
      return {
        message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
        pass: false,
      };
    }
  },
});
```

---

本测试框架为Py Copilot前端项目提供了全面的测试覆盖，确保代码质量和功能正确性。