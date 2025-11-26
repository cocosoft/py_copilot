import React from 'react';
import ModelCategoryManagement from '../components/ModelCategoryManagement';
import './ModelCategoryManagementPage.css';

const ModelCategoryManagementPage = () => {
  return (
    <div className="model-category-management-page">
      <header className="page-header">
        <p>管理和维护AI模型的分类体系，支持多级分类结构</p>
      </header>
      
      <main className="page-content">
        <ModelCategoryManagement />
      </main>
    </div>
  );
};

export default ModelCategoryManagementPage;