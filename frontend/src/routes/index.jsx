import { Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import Loading from '../components/Common/Loading';

const Home = lazy(() => import('../pages/Home'));
const Chat = lazy(() => import('../pages/Chat'));
const Agent = lazy(() => import('../pages/Agent'));
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

const AppRoutes = () => {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route index element={<Home />} />
        <Route path="chat" element={<Chat />} />
        <Route path="agents" element={<Agent />} />
        <Route path="image" element={<Image />} />
        <Route path="video" element={<Video />} />
        <Route path="voice" element={<Voice />} />
        <Route path="translate" element={<Translate />} />
        <Route path="knowledge" element={<Knowledge />} />
        <Route path="workflow" element={<Workflow />} />
        <Route path="tool" element={<Tool />} />
        <Route path="task" element={<Task />} />
        <Route path="settings" element={<Settings />} />
        <Route path="personal/*" element={<PersonalCenter />} />
        <Route path="help/*" element={<HelpCenter />} />
        <Route path="model-select-test" element={<ModelSelectDropdownTest />} />
      </Routes>
    </Suspense>
  );
};

export default AppRoutes;
