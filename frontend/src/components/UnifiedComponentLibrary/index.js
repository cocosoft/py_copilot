/**
 * 统一前端组件库入口文件
 * 
 * 提供项目中所有统一组件的统一导出接口
 * 解决组件重复、功能重叠和组织混乱问题
 * 
 * 任务编号: Phase1-Week3
 * 阶段: 第一阶段 - 功能重复问题优化
 */

// Core 核心基础组件
export { default as Button } from './Core/Button';
export { default as Modal } from './Core/Modal';
export { default as Loading } from './Core/Loading';
export { default as ErrorBoundary } from './Core/ErrorBoundary';
export { default as Input } from './Core/Input';

// Layout 布局组件
// export { default as Header } from './Layout/Header';
// export { default as Sidebar } from './Layout/Sidebar';
// export { default as Footer } from './Layout/Footer';

// DataDisplay 数据展示组件
export { default as Card } from './DataDisplay/Card';
export { default as Badge } from './DataDisplay/Badge';
// export { default as Table } from './DataDisplay/Table';
// export { default as List } from './DataDisplay/List';

// DataEntry 数据输入组件
// export { default as Input } from './DataEntry/Input';
// export { default as Select } from './DataEntry/Select';
// export { default as Upload } from './DataEntry/Upload';

// Feedback 反馈组件
// export { default as Toast } from './Feedback/Toast';
// export { default as Notification } from './Feedback/Notification';
// export { default as Message } from './Feedback/Message';

// Navigation 导航组件
// export { default as Breadcrumb } from './Navigation/Breadcrumb';
// export { default as Pagination } from './Navigation/Pagination';
// export { default as Tabs } from './Navigation/Tabs';

// Knowledge 知识库业务组件
// export { default as DocumentCard } from './Knowledge/DocumentCard';
// export { default as EntityManagement } from './Knowledge/EntityManagement';
// export { default as SearchPanel } from './Knowledge/SearchPanel';

// KnowledgeGraph 知识图谱业务组件
// export { default as GraphVisualization } from './KnowledgeGraph/GraphVisualization';
// export { default as EntityConfig } from './KnowledgeGraph/EntityConfig';
// export { default as RelationManagement } from './KnowledgeGraph/RelationManagement';

// 设计系统变量
export const designTokens = {
  colors: {
    primary: {
      50: 'var(--ucl-color-primary-50, #f0f9ff)',
      100: 'var(--ucl-color-primary-100, #e0f2fe)',
      200: 'var(--ucl-color-primary-200, #bae6fd)',
      300: 'var(--ucl-color-primary-300, #7dd3fc)',
      400: 'var(--ucl-color-primary-400, #38bdf8)',
      500: 'var(--ucl-color-primary-500, #0ea5e9)',
      600: 'var(--ucl-color-primary-600, #0284c7)',
      700: 'var(--ucl-color-primary-700, #0369a1)',
      800: 'var(--ucl-color-primary-800, #075985)',
      900: 'var(--ucl-color-primary-900, #0c4a6e)',
    },
    gray: {
      50: 'var(--ucl-color-gray-50, #f9fafb)',
      100: 'var(--ucl-color-gray-100, #f3f4f6)',
      200: 'var(--ucl-color-gray-200, #e5e7eb)',
      300: 'var(--ucl-color-gray-300, #d1d5db)',
      400: 'var(--ucl-color-gray-400, #9ca3af)',
      500: 'var(--ucl-color-gray-500, #6b7280)',
      600: 'var(--ucl-color-gray-600, #4b5563)',
      700: 'var(--ucl-color-gray-700, #374151)',
      800: 'var(--ucl-color-gray-800, #1f2937)',
      900: 'var(--ucl-color-gray-900, #111827)',
    },
    success: {
      500: 'var(--ucl-color-success-500, #10b981)',
      600: 'var(--ucl-color-success-600, #059669)',
    },
    warning: {
      500: 'var(--ucl-color-warning-500, #f59e0b)',
      600: 'var(--ucl-color-warning-600, #d97706)',
    },
    danger: {
      500: 'var(--ucl-color-danger-500, #ef4444)',
      600: 'var(--ucl-color-danger-600, #dc2626)',
    },
  },
  spacing: {
    xs: 'var(--ucl-spacing-xs, 4px)',
    sm: 'var(--ucl-spacing-sm, 8px)',
    md: 'var(--ucl-spacing-md, 16px)',
    lg: 'var(--ucl-spacing-lg, 24px)',
    xl: 'var(--ucl-spacing-xl, 32px)',
    xxl: 'var(--ucl-spacing-xxl, 48px)',
  },
  borderRadius: {
    sm: 'var(--ucl-border-radius-sm, 4px)',
    md: 'var(--ucl-border-radius-md, 6px)',
    lg: 'var(--ucl-border-radius-lg, 8px)',
    xl: 'var(--ucl-border-radius-xl, 12px)',
  },
  shadows: {
    sm: 'var(--ucl-shadow-sm, 0 1px 2px 0 rgba(0, 0, 0, 0.05))',
    md: 'var(--ucl-shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1))',
    lg: 'var(--ucl-shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1))',
    xl: 'var(--ucl-shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1))',
  },
  typography: {
    fontFamily: {
      sans: 'var(--ucl-font-family-sans, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif)',
      mono: 'var(--ucl-font-family-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace)',
    },
    fontSize: {
      xs: 'var(--ucl-font-size-xs, 0.75rem)',
      sm: 'var(--ucl-font-size-sm, 0.875rem)',
      base: 'var(--ucl-font-size-base, 1rem)',
      lg: 'var(--ucl-font-size-lg, 1.125rem)',
      xl: 'var(--ucl-font-size-xl, 1.25rem)',
      '2xl': 'var(--ucl-font-size-2xl, 1.5rem)',
      '3xl': 'var(--ucl-font-size-3xl, 1.875rem)',
    },
    fontWeight: {
      normal: 'var(--ucl-font-weight-normal, 400)',
      medium: 'var(--ucl-font-weight-medium, 500)',
      semibold: 'var(--ucl-font-weight-semibold, 600)',
      bold: 'var(--ucl-font-weight-bold, 700)',
    },
  },
};

