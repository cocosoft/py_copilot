# 搜索管理页面精简开发计划

## 一、项目概述

本计划旨在完成Py Copilot应用中“搜索管理”页面的精简版前后端开发，仅实现大模型调用所需的核心搜索配置功能，确保功能够用且大模型能够正常调用。

## 二、核心需求分析

### 2.1 核心功能需求

搜索管理作为系统中的一个配置模块，用于后续大模型调用，仅需要以下核心功能：
- 搜索设置配置（基础搜索引擎和过滤选项）
- 语义搜索参数配置（用于大模型调用的关键参数）
- 确保配置能够被大模型正确调用

### 2.2 精简内容

根据需求，以下功能将被精简或移除：
- 复杂的同义词管理界面（可由系统自动维护或后续按需添加）
- 详细的搜索权重配置界面（可使用默认权重或通过API调整）
- 复杂的前端交互和UI设计（保持简洁实用）

## 三、后端开发计划

### 3.1 数据库模型设计

#### 3.1.1 SearchSetting 模型

仅保留一个核心模型，包含所有搜索配置：

```python
# backend/app/modules/knowledge/models/search_settings.py
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class SearchSetting(Base):
    """搜索设置模型"""
    __tablename__ = "search_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # nullable=True表示全局设置
    default_search_engine = Column(String(50), default="google")
    safe_search = Column(Boolean, default=True)
    # 语义搜索参数（大模型调用关键参数）
    use_entities = Column(Boolean, default=True)
    use_synonyms = Column(Boolean, default=True)
    boost_recent = Column(Boolean, default=True)
    semantic_boost = Column(Float, default=0.3)
    # 搜索权重参数（默认值，可通过API调整）
    entity_match = Column(Float, default=1.5)
    concept_similarity = Column(Float, default=1.3)
    context_relevance = Column(Float, default=1.2)
    recency_boost_weight = Column(Float, default=1.1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 3.2 API端点设计

仅提供核心的搜索设置管理接口：

| HTTP方法 | 端点 | 功能描述 |
|---------|------|---------|
| GET | /api/v1/knowledge/search-settings | 获取搜索设置 |
| PUT | /api/v1/knowledge/search-settings | 更新搜索设置 |

### 3.3 服务层实现

简化服务层，仅提供基本的CRUD操作：

```python
# backend/app/modules/knowledge/services/search_management_service.py
from sqlalchemy.orm import Session
from typing import Optional
from app.modules.knowledge.models.search_settings import SearchSetting

class SearchManagementService:
    """搜索管理服务"""
    
    def get_search_settings(self, db: Session, user_id: Optional[int] = None) -> Optional[SearchSetting]:
        """获取搜索设置"""
        if user_id:
            return db.query(SearchSetting).filter(
                (SearchSetting.user_id == user_id) | (SearchSetting.user_id.is_(None))
            ).order_by(SearchSetting.user_id.desc()).first()
        return db.query(SearchSetting).filter(SearchSetting.user_id.is_(None)).first()
    
    def update_search_settings(self, db: Session, settings_data: dict, user_id: Optional[int] = None) -> SearchSetting:
        """更新搜索设置"""
        settings = self.get_search_settings(db, user_id)
        if not settings:
            settings = SearchSetting(user_id=user_id, **settings_data)
            db.add(settings)
        else:
            for key, value in settings_data.items():
                setattr(settings, key, value)
        db.commit()
        db.refresh(settings)
        return settings
```

### 3.4 API接口实现

简化API接口，仅提供基本的获取和更新功能：

```python
# backend/app/modules/knowledge/api/search_management.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.modules.knowledge.services.search_management_service import SearchManagementService
from app.modules.knowledge.schemas.search_settings import (
    SearchSettingResponse,
    SearchSettingUpdate
)

router = APIRouter(prefix="/search-settings", tags=["搜索管理"])

# 初始化服务
search_management_service = SearchManagementService()

