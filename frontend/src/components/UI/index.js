// UI组件库入口文件

// 基础组件
export { default as Button } from './Button';
export { default as Input } from './Input';
export { default as Card } from './Card';
export { default as Loading } from './Loading';
export { default as ErrorBoundary } from './ErrorBoundary';
export { default as Responsive } from './Responsive';
export { default as Toast, ToastContainer, showToast, showSuccess, showError, showWarning, showInfo } from './Toast';
export { default as Badge } from './Badge';
export { default as Select } from './Select';
export { default as Modal } from './Modal';
export { default as Icon } from './Icon';

// 工具函数和常量
export * from './utils';

// 设计系统变量
export const designTokens = {
  colors: {
    primary: {
      50: 'var(--ui-color-primary-50)',
      100: 'var(--ui-color-primary-100)',
      200: 'var(--ui-color-primary-200)',
      300: 'var(--ui-color-primary-300)',
      400: 'var(--ui-color-primary-400)',
      500: 'var(--ui-color-primary-500)',
      600: 'var(--ui-color-primary-600)',
      700: 'var(--ui-color-primary-700)',
      800: 'var(--ui-color-primary-800)',
      900: 'var(--ui-color-primary-900)',
    },
    gray: {
      50: 'var(--ui-color-gray-50)',
      100: 'var(--ui-color-gray-100)',
      200: 'var(--ui-color-gray-200)',
      300: 'var(--ui-color-gray-300)',
      400: 'var(--ui-color-gray-400)',
      500: 'var(--ui-color-gray-500)',
      600: 'var(--ui-color-gray-600)',
      700: 'var(--ui-color-gray-700)',
      800: 'var(--ui-color-gray-800)',
      900: 'var(--ui-color-gray-900)',
    },
    success: {
      500: 'var(--ui-color-success-500)',
      600: 'var(--ui-color-success-600)',
    },
    warning: {
      500: 'var(--ui-color-warning-500)',
      600: 'var(--ui-color-warning-600)',
    },
    danger: {
      500: 'var(--ui-color-danger-500)',
      600: 'var(--ui-color-danger-600)',
    },
    white: 'var(--ui-color-white)',
    black: 'var(--ui-color-black)',
  },
  shadows: {
    sm: 'var(--ui-shadow-sm)',
    md: 'var(--ui-shadow-md)',
    lg: 'var(--ui-shadow-lg)',
    xl: 'var(--ui-shadow-xl)',
  },
  radii: {
    sm: 'var(--ui-radius-sm)',
    md: 'var(--ui-radius-md)',
    lg: 'var(--ui-radius-lg)',
    xl: 'var(--ui-radius-xl)',
    full: 'var(--ui-radius-full)',
  },
  space: {
    1: 'var(--ui-space-1)',
    2: 'var(--ui-space-2)',
    3: 'var(--ui-space-3)',
    4: 'var(--ui-space-4)',
    5: 'var(--ui-space-5)',
    6: 'var(--ui-space-6)',
    8: 'var(--ui-space-8)',
    10: 'var(--ui-space-10)',
    12: 'var(--ui-space-12)',
    16: 'var(--ui-space-16)',
  },
  fontSizes: {
    xs: 'var(--ui-font-size-xs)',
    sm: 'var(--ui-font-size-sm)',
    base: 'var(--ui-font-size-base)',
    lg: 'var(--ui-font-size-lg)',
    xl: 'var(--ui-font-size-xl)',
    '2xl': 'var(--ui-font-size-2xl)',
    '3xl': 'var(--ui-font-size-3xl)',
    '4xl': 'var(--ui-font-size-4xl)',
  },
  fontWeights: {
    normal: 'var(--ui-font-weight-normal)',
    medium: 'var(--ui-font-weight-medium)',
    semibold: 'var(--ui-font-weight-semibold)',
    bold: 'var(--ui-font-weight-bold)',
  },
  lineHeights: {
    tight: 'var(--ui-line-height-tight)',
    normal: 'var(--ui-line-height-normal)',
    relaxed: 'var(--ui-line-height-relaxed)',
  },
  transitions: {
    fast: 'var(--ui-transition-fast)',
    normal: 'var(--ui-transition-normal)',
    slow: 'var(--ui-transition-slow)',
  },
  zIndices: {
    dropdown: 'var(--ui-z-index-dropdown)',
    sticky: 'var(--ui-z-index-sticky)',
    modal: 'var(--ui-z-index-modal)',
    popover: 'var(--ui-z-index-popover)',
    tooltip: 'var(--ui-z-index-tooltip)',
    toast: 'var(--ui-z-index-toast)',
  },
};

// 组件使用示例
export const usageExamples = {
  Button: `
import { Button } from './components/UI';

// 基础使用
<Button variant="primary" size="medium">
  点击我
</Button>

// 带图标和加载状态
<Button 
  variant="success" 
  size="large" 
  icon="✓" 
  loading={true}
>
  保存
</Button>
  `,
  
  Input: `
import { Input } from './components/UI';

// 基础输入框
<Input 
  placeholder="请输入内容"
  value={value}
  onChange={(e) => setValue(e.target.value)}
/>

// 带图标和状态
<Input 
  icon="🔍"
  placeholder="搜索..."
  error={hasError}
  loading={isLoading}
/>
  `,
  
  Card: `
import { Card } from './components/UI';

// 基础卡片
<Card variant="default" padding="normal">
  <Card.Header>
    <Card.Title>卡片标题</Card.Title>
  </Card.Header>
  <Card.Content>
    <p>卡片内容</p>
  </Card.Content>
  <Card.Footer>
    <Button variant="outline">操作</Button>
  </Card.Footer>
</Card>
  `,
};