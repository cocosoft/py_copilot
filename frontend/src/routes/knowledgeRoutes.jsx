/**
 * 知识库模块路由配置
 * 
 * 使用嵌套路由结构，支持懒加载
 */

import { lazy, Suspense } from 'react';
import { Navigate } from 'react-router-dom';

// 懒加载页面组件
const KnowledgeLayout = lazy(() => import('../layouts/KnowledgeLayout'));
const DocumentManagement = lazy(() => import('../pages/knowledge/DocumentManagement'));
const KnowledgeGraph = lazy(() => import('../pages/knowledge/KnowledgeGraph'));
const VectorizationManagement = lazy(() => import('../pages/knowledge/VectorizationManagement'));
const AdvancedSearch = lazy(() => import('../pages/knowledge/AdvancedSearch'));
const KnowledgeSettings = lazy(() => import('../pages/knowledge/KnowledgeSettings'));
const EntityRecognition = lazy(() => import('../pages/knowledge/EntityRecognition'));

/**
 * 页面加载占位符
 */
import { KnowledgePageSkeleton } from '../components/UI/PageSkeleton';

const PageSkeleton = () => <KnowledgePageSkeleton />;

/**
 * 带 Suspense 的组件包装器
 */
const withSuspense = (Component) => (
  <Suspense fallback={<PageSkeleton />}>
    <Component />
  </Suspense>
);

/**
 * 知识库路由配置
 */
export const knowledgeRoutes = {
  path: 'knowledge',
  element: withSuspense(KnowledgeLayout),
  children: [
    {
      index: true,
      element: <Navigate to="documents" replace />,
    },
    {
      path: 'documents',
      element: withSuspense(DocumentManagement),
    },
    {
      path: 'documents/:documentId',
      element: withSuspense(DocumentManagement),
    },
    {
      path: 'graph',
      element: withSuspense(KnowledgeGraph),
    },
    {
      path: 'vectorization',
      element: withSuspense(VectorizationManagement),
    },
    {
      path: 'entities',
      element: withSuspense(EntityRecognition),
    },
    {
      path: 'search',
      element: withSuspense(AdvancedSearch),
    },
    {
      path: 'settings',
      element: withSuspense(KnowledgeSettings),
    },
  ],
};

/**
 * 预加载知识库相关模块
 * 用于路由预加载优化
 */
export const prefetchKnowledge = () => {
  const imports = [
    import('../pages/knowledge/DocumentManagement'),
    import('../stores/knowledgeStore'),
  ];
  return Promise.all(imports);
};

export default knowledgeRoutes;
