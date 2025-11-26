import React from 'react';
import ApiKeyUpdater from './components/ApiKeyUpdater';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Chat from './pages/Chat';
import Agent from './pages/Agent';
import Image from './pages/Image';
import Video from './pages/Video';
import Voice from './pages/Voice';
import Translate from './pages/Translate';
import Knowledge from './pages/Knowledge';
import Workflow from './pages/Workflow';
import Tool from './pages/Tool';
import Settings from './pages/Settings';

import ModelCapabilityManagement from './components/ModelCapabilityManagement';
import ModelCapabilityAssociation from './components/ModelCapabilityAssociation';

function App() {
  return (
    <Router>
      <div className="app-container">
        <ApiKeyUpdater />
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/agents" element={<Agent />} />
            <Route path="/image" element={<Image />} />
            <Route path="/video" element={<Video />} />
            <Route path="/voice" element={<Voice />} />
            <Route path="/translate" element={<Translate />} />
            <Route path="/knowledge" element={<Knowledge />} />
            <Route path="/workflow" element={<Workflow />} />
            <Route path="/tool" element={<Tool />} />
            <Route path="/settings" element={<Settings />} />
  
            <Route path="/model-capabilities" element={<ModelCapabilityManagement />} />
            <Route path="/model-capability-association" element={<ModelCapabilityAssociation />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;