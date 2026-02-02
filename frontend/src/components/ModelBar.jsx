import React from 'react';
import ModelSelectDropdown from './ModelManagement/ModelSelectDropdown';
import './ModelBar.css';

const ModelBar = ({ 
  models, 
  selectedModel, 
  onModelChange 
}) => {
  return (
    <div className="model-bar">
      <div className="model-bar-left">
        <div className="model-selector-wrapper">
          <label className="model-label">模型:</label>
          <ModelSelectDropdown
            models={models}
            selectedModel={selectedModel}
            onModelSelect={onModelChange}
            className="model-selector"
            placeholder="选择模型..."
          />
        </div>
      </div>
      
      <div className="model-bar-right">
        <div className="model-info">
          {selectedModel && (
            <>
              <img 
                src={(selectedModel.logo || selectedModel.supplier_logo) ? 
                  (selectedModel.logo ? 
                    (selectedModel.logo.startsWith('http') || selectedModel.logo.startsWith('/') ? 
                      selectedModel.logo : `/logos/models/${selectedModel.logo}`) : 
                    (selectedModel.supplier_logo.startsWith('http') || selectedModel.supplier_logo.startsWith('/') ? 
                      selectedModel.supplier_logo : `/logos/providers/${selectedModel.supplier_logo}`)) : 
                  '/logos/models/default.png'}
                alt={selectedModel.supplier_name || selectedModel.model_name}
                className="model-logo-small"
              />
              <span className="model-name">
                {selectedModel.model_name || selectedModel.name || '未知模型'}
              </span>
              <span className="supplier-name">
                {selectedModel.supplier_display_name || selectedModel.supplier_name || '未知供应商'}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModelBar;
