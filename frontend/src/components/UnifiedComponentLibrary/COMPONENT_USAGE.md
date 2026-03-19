# 统一前端组件库使用文档

## 概述

统一前端组件库提供了一套标准化的React组件，用于解决项目中存在的组件重复、功能重叠和组织混乱问题。

## 快速开始

### 安装和导入

```javascript
// 导入整个组件库
import { Button, Modal, Loading, ErrorBoundary } from './UnifiedComponentLibrary';

// 或者导入单个组件
import Button from './UnifiedComponentLibrary/Core/Button';
```

### 基础使用示例

```jsx
import React, { useState } from 'react';
import { Button, Modal, Loading } from './UnifiedComponentLibrary';

function App() {
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  return (
    <div>
      {/* 按钮组件 */}
      <Button 
        variant="primary" 
        onClick={() => setModalOpen(true)}
      >
        打开模态框
      </Button>

      {/* 模态框组件 */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="示例模态框"
        footer={
          <Button variant="primary" onClick={() => setModalOpen(false)}>
            关闭
          </Button>
        }
      >
        <p>这是一个模态框示例</p>
      </Modal>

      {/* 加载组件 */}
      {loading && (
        <Loading type="spinner" text="加载中..." />
      )}
    </div>
  );
}
```

## 组件详细文档

### 1. Button 按钮组件

#### 基本用法

```jsx
import { Button } from './UnifiedComponentLibrary';

// 基础按钮
<Button variant="primary">主要按钮</Button>

// 带图标按钮
<Button 
  variant="outline" 
  icon={<FiPlus />} 
  iconPosition="left"
>
  添加项目
</Button>

// 加载状态按钮
<Button loading={true} disabled={true}>
  处理中...
</Button>
```

#### 属性说明

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| variant | 'primary'\|'secondary'\|'success'\|'warning'\|'danger'\|'outline'\|'ghost' | 'primary' | 按钮变体 |
| size | 'small'\|'medium'\|'large' | 'medium' | 按钮大小 |
| disabled | boolean | false | 是否禁用 |
| loading | boolean | false | 加载状态 |
| icon | ReactNode | - | 图标元素 |
| iconPosition | 'left'\|'right' | 'left' | 图标位置 |
| onClick | function | - | 点击事件 |
| type | 'button'\|'submit'\|'reset' | 'button' | 按钮类型 |
| className | string | '' | 自定义类名 |

#### 变体示例

```jsx
// 所有变体示例
<div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
  <Button variant="primary">主要</Button>
  <Button variant="secondary">次要</Button>
  <Button variant="success">成功</Button>
  <Button variant="warning">警告</Button>
  <Button variant="danger">危险</Button>
  <Button variant="outline">轮廓</Button>
  <Button variant="ghost">幽灵</Button>
</div>
```

### 2. Modal 模态框组件

#### 基本用法

```jsx
import { Modal, Button } from './UnifiedComponentLibrary';

function ExampleModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>
        打开模态框
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="确认操作"
        size="medium"
        footer={
          <>
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              取消
            </Button>
            <Button variant="primary" onClick={() => {
              // 处理确认逻辑
              setIsOpen(false);
            }}>
              确认
            </Button>
          </>
        }
      >
        <p>确定要执行此操作吗？此操作不可撤销。</p>
      </Modal>
    </>
  );
}
```

#### 属性说明

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| isOpen | boolean | false | 是否显示模态框 |
| onClose | function | - | 关闭回调 |
| title | string | - | 标题 |
| size | 'small'\|'medium'\|'large'\|'fullscreen' | 'medium' | 模态框尺寸 |
| position | 'center'\|'top'\|'bottom' | 'center' | 模态框位置 |
| showCloseButton | boolean | true | 是否显示关闭按钮 |
| closeOnOverlayClick | boolean | true | 点击遮罩层是否关闭 |
| closeOnEscape | boolean | true | 按ESC键是否关闭 |
| footer | ReactNode | - | 底部内容 |
| className | string | '' | 自定义类名 |

#### 尺寸示例

```jsx
// 不同尺寸的模态框
<Modal size="small" title="小模态框">内容较少时使用</Modal>
<Modal size="medium" title="中模态框">标准内容使用</Modal>
<Modal size="large" title="大模态框">内容较多时使用</Modal>
<Modal size="fullscreen" title="全屏模态框">复杂操作使用</Modal>
```

### 3. Loading 加载组件

#### 基本用法

```jsx
import { Loading } from './UnifiedComponentLibrary';

// 旋转加载器
<Loading type="spinner" text="加载中..." />

// 点状加载器
<Loading type="dots" size="large" />

// 进度条
<Loading type="progress" progress={75} text="处理进度" />

// 骨架屏
<Loading type="skeleton" />

// 全屏加载
<Loading type="spinner" fullscreen={true} text="页面加载中" />
```

#### 属性说明

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | 'spinner'\|'dots'\|'progress'\|'skeleton' | 'spinner' | 加载类型 |
| size | 'small'\|'medium'\|'large' | 'medium' | 加载器大小 |
| color | string | - | 加载器颜色 |
| text | string | - | 加载文本 |
| progress | number | - | 进度百分比（0-100） |
| overlay | boolean | false | 是否显示遮罩层 |
| fullscreen | boolean | false | 是否全屏显示 |
| className | string | '' | 自定义类名 |

#### 类型示例