@router.get("", response_model=SearchSettingResponse)
async def get_search_settings(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取搜索设置"""
    settings = search_management_service.get_search_settings(db, user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="搜索设置不存在")
    return settings

@router.put("", response_model=SearchSettingResponse)
async def update_search_settings(
    settings_update: SearchSettingUpdate,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """更新搜索设置"""
    return search_management_service.update_search_settings(db, settings_update.dict(), user_id)
```

### 3.5 数据校验模式

简化数据校验模式，仅包含核心字段：

```python
# backend/app/modules/knowledge/schemas/search_settings.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SearchSettingBase(BaseModel):
    """搜索设置基础模式"""
    # 基础搜索设置
    default_search_engine: Optional[str] = "google"
    safe_search: Optional[bool] = True
    # 语义搜索参数（大模型调用关键参数）
    use_entities: Optional[bool] = True
    use_synonyms: Optional[bool] = True
    boost_recent: Optional[bool] = True
    semantic_boost: Optional[float] = Field(0.3, ge=0, le=1)
    # 搜索权重参数
    entity_match: Optional[float] = Field(1.5, ge=0, le=3)
    concept_similarity: Optional[float] = Field(1.3, ge=0, le=3)
    context_relevance: Optional[float] = Field(1.2, ge=0, le=3)
    recency_boost_weight: Optional[float] = Field(1.1, ge=0, le=3)

class SearchSettingUpdate(SearchSettingBase):
    """更新搜索设置模式"""
    pass

class SearchSettingResponse(SearchSettingBase):
    """搜索设置响应模式"""
    id: int
    user_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

### 3.6 文件结构

简化文件结构，减少不必要的文件：

```
backend/
└── app/
    └── modules/
        └── knowledge/
            ├── api/
            │   └── search_management.py   # API接口
            ├── models/
            │   └── search_settings.py      # 数据库模型
            ├── schemas/
            │   └── search_settings.py      # 数据校验
            └── services/
                └── search_management_service.py  # 服务层
```

## 四、前端开发计划

### 4.1 页面结构设计

在现有Settings.jsx页面的搜索管理部分，仅保留核心配置选项：

1. **基础搜索设置**
   - 默认搜索引擎选择
   - 安全搜索开关

2. **语义搜索参数（大模型调用关键参数）**
   - 实体匹配开关
   - 同义词扩展开关
   - 时效性提升开关
   - 语义提升权重滑块

### 4.2 集成到现有Settings页面

直接在Settings.jsx页面中实现搜索管理功能，不需要单独的组件：

```jsx
// frontend/src/pages/Settings.jsx
// 在activeSection === 'search'部分修改
case 'search':
  return (
    <div className="settings-content">
      <div className="content-header">
        <h2>搜索管理</h2>
        <p>配置搜索偏好和搜索引擎</p>
      </div>
      
      <div className="search-section">
        <div className="setting-card">
          <div className="setting-header">
            <h3>基础搜索设置</h3>
            <p>配置基础的搜索引擎和过滤选项</p>
          </div>
          <div className="search-settings">
            <div className="setting-item">
              <label htmlFor="default_search_engine">默认搜索引擎</label>
              <select 
                id="default_search_engine"
                value={searchSettings.default_search_engine}
                onChange={(e) => setSearchSettings(prev => ({
                  ...prev, 
                  default_search_engine: e.target.value
                }))}
              >
                <option value="google">Google</option>
                <option value="bing">Bing</option>
                <option value="duckduckgo">DuckDuckGo</option>
                <option value="baidu">百度</option>
              </select>
            </div>
            <div className="setting-item">
              <label htmlFor="safe_search">安全搜索</label>
              <input 
                type="checkbox" 
                id="safe_search" 
                checked={searchSettings.safe_search}
                onChange={(e) => setSearchSettings(prev => ({
                  ...prev, 
                  safe_search: e.target.checked
                }))}
              />
            </div>
          </div>
        </div>
        
        <div className="setting-card">
          <div className="setting-header">
            <h3>语义搜索参数</h3>
            <p>配置大模型调用的语义搜索参数</p>
          </div>
          <div className="semantic-settings">
            <div className="setting-item">
              <label htmlFor="use_entities">实体匹配</label>
              <input 
                type="checkbox" 
                id="use_entities" 
                checked={searchSettings.use_entities}
                onChange={(e) => setSearchSettings(prev => ({
                  ...prev, 
                  use_entities: e.target.checked
                }))}
              />
            </div>
            <div className="setting-item">
              <label htmlFor="use_synonyms">同义词扩展</label>
              <input 
                type="checkbox" 
                id="use_synonyms" 
                checked={searchSettings.use_synonyms}
                onChange={(e) => setSearchSettings(prev => ({
                  ...prev, 
                  use_synonyms: e.target.checked
                }))}
              />
            </div>
            <div className="setting-item">
              <label htmlFor="boost_recent">时效性提升</label>
              <input 
                type="checkbox" 
                id="boost_recent" 
                checked={searchSettings.boost_recent}
                onChange={(e) => setSearchSettings(prev => ({
                  ...prev, 
                  boost_recent: e.target.checked
                }))}
              />
            </div>
            <div className="setting-item">
              <label htmlFor="semantic_boost">语义提升权重 ({searchSettings.semantic_boost.toFixed(1)})</label>
              <input 
                type="range" 
                id="semantic_boost" 
                min="0" 
                max="1" 
                step="0.1"
                value={searchSettings.semantic_boost}
                onChange={(e) => setSearchSettings(prev => ({
                  ...prev, 
                  semantic_boost: parseFloat(e.target.value)
                }))}
              />
            </div>
          </div>
        </div>
        
        <div className="setting-actions">
          <button 
            className="save-btn" 
            onClick={handleSaveSettings}
            disabled={isSaving}
          >
            {isSaving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
```

### 4.3 API调用封装

简化API调用封装，仅提供基本的获取和更新功能：

```jsx
// frontend/src/services/searchManagementApi.js
import axios from 'axios';

// 搜索设置相关API
export const getSearchSettings = async (userId = null) => {
  const params = userId ? { user_id: userId } : {};
  const response = await axios.get('/api/v1/knowledge/search-settings', { params });
  return response.data;
};

export const updateSearchSettings = async (settings, userId = null) => {
  const params = userId ? { user_id: userId } : {};
  const response = await axios.put('/api/v1/knowledge/search-settings', settings, { params });
  return response.data;
};
```

### 4.4 状态管理

在Settings.jsx中直接管理搜索设置的状态：

```jsx
// frontend/src/pages/Settings.jsx
// 添加以下状态和方法
const [searchSettings, setSearchSettings] = useState({
  default_search_engine: 'google',
  safe_search: true,
  use_entities: true,
  use_synonyms: true,
  boost_recent: true,
  semantic_boost: 0.3,
  entity_match: 1.5,
  concept_similarity: 1.3,
  context_relevance: 1.2,
  recency_boost_weight: 1.1
});

const [isSaving, setIsSaving] = useState(false);

// 获取搜索设置
useEffect(() => {
  const fetchSearchSettings = async () => {
    try {
      const settings = await getSearchSettings();
      setSearchSettings(settings);
    } catch (error) {
      console.error('获取搜索设置失败:', error);
    }
  };
  
  fetchSearchSettings();
}, []);

// 保存搜索设置
const handleSaveSettings = async () => {
  setIsSaving(true);
  try {
    await updateSearchSettings(searchSettings);
    alert('搜索设置已保存');
  } catch (error) {
    console.error('保存搜索设置失败:', error);
    alert('保存失败，请重试');
  } finally {
    setIsSaving(false);
  }
};
```

## 五、前后端交互设计

### 5.1 API调用流程

1. **页面加载时**：
   - 调用`GET /api/v1/knowledge/search-settings`获取搜索设置

2. **设置保存时**：
   - 调用`PUT /api/v1/knowledge/search-settings`更新搜索设置

### 5.2 数据格式

```json
{
  "id": 1,
  "user_id": null,
  "default_search_engine": "google",
  "safe_search": true,
  "use_entities": true,
  "use_synonyms": true,
  "boost_recent": true,
  "semantic_boost": 0.3,
  "entity_match": 1.5,
  "concept_similarity": 1.3,
  "context_relevance": 1.2,
  "recency_boost_weight": 1.1,
  "created_at": "2025-12-19T10:00:00Z",
  "updated_at": "2025-12-19T10:00:00Z"
}
```

## 六、大模型调用集成

### 6.1 大模型调用搜索配置

在大模型调用的相关服务中，直接使用搜索配置：

```python
# backend/app/services/llm_service.py
from app.modules.knowledge.services.search_management_service import SearchManagementService

class LLMService:
    """大模型服务"""
    
    def __init__(self):
        self.search_management_service = SearchManagementService()
    
    def generate_response(self, query: str, user_id: Optional[int] = None):
        """生成大模型响应"""
        # 获取搜索配置
        search_settings = self.search_management_service.get_search_settings(db, user_id)
        
        # 使用搜索配置调用语义搜索服务
        search_results = semantic_search_service.semantic_search(
            query=query,
            use_entities=search_settings.use_entities,
            use_synonyms=search_settings.use_synonyms,
            boost_recent=search_settings.boost_recent,
            semantic_boost=search_settings.semantic_boost
        )
        
        # 使用搜索结果生成大模型响应
        # ...
```

## 七、测试计划

### 7.1 后端测试

仅测试核心功能：
- 搜索设置的获取和更新功能
- 大模型调用搜索配置的正确性

### 7.2 前端测试

仅测试基本功能：
- 页面显示的正确性
- 设置保存的功能

## 八、开发时间表

| 阶段 | 时间 | 任务 |
|------|------|------|
| 后端开发 | 1天 | 数据库模型、API接口、服务层实现 |
| 前端开发 | 1天 | 集成到现有Settings页面 |
| 前后端联调 | 0.5天 | 实现前后端交互 |
| 测试 | 0.5天 | 功能测试和大模型调用测试 |

总计：3天

## 九、风险评估

1. **功能精简风险**：
   - 可能缺少未来扩展所需的功能
   - 解决方案：保留扩展的可能性，后续可按需添加功能

2. **大模型调用风险**：
   - 搜索配置可能不满足大模型调用的需求
   - 解决方案：与大模型开发团队密切合作，确保配置满足需求

## 十、总结

本精简版开发计划仅实现搜索管理的核心功能，确保大模型能够正常调用搜索配置。通过精简不必要的功能和设计，减少了开发时间和复杂度，同时满足了核心需求。后续可根据实际需求，逐步扩展搜索管理的功能。