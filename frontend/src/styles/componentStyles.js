/**
 * 组件样式规范
 * 
 * 定义前端组件的设计系统、样式规范和最佳实践
 * 
 * 任务编号: Phase1-Week3
 * 阶段: 第一阶段 - 功能重复问题优化
 */

// 设计令牌
export const designTokens = {
  colors: {
    primary: {
      50: '#f0f9ff',
      100: '#e0f2fe',
      200: '#bae6fd',
      300: '#7dd3fc',
      400: '#38bdf8',
      500: '#0ea5e9',
      600: '#0284c7',
      700: '#0369a1',
      800: '#075985',
      900: '#0c4a6e',
    },
    secondary: {
      50: '#f8fafc',
      100: '#f1f5f9',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
    },
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      300: '#86efac',
      400: '#4ade80',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      800: '#166534',
      900: '#14532d',
    },
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f',
    },
    danger: {
      50: '#fef2f2',
      100: '#fee2e2',
      200: '#fecaca',
      300: '#fca5a5',
      400: '#f87171',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
      800: '#991b1b',
      900: '#7f1d1d',
    },
    info: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
  },
  
  spacing: {
    0: '0',
    1: '4px',
    2: '8px',
    3: '12px',
    4: '16px',
    5: '20px',
    6: '24px',
    8: '32px',
    10: '40px',
    12: '48px',
    16: '64px',
    20: '80px',
    24: '96px',
  },
  
  borderRadius: {
    none: '0',
    sm: '2px',
    md: '4px',
    lg: '8px',
    xl: '12px',
    '2xl': '16px',
    '3xl': '24px',
    full: '9999px',
  },
  
  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  },
  
  typography: {
    fontFamily: {
      sans: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      serif: 'ui-serif, Georgia, Cambria, "Times New Roman", Times, serif',
      mono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem',
      '6xl': '3.75rem',
    },
    fontWeight: {
      thin: '100',
      extralight: '200',
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800',
      black: '900',
    },
    lineHeight: {
      none: '1',
      tight: '1.25',
      snug: '1.375',
      normal: '1.5',
      relaxed: '1.625',
      loose: '2',
    },
  },
  
  transitions: {
    none: 'none',
    all: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    colors: 'color, background-color, border-color, fill, stroke 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    opacity: 'opacity 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    shadow: 'box-shadow 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    transform: 'transform 150ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
  
  zIndex: {
    0: '0',
    10: '10',
    20: '20',
    30: '30',
    40: '40',
    50: '50',
    dropdown: '1000',
    sticky: '1020',
    fixed: '1030',
    modalBackdrop: '1040',
    modal: '1050',
    popover: '1060',
    tooltip: '1070',
  },
};

// 组件样式变体
export const componentVariants = {
  Button: {
    variants: ['primary', 'secondary', 'success', 'warning', 'danger', 'outline', 'ghost', 'link'],
    sizes: ['xs', 'sm', 'md', 'lg', 'xl'],
    shapes: ['default', 'rounded', 'circle', 'square'],
  },
  
  Input: {
    variants: ['default', 'filled', 'flushed', 'unstyled'],
    sizes: ['sm', 'md', 'lg'],
    states: ['default', 'hover', 'focus', 'disabled', 'error', 'success'],
  },
  
  Card: {
    variants: ['default', 'outlined', 'elevated', 'filled'],
    padding: ['none', 'sm', 'md', 'lg'],
  },
  
  Modal: {
    sizes: ['sm', 'md', 'lg', 'xl', 'full'],
    positions: ['center', 'top', 'bottom'],
  },
  
  Table: {
    variants: ['default', 'striped', 'bordered'],
    sizes: ['sm', 'md', 'lg'],
  },
  
  Badge: {
    variants: ['solid', 'subtle', 'outline'],
    colors: ['primary', 'secondary', 'success', 'warning', 'danger', 'info'],
    sizes: ['sm', 'md', 'lg'],
  },
  
  Tag: {
    variants: ['default', 'closable', 'checkable'],
    colors: ['default', 'primary', 'success', 'warning', 'danger', 'info'],
  },
  
  Tooltip: {
    placements: ['top', 'right', 'bottom', 'left'],
    triggers: ['hover', 'click', 'focus'],
  },
  
  Dropdown: {
    placements: ['bottom-start', 'bottom-end', 'top-start', 'top-end'],
    sizes: ['sm', 'md', 'lg'],
  },
  
  Tabs: {
    variants: ['line', 'enclosed', 'filled', 'pills'],
    alignments: ['start', 'center', 'end', 'stretch'],
  },
  
  Alert: {
    variants: ['solid', 'subtle', 'left-accent', 'top-accent'],
    status: ['info', 'success', 'warning', 'error'],
  },
};