```jsx
// 所有加载类型
<div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
  <Loading type="spinner" text="旋转" />
  <Loading type="dots" text="点状" />
  <Loading type="progress" progress={50} text="进度" />
  <Loading type="skeleton" text="骨架" />
</div>
```

### 4. ErrorBoundary 错误边界组件

#### 基本用法

```jsx
import { ErrorBoundary } from './UnifiedComponentLibrary';

function App() {
  return (
    <ErrorBoundary
      showDetails={true}
      onError={(error, errorInfo) => {
        // 发送错误报告
        console.error('组件错误:', error, errorInfo);
      }}
    >
      <YourComponent />
    </ErrorBoundary>
  );
}
```

#### 自定义回退界面

```jsx
<ErrorBoundary
  fallback={
    <div style={{ 
      padding: '40px', 
      textAlign: 'center',
      backgroundColor: '#f5f5f5'
    }}>
      <h3>组件加载失败</h3>
      <p>抱歉，当前组件出现了一些问题。</p>
      <button onClick={resetError}>重试</button>
    </div>
  }
>
  <YourComponent />
</ErrorBoundary>
```

#### 属性说明

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| children | ReactNode | - | 子组件 |
| fallback | ReactNode | - | 错误回退组件 |
| onError | function | - | 错误回调 |
| showDetails | boolean | false | 是否显示错误详情 |
| className | string | '' | 自定义类名 |

## 设计系统

### 颜色系统

```javascript
import { designTokens } from './UnifiedComponentLibrary';

// 使用设计令牌
const primaryColor = designTokens.colors.primary[500];
const successColor = designTokens.colors.success[500];
```

#### 可用颜色

- **主色调 (primary)**: 50-900 共10个梯度
- **灰色调 (gray)**: 50-900 共10个梯度  
- **成功色 (success)**: 500, 600
- **警告色 (warning)**: 500, 600
- **危险色 (danger)**: 500, 600

### 间距系统

```css
/* 使用CSS变量 */
.element {
  padding: var(--ucl-spacing-md);
  margin-bottom: var(--ucl-spacing-lg);
}
```

#### 可用间距

- xs: 4px
- sm: 8px  
- md: 16px
- lg: 24px
- xl: 32px
- xxl: 48px

### 圆角系统

```css
.element {
  border-radius: var(--ucl-border-radius-md);
}
```

#### 可用圆角

- sm: 4px
- md: 6px
- lg: 8px  
- xl: 12px

## 最佳实践

### 1. 组件组合使用

```jsx
// 推荐的组合方式
function ComplexComponent() {
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <ErrorBoundary>
      <div>
        <Button 
          loading={loading}
          onClick={async () => {
            setLoading(true);
            try {
              await performAction();
              setModalOpen(true);
            } finally {
              setLoading(false);
            }
          }}
        >
          执行操作
        </Button>

        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="操作成功"
        >
          <p>操作已完成！</p>
        </Modal>
      </div>
    </ErrorBoundary>
  );
}
```

### 2. 样式定制

```jsx
// 使用className进行样式定制
<Button 
  className="custom-button"
  variant="primary"
>
  自定义按钮
</Button>

// CSS样式
.custom-button {
  border-radius: 20px;
  font-weight: bold;
}
```

### 3. 无障碍访问

所有组件都支持无障碍访问：

- 按钮组件支持键盘导航
- 模态框组件支持ESC键关闭
- 加载组件提供屏幕阅读器支持
- 错误边界组件提供错误信息访问

## 迁移指南

### 从旧组件迁移

#### 按钮组件迁移

**旧代码：**
```jsx
// 各种不同的按钮实现
<button className="btn-primary">主要按钮</button>
<button className="btn-secondary">次要按钮</button>
```

**新代码：**
```jsx
import { Button } from './UnifiedComponentLibrary';

<Button variant="primary">主要按钮</Button>
<Button variant="secondary">次要按钮</Button>
```

#### 模态框组件迁移

**旧代码：**
```jsx
// 各种模态框实现
<Modal isOpen={open} onClose={handleClose}>
  <div>内容</div>
</Modal>
```

**新代码：**
```jsx
import { Modal } from './UnifiedComponentLibrary';

<Modal 
  isOpen={open} 
  onClose={handleClose}
  title="标题"
>
  <div>内容</div>
</Modal>
```

### 渐进式迁移策略

1. **第一阶段**: 在新功能中使用统一组件
2. **第二阶段**: 逐步替换现有组件
3. **第三阶段**: 清理重复的旧组件

## 故障排除

### 常见问题

#### 1. 组件样式不显示

**问题**: 导入组件后样式不生效

**解决方案**: 确保CSS文件正确导入，检查CSS变量定义

#### 2. 模态框无法关闭

**问题**: 点击遮罩层或ESC键无法关闭模态框

**解决方案**: 检查`onClose`回调函数是否正确设置

#### 3. 错误边界不工作

**问题**: 错误边界没有捕获到错误

**解决方案**: 确保错误发生在错误边界的子组件中

### 调试技巧

```javascript
// 启用详细日志
console.log('组件属性:', props);

// 检查CSS变量
console.log('CSS变量:', getComputedStyle(document.documentElement));
```

## 版本信息

- **当前版本**: 1.0.0
- **构建日期**: 2025-03-18
- **兼容性**: React 16.8+

## 技术支持

如有问题，请参考：

1. 查看组件示例代码
2. 检查设计系统变量
3. 参考迁移指南
4. 联系开发团队

---

**文档版本**: 1.0.0  
**最后更新**: 2025-03-18