// 工具函数 - 暂时移除，因为utils模块不存在
// 如果需要工具函数，可以在这里直接定义或导入具体的工具模块

// 组件使用示例
export const usageExamples = {
  Button: `
import { Button } from './UnifiedComponentLibrary';

// 基础使用
<Button variant="primary" onClick={() => console.log('Clicked')}>
  点击我
</Button>

// 带图标
<Button variant="outline" icon={<FiPlus />} iconPosition="left">
  添加项目
</Button>

// 加载状态
<Button loading={true} disabled={true}>
  处理中...
</Button>
  `,
  
  Modal: `
import { Modal } from './UnifiedComponentLibrary';

// 基础模态框
<Modal 
  isOpen={isOpen} 
  onClose={() => setIsOpen(false)}
  title="确认操作"
  footer={
    <>
      <Button variant="outline" onClick={() => setIsOpen(false)}>
        取消
      </Button>
      <Button variant="primary" onClick={handleConfirm}>
        确认
      </Button>
    </>
  }
>
  <p>确定要执行此操作吗？</p>
</Modal>
  `,
  
  Loading: `
import { Loading } from './UnifiedComponentLibrary';

// 旋转加载器
<Loading type="spinner" size="large" text="加载中..." />

// 进度条
<Loading type="progress" progress={75} text="处理进度" />

// 全屏加载
<Loading type="dots" fullscreen={true} text="页面加载中" />
  `,
  
  ErrorBoundary: `
import { ErrorBoundary } from './UnifiedComponentLibrary';

// 基础使用
<ErrorBoundary>
  <YourComponent />
</ErrorBoundary>

// 自定义回退界面
<ErrorBoundary 
  fallback={
    <div>
      <h3>组件加载失败</h3>
      <button onClick={resetError}>重试</button>
    </div>
  }
  onError={(error, errorInfo) => {
    console.error('组件错误:', error, errorInfo);
  }}
>
  <YourComponent />
</ErrorBoundary>
  `
};

// 版本信息
export const version = '1.0.0';
export const buildDate = '2025-03-18';

// 默认导出整个组件库 - 暂时移除，因为变量未定义
// export default {
//   // Core 组件
//   Button,
//   Modal,
//   Loading,
//   ErrorBoundary,
//   
//   // 设计系统
//   designTokens,
//   
//   // 工具函数
//   // ...
//   
//   // 元信息
//   version,
//   buildDate,
//   usageExamples,
// };