// 响应式断点
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// 媒体查询
export const mediaQueries = {
  sm: `@media (min-width: ${breakpoints.sm})`,
  md: `@media (min-width: ${breakpoints.md})`,
  lg: `@media (min-width: ${breakpoints.lg})`,
  xl: `@media (min-width: ${breakpoints.xl})`,
  '2xl': `@media (min-width: ${breakpoints['2xl']})`,
};

// 动画定义
export const animations = {
  fadeIn: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },
  fadeOut: {
    from: { opacity: 1 },
    to: { opacity: 0 },
  },
  slideInUp: {
    from: { transform: 'translateY(10px)', opacity: 0 },
    to: { transform: 'translateY(0)', opacity: 1 },
  },
  slideInDown: {
    from: { transform: 'translateY(-10px)', opacity: 0 },
    to: { transform: 'translateY(0)', opacity: 1 },
  },
  slideInLeft: {
    from: { transform: 'translateX(-10px)', opacity: 0 },
    to: { transform: 'translateX(0)', opacity: 1 },
  },
  slideInRight: {
    from: { transform: 'translateX(10px)', opacity: 0 },
    to: { transform: 'translateX(0)', opacity: 1 },
  },
  scaleIn: {
    from: { transform: 'scale(0.95)', opacity: 0 },
    to: { transform: 'scale(1)', opacity: 1 },
  },
  spin: {
    from: { transform: 'rotate(0deg)' },
    to: { transform: 'rotate(360deg)' },
  },
  pulse: {
    '0%, 100%': { opacity: 1 },
    '50%': { opacity: 0.5 },
  },
  bounce: {
    '0%, 100%': { transform: 'translateY(-5%)' },
    '50%': { transform: 'translateY(0)' },
  },
};

// CSS变量生成函数
export const generateCSSVariables = () => {
  const cssVars = {};
  
  Object.entries(designTokens.colors).forEach(([colorName, shades]) => {
    Object.entries(shades).forEach(([shade, value]) => {
      cssVars[`--color-${colorName}-${shade}`] = value;
    });
  });
  
  Object.entries(designTokens.spacing).forEach(([name, value]) => {
    cssVars[`--spacing-${name}`] = value;
  });
  
  Object.entries(designTokens.borderRadius).forEach(([name, value]) => {
    cssVars[`--radius-${name}`] = value;
  });
  
  Object.entries(designTokens.shadows).forEach(([name, value]) => {
    cssVars[`--shadow-${name}`] = value;
  });
  
  Object.entries(designTokens.typography.fontSize).forEach(([name, value]) => {
    cssVars[`--font-size-${name}`] = value;
  });
  
  return cssVars;
};

