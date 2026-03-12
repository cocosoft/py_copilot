# 知识库模块组件文档

本文档介绍知识库模块中创建的所有组件及其使用方法。

## 目录

- [UI 组件](#ui-组件)
- [知识库专用组件](#知识库专用组件)
- [Hooks](#hooks)
- [工具函数](#工具函数)

---

## UI 组件

### Button 按钮

通用按钮组件，支持多种变体和尺寸。

```jsx
import Button from './components/UI/Button';

// 基础用法
<Button onClick={handleClick}>点击我</Button>

// 变体
<Button variant="primary">主要按钮</Button>
<Button variant="secondary">次要按钮</Button>
<Button variant="danger">危险按钮</Button>
<Button variant="ghost">幽灵按钮</Button>

// 尺寸
<Button size="small">小按钮</Button>
<Button size="medium">中按钮</Button>
<Button size="large">大按钮</Button>

// 带图标
<Button icon={<FiPlus />}>添加</Button>

// 加载状态
<Button loading>加载中</Button>

// 禁用状态
<Button disabled>禁用</Button>
```

**Props:**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| variant | string | 'primary' | 按钮变体 |
| size | string | 'medium' | 按钮尺寸 |
| icon | ReactNode | - | 图标 |
| loading | boolean | false | 加载状态 |
| disabled | boolean | false | 禁用状态 |
| onClick | function | - | 点击事件 |

---

### PageSkeleton 页面骨架屏

页面加载时的占位显示组件。

```jsx
import PageSkeleton, { FullPageSkeleton, KnowledgePageSkeleton } from './components/UI/PageSkeleton';

// 列表类型
<PageSkeleton type="list" rows={5} />

// 网格类型
<PageSkeleton type="grid" rows={3} columns={4} />

// 卡片类型
<PageSkeleton type="card" />

// 文本类型
<PageSkeleton type="text" rows={8} />

// 完整页面骨架
<FullPageSkeleton />

// 知识库页面骨架
<KnowledgePageSkeleton />
```

**Props:**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string | 'list' | 骨架屏类型 |
| rows | number | 5 | 行数 |
| columns | number | 3 | 列数（仅grid类型）|

---

### ErrorBoundary 错误边界

捕获子组件错误，防止应用崩溃。

```jsx
import ErrorBoundary, { KnowledgeErrorBoundary } from './components/UI/ErrorBoundary';

// 基础用法
<ErrorBoundary>
  <MyComponent />
</ErrorBoundary>

// 自定义降级UI
<ErrorBoundary
  fallback={({ error, onReset, onReload }) => (
    <div>
      <p>出错了: {error.message}</p>
      <button onClick={onReset}>重试</button>
    </div>
  )}
>
  <MyComponent />
</ErrorBoundary>

// 知识库专用
<KnowledgeErrorBoundary>
  <KnowledgeComponent />
</KnowledgeErrorBoundary>
```

**Props:**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| fallback | function | - | 自定义降级UI |
| onError | function | - | 错误回调 |
| onReset | function | - | 重置回调 |

---

## 知识库专用组件

### DocumentCard 文档卡片

文档列表项组件，支持列表和网格视图。

```jsx
import DocumentCard from './components/Knowledge/DocumentCard';

<DocumentCard
  document={{
    id: '1',
    name: '文档.pdf',
    type: 'pdf',
    size: 1024000,
    status: 'completed',
    createdAt: new Date(),
  }}
  viewMode="list"
  selected={false}
  onSelect={() => {}}
  onClick={() => {}}
  onDelete={() => {}}
  onDownload={() => {}}
/>
```

**Props:**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| document | object | required | 文档数据 |
| viewMode | string | 'list' | 视图模式 |
| selected | boolean | false | 是否选中 |
| onSelect | function | - | 选择回调 |
| onClick | function | - | 点击回调 |
| onDelete | function | - | 删除回调 |
| onDownload | function | - | 下载回调 |

---

### UploadButton 上传按钮

文件上传组件，支持拖拽上传。

```jsx
import UploadButton from './components/Knowledge/UploadButton';

<UploadButton
  onUpload={handleUpload}
  accept=".pdf,.doc,.docx"
  maxSize={100 * 1024 * 1024}
  multiple
>
  上传文件
</UploadButton>
```

**Props:**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| onUpload | function | required | 上传回调 |
| accept | string | - | 接受的文件类型 |
| maxSize | number | - | 最大文件大小（字节）|
| multiple | boolean | false | 是否多选 |
| disabled | boolean | false | 是否禁用 |

---

### BatchOperationToolbar 批量操作工具栏

批量操作工具栏组件。

```jsx
import BatchOperationToolbar from './components/Knowledge/BatchOperationToolbar';

<BatchOperationToolbar
  selectedCount={5}
  onDelete={() => {}}
  onDownload={() => {}}
  onVectorize={() => {}}
  onClear={() => {}}
/>
```

**Props:**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| selectedCount | number | required | 选中数量 |
| onDelete | function | - | 删除回调 |
| onDownload | function | - | 下载回调 |
| onVectorize | function | - | 向量化回调 |
| onClear | function | - | 清除选择回调 |

---

### SmartSearch 智能搜索

智能搜索组件，支持搜索建议和历史记录。

```jsx
import SmartSearch from './components/Knowledge/SmartSearch';

<SmartSearch
  value={searchQuery}
  onChange={setSearchQuery}
  onSearch={handleSearch}
  suggestions={suggestions}
  history={searchHistory}
  placeholder="搜索文档..."
/>
```

**Props:**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| value | string | '' | 搜索值 |
| onChange | function | - | 变化回调 |
| onSearch | function | - | 搜索回调 |
| suggestions | array | [] | 搜索建议 |
| history | array | [] | 搜索历史 |
| placeholder | string | - | 占位文本 |

---

## Hooks

### useDebounce

防抖 Hook，用于延迟执行函数。

```jsx
import { useDebounce } from './hooks/useDebounce';

// 基础用法
const debouncedValue = useDebounce(inputValue, 300);

// 函数防抖
const debouncedSearch = useDebounce((query) => {
  performSearch(query);
}, 500);
```

**参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| value | any | 需要防抖的值或函数 |
| delay | number | 延迟时间（毫秒）|

---

### usePerformance

性能监控 Hook。

```jsx
import { usePerformance, useRenderPerformance } from './utils/performance';

// 使用性能监控
const { measureRender, recordMetric } = usePerformance();

// 测量组件渲染
useRenderPerformance('MyComponent');

// 记录自定义指标
recordMetric('CustomMetric', 100);
```

---

## 工具函数

### performanceLogger

性能监控工具。

```jsx
import performanceLogger from './utils/performance';

// 启动监控
performanceLogger.start();

// 测量函数执行时间
const measuredFn = performanceLogger.measureFunction(myFunction, 'myFunction');

// 获取指标
const metrics = performanceLogger.getMetrics();
const stats = performanceLogger.getStats();

// 停止监控
performanceLogger.stop();
```

---

## 状态管理

### knowledgeStore

知识库状态管理。

```jsx
import { useKnowledgeStore } from './stores/knowledgeStore';

const MyComponent = () => {
  const {
    // 状态
    knowledgeBases,
    currentKnowledgeBase,
    documents,
    selectedDocuments,
    
    // 动作
    setCurrentKnowledgeBase,
    selectDocument,
    deselectDocument,
    clearSelection,
    batchSelect,
    batchDelete,
    
    // 计算属性
    selectedCount,
    allSelected,
  } = useKnowledgeStore();
  
  return (
    // ...
  );
};
```

---

## 路由配置

### 知识库路由

```jsx
import { knowledgeRoutes, prefetchKnowledge } from './routes/knowledgeRoutes';

// 在路由配置中使用
const routes = [
  knowledgeRoutes,
  // ...其他路由
];

// 预加载知识库模块
prefetchKnowledge().then(() => {
  console.log('知识库模块已预加载');
});
```

**路由路径:**

| 路径 | 页面 | 说明 |
|------|------|------|
| /knowledge | - | 重定向到 /knowledge/documents |
| /knowledge/documents | DocumentManagement | 文档管理 |
| /knowledge/graph | KnowledgeGraph | 知识图谱 |
| /knowledge/vectorization | VectorizationManagement | 向量化管理 |
| /knowledge/search | AdvancedSearch | 高级搜索 |
| /knowledge/settings | KnowledgeSettings | 知识库设置 |

---

## 设计系统

### CSS 变量

```css
/* 颜色 */
--color-primary: #1890ff;
--color-success: #52c41a;
--color-warning: #faad14;
--color-error: #ff4d4f;

/* 间距 */
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;

/* 圆角 */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;

/* 阴影 */
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 12px rgba(0,0,0,0.1);
--shadow-lg: 0 8px 24px rgba(0,0,0,0.15);
```

---

## 最佳实践

1. **组件使用**
   - 优先使用已有的 UI 组件，保持界面一致性
   - 使用 ErrorBoundary 包裹可能出错的组件
   - 使用 PageSkeleton 作为加载占位

2. **性能优化**
   - 使用虚拟列表渲染大量数据
   - 使用防抖处理频繁触发的事件
   - 使用路由懒加载减少首屏加载时间

3. **状态管理**
   - 使用 knowledgeStore 管理知识库相关状态
   - 避免在组件中直接修改状态
   - 使用批量操作提高性能

4. **错误处理**
   - 使用 try-catch 处理异步操作
   - 使用错误边界捕获渲染错误
   - 提供友好的错误提示

---

## 更新日志

### v1.0.0
- 初始版本发布
- 添加基础 UI 组件
- 添加知识库专用组件
- 添加性能监控工具
- 添加错误边界组件
