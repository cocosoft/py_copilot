import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import Loading from '../components/Common/Loading';
import { knowledgeRoutes } from './knowledgeRoutes';

const Home = lazy(() => import('../pages/Home'));
const Chat = lazy(() => import('../pages/Chat'));
const AgentManagement = lazy(() => import('../pages/AgentManagement'));
const Image = lazy(() => import('../pages/Image'));
const Video = lazy(() => import('../pages/Video'));
const Voice = lazy(() => import('../pages/Voice'));
const Translate = lazy(() => import('../pages/Translate'));
const Knowledge = lazy(() => import('../pages/Knowledge'));
const Workflow = lazy(() => import('../pages/Workflow'));
const Tool = lazy(() => import('../pages/Tool'));
const Task = lazy(() => import('../pages/Task'));
const Settings = lazy(() => import('../pages/Settings'));
const PersonalCenter = lazy(() => import('../pages/PersonalCenter'));
const HelpCenter = lazy(() => import('../pages/HelpCenter'));
const ModelSelectDropdownTest = lazy(() => import('../pages/ModelSelectDropdownTest'));
const CapabilityCenter = lazy(() => import('../pages/CapabilityCenter'));
const DevCenter = lazy(() => import('../pages/DevCenter'));

// 增强版知识库相关页面（向量化管理模块优化）
const EnhancedKnowledge = lazy(() => import('../pages/knowledge/EnhancedKnowledge'));
const EnhancedVectorization = lazy(() => import('../pages/knowledge/EnhancedVectorization'));
const EnhancedKnowledgeGraph = lazy(() => import('../pages/knowledge/EnhancedKnowledgeGraph'));

/**
 * 重定向组件：将旧路由重定向到能力中心
 * @param {string} type - 能力类型筛选
 * @param {string} category - 分类筛选
 */
const RedirectToCapabilityCenter = ({ type, category }) => {
  const searchParams = new URLSearchParams();
  if (type) searchParams.set('type', type);
  if (category) searchParams.set('category', category);

  const to = {
    pathname: '/capability-center',
    search: searchParams.toString() ? `?${searchParams.toString()}` : ''
  };

  // eslint-disable-next-line no-console
  console.warn(`路由 ${window.location.pathname} 已废弃，请使用 /capability-center`);

  return <Navigate to={to} replace />;
};

const AppRoutes = () => {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route index element={<Home />} />
        <Route path="chat" element={<Chat />} />
        <Route path="agents" element={<AgentManagement />} />
        <Route path="image" element={<Image />} />
        <Route path="video" element={<Video />} />
        <Route path="voice" element={<Voice />} />
        <Route path="translate" element={<Translate />} />
        {/* 新版知识库路由 - 使用嵌套路由 */}
        <Route path={knowledgeRoutes.path} element={knowledgeRoutes.element}>
          {knowledgeRoutes.children.map((child, index) => (
            <Route
              key={index}
              index={child.index}
              path={child.path}
              element={child.element}
            />
          ))}
        </Route>
        
        {/* 旧版知识库页面 - 保持兼容 */}
        <Route path="knowledge-old" element={<Knowledge />} />
        
        {/* 增强版知识库页面（向量化管理模块优化） */}
        <Route path="knowledge/enhanced" element={<EnhancedKnowledge />} />
        <Route path="knowledge/vectorization" element={<EnhancedVectorization />} />
        <Route path="knowledge/graph" element={<EnhancedKnowledgeGraph />} />
        <Route path="workflow" element={<Workflow />} />

        {/* 废弃路由重定向 - 请使用能力中心 */}
        <Route
          path="tool"
          element={<RedirectToCapabilityCenter type="tool" />}
        />
        <Route
          path="settings/search"
          element={<RedirectToCapabilityCenter type="tool" category="search" />}
        />
        <Route
          path="settings/skills"
          element={<RedirectToCapabilityCenter type="skill" />}
        />

        <Route path="task" element={<Task />} />
        <Route path="settings" element={<Settings />} />
        <Route path="personal/*" element={<PersonalCenter />} />
        <Route path="help/*" element={<HelpCenter />} />
        <Route path="model-select-test" element={<ModelSelectDropdownTest />} />
        <Route path="capability-center" element={<CapabilityCenter />} />
        <Route path="dev-center" element={<DevCenter />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;
