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
const UnifiedKnowledgeGraph = lazy(() => import('../pages/knowledge/KnowledgeGraph/UnifiedKnowledgeGraph'));
const VectorizationManagement = lazy(() => import('../pages/knowledge/VectorizationManagement'));
const AdvancedSearch = lazy(() => import('../pages/knowledge/AdvancedSearch'));
const KnowledgeSettings = lazy(() => import('../pages/knowledge/KnowledgeSettings'));
const EntityManagement = lazy(() => import('../pages/knowledge/EntityManagement.jsx'));
const DataDashboard = lazy(() => import('../pages/knowledge/DataDashboard'));
const Reranking = lazy(() => import('../pages/knowledge/Reranking'));

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
 * 
 * 按照实施方案中的顺序组织功能模块：
 * 文档管理-向量化-实体识别-实体关系管理-知识图谱-重排序-高级搜索-设置
 */
export const knowledgeRoutes = {
  path: 'knowledge',
  element: withSuspense(KnowledgeLayout),
  children: [
    {
      index: true,
      element: <Navigate to="documents" replace />,
    },
    // 1. 文档管理
    {
      path: 'documents',
      element: withSuspense(DocumentManagement),
    },
    {
      path: 'documents/:documentId',
      element: withSuspense(DocumentManagement),
    },
    // 2. 向量化
    {
      path: 'vectorization',
      element: withSuspense(VectorizationManagement),
    },
    // 3. 实体管理（整合实体识别和实体关系）
    {
      path: 'entity-management',
      element: withSuspense(EntityManagement),
    },
    // 5. 知识图谱
    {
      path: 'knowledge-graph',
      element: withSuspense(UnifiedKnowledgeGraph),
    },
    // 6. 重排序
    {
      path: 'reranking',
      element: withSuspense(Reranking),
    },
    // 7. 高级搜索
    {
      path: 'search',
      element: withSuspense(AdvancedSearch),
    },
    // 8. 数据可视化
    {
      path: 'dashboard',
      element: withSuspense(DataDashboard),
    },
    // 9. 设置
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
