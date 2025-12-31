import { Routes, Route } from 'react-router-dom';
import Home from '../pages/Home';
import Chat from '../pages/Chat';
import Agent from '../pages/Agent';
import Image from '../pages/Image';
import Video from '../pages/Video';
import Voice from '../pages/Voice';
import Translate from '../pages/Translate';
import Knowledge from '../pages/Knowledge';
import Workflow from '../pages/Workflow';
import Tool from '../pages/Tool';
import Settings from '../pages/Settings';
import PersonalCenter from '../pages/PersonalCenter';
import HelpCenter from '../pages/HelpCenter';

const AppRoutes = () => {
  return (
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
      <Route path="settings" element={<Settings />} />
      <Route path="personal">
        <Route index element={<PersonalCenter />} />
        <Route path="*" element={<PersonalCenter />} />
      </Route>
      <Route path="help">
        <Route index element={<HelpCenter />} />
        <Route path="*" element={<HelpCenter />} />
      </Route>
    </Routes>
  );
};

export default AppRoutes;
