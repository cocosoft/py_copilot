# 前端构建性能优化策略

本文档描述了前端项目的构建性能优化策略，包括Vite配置优化、代码分割、资源优化等方面。

## 1. Vite配置优化

### 1.1 构建配置

- **代码分割**：使用`manualChunks`策略将第三方依赖和核心库分离，减少主包体积
- **压缩优化**：使用Terser进行代码压缩，移除console和debugger
- **CSS分割**：启用CSS代码分割，避免重复CSS
- **持久化缓存**：启用`cacheDir`，加快二次构建速度
- **构建分析**：使用`rollup-plugin-visualizer`生成构建分析报告

### 1.2 开发服务器优化

- **热模块替换**：启用HMR，提高开发体验
- **文件监听**：优化文件监听配置，减少不必要的重新构建
- **依赖预构建**：预构建常用依赖，加快启动速度
- **代理配置**：优化代理设置，支持流式响应

### 1.3 路径别名

配置了以下路径别名，简化导入路径：

- `@`: 指向src目录
- `@components`: 指向src/components目录
- `@pages`: 指向src/pages目录
- `@services`: 指向src/services目录
- `@utils`: 指向src/utils目录
- `@stores`: 指向src/stores目录
- `@hooks`: 指向src/hooks目录
- `@assets`: 指向src/assets目录
- `@contexts`: 指向src/contexts目录

## 2. 代码分割策略

### 2.1 第三方依赖分割

将第三方依赖分为以下几个chunk：

- **react-vendor**：React核心库（react, react-dom, react-router-dom）
- **ui-vendor**：UI库（framer-motion, reactflow）
- **utils-vendor**：工具库（axios, classnames）
- **charts-vendor**：图表库（d3）
- **pdf-vendor**：PDF处理（pdfjs-dist）
- **markdown-vendor**：Markdown渲染（react-markdown, remark系列, rehype系列）
- **state-vendor**：状态管理（zustand, @tanstack/react-query）
- **i18n-vendor**：国际化（i18next, react-i18next）
- **icons-vendor**：图标库（react-icons）

### 2.2 动态导入

对于大型组件和页面，建议使用动态导入：

```jsx
// 动态导入组件
const HeavyComponent = React.lazy(() => import('@components/HeavyComponent'));

// 动态导入页面
const Dashboard = React.lazy(() => import('@pages/Dashboard'));
```

## 3. 资源优化

### 3.1 图片优化

- 使用适当的图片格式（WebP优先）
- 压缩图片大小
- 使用懒加载
- 考虑使用CDN

### 3.2 字体优化

- 使用现代字体格式（WOFF2优先）
- 字体子集化
- 字体预加载

### 3.3 CSS优化

- 使用CSS变量
- 避免过度嵌套
- 减少CSS文件大小
- 考虑使用CSS-in-JS或CSS模块

## 4. 性能监控

### 4.1 构建分析

运行以下命令生成构建分析报告：

```bash
npm run build
```

报告将生成在`dist/stats.html`文件中，包含：

- 各chunk大小
- 依赖关系
- gzip和brotli压缩后的大小

### 4.2 性能指标

关注以下性能指标：

- **首次内容绘制（FCP）**：页面开始显示内容的时间
- **最大内容绘制（LCP）**：页面主要内容完成绘制的时间
- **累积布局偏移（CLS）**：页面元素意外移动的程度
- **首次输入延迟（FID）**：用户首次交互到浏览器响应的时间
- **最大输入延迟（Max FID）**：所有用户交互中最长的响应时间

## 5. 优化建议

### 5.1 代码层面

- **减少Bundle大小**：移除未使用的代码，使用tree-shaking
- **优化组件渲染**：使用React.memo, useMemo, useCallback
- **减少重渲染**：优化状态管理，避免不必要的状态更新
- **合理使用hooks**：避免在渲染过程中创建新函数和对象

### 5.2 资源层面

- **懒加载**：对非关键资源使用懒加载
- **预加载**：对关键资源使用预加载
- **缓存策略**：合理设置缓存策略，减少重复请求
- **CDN使用**：考虑使用CDN加速静态资源

### 5.3 构建层面

- **持续优化**：定期分析构建报告，识别优化机会
- **依赖管理**：定期更新依赖，移除未使用的依赖
- **构建缓存**：利用CI/CD中的构建缓存，加快构建速度

## 6. 构建命令

### 6.1 开发环境

```bash
npm run dev
```

### 6.2 生产构建

```bash
npm run build
```

### 6.3 预览生产构建

```bash
npm run preview
```

## 7. 常见问题

### 7.1 构建速度慢

- 检查依赖是否过多
- 确保启用了持久化缓存
- 检查文件监听配置

### 7.2 包体积过大

- 检查是否有未使用的依赖
- 分析构建报告，识别大型chunk
- 考虑进一步的代码分割

### 7.3 热更新不生效

- 检查HMR配置
- 确保文件监听正确设置
- 检查网络连接

## 8. 最佳实践

1. **定期分析**：定期运行构建分析，识别优化机会
2. **渐进式优化**：小步快跑，逐步优化性能
3. **监控指标**：持续监控性能指标，确保优化效果
4. **团队协作**：建立性能优化规范，团队成员共同遵守
5. **持续集成**：在CI/CD中添加性能检查，防止性能回归

## 9. 参考资料

- [Vite官方文档](https://vitejs.dev/)
- [Web性能优化指南](https://web.dev/performance/)
- [React性能优化](https://react.dev/learn/optimizing-performance)
- [Lighthouse性能审计](https://developers.google.com/web/tools/lighthouse)