// 组件样式生成器
export const createComponentStyles = (componentName, variant, size) => {
  const baseStyles = {
    Button: {
      base: {
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: designTokens.typography.fontWeight.medium,
        transition: designTokens.transitions.all,
        cursor: 'pointer',
        outline: 'none',
      },
      variants: {
        primary: {
          backgroundColor: designTokens.colors.primary[500],
          color: '#ffffff',
          border: 'none',
          '&:hover': {
            backgroundColor: designTokens.colors.primary[600],
          },
        },
        secondary: {
          backgroundColor: designTokens.colors.secondary[100],
          color: designTokens.colors.secondary[700],
          border: 'none',
          '&:hover': {
            backgroundColor: designTokens.colors.secondary[200],
          },
        },
        outline: {
          backgroundColor: 'transparent',
          color: designTokens.colors.primary[500],
          border: `1px solid ${designTokens.colors.primary[500]}`,
          '&:hover': {
            backgroundColor: designTokens.colors.primary[50],
          },
        },
        ghost: {
          backgroundColor: 'transparent',
          color: designTokens.colors.gray[700],
          border: 'none',
          '&:hover': {
            backgroundColor: designTokens.colors.gray[100],
          },
        },
      },
      sizes: {
        sm: {
          padding: `${designTokens.spacing[1]} ${designTokens.spacing[3]}`,
          fontSize: designTokens.typography.fontSize.sm,
          borderRadius: designTokens.borderRadius.md,
        },
        md: {
          padding: `${designTokens.spacing[2]} ${designTokens.spacing[4]}`,
          fontSize: designTokens.typography.fontSize.base,
          borderRadius: designTokens.borderRadius.md,
        },
        lg: {
          padding: `${designTokens.spacing[3]} ${designTokens.spacing[6]}`,
          fontSize: designTokens.typography.fontSize.lg,
          borderRadius: designTokens.borderRadius.lg,
        },
      },
    },
    
    Card: {
      base: {
        backgroundColor: '#ffffff',
        borderRadius: designTokens.borderRadius.lg,
        overflow: 'hidden',
      },
      variants: {
        default: {
          boxShadow: designTokens.shadows.sm,
        },
        outlined: {
          border: `1px solid ${designTokens.colors.gray[200]}`,
        },
        elevated: {
          boxShadow: designTokens.shadows.lg,
        },
      },
      padding: {
        sm: { padding: designTokens.spacing[3] },
        md: { padding: designTokens.spacing[4] },
        lg: { padding: designTokens.spacing[6] },
      },
    },
    
    Input: {
      base: {
        width: '100%',
        transition: designTokens.transitions.colors,
        outline: 'none',
      },
      variants: {
        default: {
          backgroundColor: '#ffffff',
          border: `1px solid ${designTokens.colors.gray[300]}`,
          borderRadius: designTokens.borderRadius.md,
          '&:focus': {
            borderColor: designTokens.colors.primary[500],
            boxShadow: `0 0 0 3px ${designTokens.colors.primary[100]}`,
          },
        },
        filled: {
          backgroundColor: designTokens.colors.gray[100],
          border: 'none',
          borderRadius: designTokens.borderRadius.md,
          '&:focus': {
            backgroundColor: '#ffffff',
            boxShadow: `0 0 0 2px ${designTokens.colors.primary[500]}`,
          },
        },
      },
      sizes: {
        sm: {
          padding: `${designTokens.spacing[1]} ${designTokens.spacing[2]}`,
          fontSize: designTokens.typography.fontSize.sm,
        },
        md: {
          padding: `${designTokens.spacing[2]} ${designTokens.spacing[3]}`,
          fontSize: designTokens.typography.fontSize.base,
        },
        lg: {
          padding: `${designTokens.spacing[3]} ${designTokens.spacing[4]}`,
          fontSize: designTokens.typography.fontSize.lg,
        },
      },
    },
  };
  
  const componentStyles = baseStyles[componentName];
  if (!componentStyles) return {};
  
  return {
    ...componentStyles.base,
    ...(componentStyles.variants?.[variant] || {}),
    ...(componentStyles.sizes?.[size] || componentStyles.padding?.[size] || {}),
  };
};

// 导出所有样式规范
export default {
  designTokens,
  componentVariants,
  breakpoints,
  mediaQueries,
  animations,
  generateCSSVariables,
  createComponentStyles,
};
