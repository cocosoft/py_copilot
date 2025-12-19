# 搜索管理页面开发计划

## 一、项目概述

本计划旨在完成Py Copilot应用中“搜索管理”页面的前后端开发，实现搜索设置、同义词管理和搜索权重配置等功能，提升用户搜索体验和搜索结果质量。

## 二、功能需求分析

### 2.1 现有功能分析

现有搜索管理页面包含以下基本功能：
- 默认搜索引擎选择（Google、Bing、DuckDuckGo、百度）
- 搜索过滤设置（安全搜索、严格内容过滤、成人内容包含）
- 搜索历史管理（保存历史、历史保留时长、清空历史）

### 2.2 扩展功能需求

为提升搜索功能的灵活性和个性化，需要扩展以下功能：
- 语义搜索参数配置
- 同义词管理
- 搜索权重配置

## 三、后端开发计划

### 3.1 数据库模型设计

#### 3.1.1 SearchSetting 模型

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
    strict_filter = Column(Boolean, default=False)
    include_adult = Column(Boolean, default=False)
    save_history = Column(Boolean, default=True)
    history_duration = Column(Integer, default=90)  # 天
    use_entities = Column(Boolean, default=True)
    use_synonyms = Column(Boolean, default=True)
    boost_recent = Column(Boolean, default=True)
    semantic_boost = Column(Float, default=0.3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 3.1.2 SearchSynonym 模型

```python
# backend/app/modules/knowledge/models/search_settings.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import ARRAY
from app.models.base import Base

class SearchSynonym(Base):
    """同义词模型"""
    __tablename__ = "search_synonyms"
    
    id = Column(Integer, primary_key=True, index=True)
    term = Column(String(100), unique=True, index=True)
    synonyms = Column(MutableList.as_mutable(ARRAY(String)), default=[])
    is_global = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

#### 3.1.3 SearchWeight 模型

```python
# backend/app/modules/knowledge/models/search_settings.py
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base

class SearchWeight(Base):
    """搜索权重模型"""
    __tablename__ = "search_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # nullable=True表示全局设置
    entity_match = Column(Float, default=1.5)
    concept_similarity = Column(Float, default=1.3)
    context_relevance = Column(Float, default=1.2)
    recency_boost = Column(Float, default=1.1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 3.2 API端点设计

| HTTP方法 | 端点 | 功能描述 |
|---------|------|---------|
| GET | /api/v1/knowledge/search-settings | 获取搜索设置 |
| PUT | /api/v1/knowledge/search-settings | 更新搜索设置 |
| GET | /api/v1/knowledge/synonyms | 获取同义词列表 |
| POST | /api/v1/knowledge/synonyms | 添加同义词 |
| PUT | /api/v1/knowledge/synonyms/{id} | 更新同义词 |
| DELETE | /api/v1/knowledge/synonyms/{id} | 删除同义词 |
| GET | /api/v1/knowledge/search-weights | 获取搜索权重 |
| PUT | /api/v1/knowledge/search-weights | 更新搜索权重 |

### 3.3 服务层实现

```python
# backend/app/modules/knowledge/services/search_management_service.py
from sqlalchemy.orm import Session
from typing import List, Optional
from app.modules.knowledge.models.search_settings import (
    SearchSetting, SearchSynonym, SearchWeight
)

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
    
    def get_synonyms(self, db: Session, is_global: Optional[bool] = None) -> List[SearchSynonym]:
        """获取同义词列表"""
        query = db.query(SearchSynonym)
        if is_global is not None:
            query = query.filter(SearchSynonym.is_global == is_global)
        return query.all()
    
    def create_synonym(self, db: Session, term: str, synonyms: List[str], is_global: bool = True) -> SearchSynonym:
        """创建同义词"""
        synonym = SearchSynonym(term=term, synonyms=synonyms, is_global=is_global)
        db.add(synonym)
        db.commit()
        db.refresh(synonym)
        return synonym
    
    def update_synonym(self, db: Session, synonym_id: int, synonyms: List[str]) -> Optional[SearchSynonym]:
        """更新同义词"""
        synonym = db.query(SearchSynonym).filter(SearchSynonym.id == synonym_id).first()
        if synonym:
            synonym.synonyms = synonyms
            db.commit()
            db.refresh(synonym)
        return synonym
    
    def delete_synonym(self, db: Session, synonym_id: int) -> bool:
        """删除同义词"""
        synonym = db.query(SearchSynonym).filter(SearchSynonym.id == synonym_id).first()
        if synonym:
            db.delete(synonym)
            db.commit()
            return True
        return False
    
    def get_search_weights(self, db: Session, user_id: Optional[int] = None) -> Optional[SearchWeight]:
        """获取搜索权重"""
        if user_id:
            return db.query(SearchWeight).filter(
                (SearchWeight.user_id == user_id) | (SearchWeight.user_id.is_(None))
            ).order_by(SearchWeight.user_id.desc()).first()
        return db.query(SearchWeight).filter(SearchWeight.user_id.is_(None)).first()
    
    def update_search_weights(self, db: Session, weights_data: dict, user_id: Optional[int] = None) -> SearchWeight:
        """更新搜索权重"""
        weights = self.get_search_weights(db, user_id)
        if not weights:
            weights = SearchWeight(user_id=user_id, **weights_data)
            db.add(weights)
        else:
            for key, value in weights_data.items():
                setattr(weights, key, value)
        db.commit()
        db.refresh(weights)
        return weights
```

### 3.4 API接口实现

```python
# backend/app/modules/knowledge/api/search_management.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.modules.knowledge.services.search_management_service import SearchManagementService
from app.modules.knowledge.schemas.search_settings import (
    SearchSettingResponse,
    SearchSettingUpdate,
    SearchSynonymResponse,
    SearchSynonymCreate,
    SearchSynonymUpdate,
    SearchWeightResponse,
    SearchWeightUpdate
)

router = APIRouter(prefix="/search-management", tags=["搜索管理"])

# 初始化服务
search_management_service = SearchManagementService()

@router.get("/settings", response_model=SearchSettingResponse)
async def get_search_settings(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取搜索设置"""
    settings = search_management_service.get_search_settings(db, user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="搜索设置不存在")
    return settings

@router.put("/settings", response_model=SearchSettingResponse)
async def update_search_settings(
    settings_update: SearchSettingUpdate,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """更新搜索设置"""
    return search_management_service.update_search_settings(db, settings_update.dict(), user_id)

@router.get("/synonyms", response_model=List[SearchSynonymResponse])
async def get_synonyms(
    is_global: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """获取同义词列表"""
    return search_management_service.get_synonyms(db, is_global)

@router.post("/synonyms", response_model=SearchSynonymResponse)
async def create_synonym(
    synonym_create: SearchSynonymCreate,
    db: Session = Depends(get_db)
):
    """创建同义词"""
    return search_management_service.create_synonym(
        db, synonym_create.term, synonym_create.synonyms, synonym_create.is_global
    )

@router.put("/synonyms/{synonym_id}", response_model=SearchSynonymResponse)
async def update_synonym(
    synonym_id: int,
    synonym_update: SearchSynonymUpdate,
    db: Session = Depends(get_db)
):
    """更新同义词"""
    synonym = search_management_service.update_synonym(
        db, synonym_id, synonym_update.synonyms
    )
    if not synonym:
        raise HTTPException(status_code=404, detail="同义词不存在")
    return synonym

@router.delete("/synonyms/{synonym_id}")
async def delete_synonym(
    synonym_id: int,
    db: Session = Depends(get_db)
):
    """删除同义词"""
    success = search_management_service.delete_synonym(db, synonym_id)
    if not success:
        raise HTTPException(status_code=404, detail="同义词不存在")
    return {"message": "同义词已删除"}

@router.get("/weights", response_model=SearchWeightResponse)
async def get_search_weights(
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取搜索权重"""
    weights = search_management_service.get_search_weights(db, user_id)
    if not weights:
        raise HTTPException(status_code=404, detail="搜索权重不存在")
    return weights

@router.put("/weights", response_model=SearchWeightResponse)
async def update_search_weights(
    weights_update: SearchWeightUpdate,
    user_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """更新搜索权重"""
    return search_management_service.update_search_weights(db, weights_update.dict(), user_id)
```

### 3.5 数据校验模式

```python
# backend/app/modules/knowledge/schemas/search_settings.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SearchSettingBase(BaseModel):
    """搜索设置基础模式"""
    default_search_engine: Optional[str] = "google"
    safe_search: Optional[bool] = True
    strict_filter: Optional[bool] = False
    include_adult: Optional[bool] = False
    save_history: Optional[bool] = True
    history_duration: Optional[int] = Field(90, ge=1, le=365)
    use_entities: Optional[bool] = True
    use_synonyms: Optional[bool] = True
    boost_recent: Optional[bool] = True
    semantic_boost: Optional[float] = Field(0.3, ge=0, le=1)

class SearchSettingCreate(SearchSettingBase):
    """创建搜索设置模式"""
    pass

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

class SearchSynonymBase(BaseModel):
    """同义词基础模式"""
    term: str
    synonyms: List[str] = Field(..., min_items=1)
    is_global: bool = True

class SearchSynonymCreate(SearchSynonymBase):
    """创建同义词模式"""
    pass

class SearchSynonymUpdate(BaseModel):
    """更新同义词模式"""
    synonyms: List[str] = Field(..., min_items=1)

class SearchSynonymResponse(SearchSynonymBase):
    """同义词响应模式"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class SearchWeightBase(BaseModel):
    """搜索权重基础模式"""
    entity_match: float = Field(1.5, ge=0, le=3)
    concept_similarity: float = Field(1.3, ge=0, le=3)
    context_relevance: float = Field(1.2, ge=0, le=3)
    recency_boost: float = Field(1.1, ge=0, le=3)

class SearchWeightCreate(SearchWeightBase):
    """创建搜索权重模式"""
    pass

class SearchWeightUpdate(SearchWeightBase):
    """更新搜索权重模式"""
    pass

class SearchWeightResponse(SearchWeightBase):
    """搜索权重响应模式"""
    id: int
    user_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
```

### 3.6 文件结构

```
backend/
└── app/
    └── modules/
        └── knowledge/
            ├── api/
            │   ├── __init__.py
            │   └── search_management.py   # API接口
            ├── models/
            │   ├── __init__.py
            │   └── search_settings.py      # 数据库模型
            ├── schemas/
            │   ├── __init__.py
            │   └── search_settings.py      # 数据校验
            └── services/
                ├── __init__.py
                └── search_management_service.py  # 服务层
```

### 3.7 集成到现有系统

需要将搜索管理API注册到现有的API路由中：

```python
# backend/app/api/v1/__init__.py
# 在适当位置添加以下导入和注册
from app.modules.knowledge.api.search_management import router as search_management_router

# 注册到知识模块路由组
api_router.include_router(search_management_router, prefix="/knowledge", tags=["knowledge"])
```

## 四、前端开发计划

### 4.1 页面结构设计

在现有Settings.jsx页面的搜索管理部分（activeSection === 'search'）扩展以下功能区块：

1. **搜索引擎设置**（现有，保持不变）
   - 默认搜索引擎选择（Google、Bing、DuckDuckGo、百度）
   - 搜索过滤设置（安全搜索、严格内容过滤、成人内容包含）

2. **搜索历史管理**（现有，保持不变）
   - 保存历史开关
   - 历史保留时长选择
   - 清空历史按钮

3. **语义搜索参数配置**（新增）
   - 实体匹配开关
   - 同义词扩展开关
   - 时效性提升开关
   - 语义提升权重滑块（0-1）

4. **同义词管理**（新增）
   - 同义词列表展示（表格形式）
   - 添加同义词表单（模态框）
   - 编辑/删除同义词操作

5. **搜索权重配置**（新增）
   - 实体匹配权重滑块（0-3）
   - 概念相似度权重滑块（0-3）
   - 上下文相关性权重滑块（0-3）
   - 时效性提升权重滑块（0-3）

### 4.2 组件实现

#### 4.2.1 语义搜索参数配置组件

```jsx
// frontend/src/components/SearchManagement/SemanticSearchConfig.jsx
import React, { useState } from 'react';
import axios from 'axios';

const SemanticSearchConfig = ({ settings, onUpdateSettings }) => {
  const [localSettings, setLocalSettings] = useState(settings);
  const [isSaving, setIsSaving] = useState(false);
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setLocalSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await axios.put('/api/v1/knowledge/search-settings', localSettings);
      onUpdateSettings(response.data);
      alert('语义搜索参数已保存');
    } catch (error) {
      console.error('保存语义搜索参数失败:', error);
      alert('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };
  
  return (
    <div className="setting-card">
      <div className="setting-header">
        <h3>语义搜索参数配置</h3>
        <p>配置语义搜索的高级参数</p>
      </div>
      <div className="semantic-params">
        <div className="param-item">
          <div className="param-info">
            <label htmlFor="use_entities">实体匹配</label>
            <p>使用实体识别提升搜索准确性</p>
          </div>
          <input 
            type="checkbox" 
            id="use_entities" 
            name="use_entities"
            checked={localSettings.use_entities}
            onChange={handleChange}
          />
        </div>
        <div className="param-item">
          <div className="param-info">
            <label htmlFor="use_synonyms">同义词扩展</label>
            <p>扩展查询词的同义词以获取更全面的结果</p>
          </div>
          <input 
            type="checkbox" 
            id="use_synonyms" 
            name="use_synonyms"
            checked={localSettings.use_synonyms}
            onChange={handleChange}
          />
        </div>
        <div className="param-item">
          <div className="param-info">
            <label htmlFor="boost_recent">时效性提升</label>
            <p>优先显示最新的文档</p>
          </div>
          <input 
            type="checkbox" 
            id="boost_recent" 
            name="boost_recent"
            checked={localSettings.boost_recent}
            onChange={handleChange}
          />
        </div>
        <div className="param-item">
          <div className="param-info">
            <label htmlFor="semantic_boost">语义提升权重</label>
            <p>调整语义特征对搜索结果排序的影响（0-1）</p>
          </div>
          <div className="slider-container">
            <input 
              type="range" 
              id="semantic_boost" 
              name="semantic_boost"
              min="0" 
              max="1" 
              step="0.1"
              value={localSettings.semantic_boost}
              onChange={handleChange}
            />
            <span className="slider-value">{localSettings.semantic_boost.toFixed(1)}</span>
          </div>
        </div>
      </div>
      <div className="setting-actions">
        <button 
          className="save-btn" 
          onClick={handleSave}
          disabled={isSaving}
        >
          {isSaving ? '保存中...' : '保存设置'}
        </button>
      </div>
    </div>
  );
};

export default SemanticSearchConfig;
```

#### 4.2.2 同义词管理组件

```jsx
// frontend/src/components/SearchManagement/SynonymManagement.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SynonymManagement = () => {
  const [synonyms, setSynonyms] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingSynonym, setEditingSynonym] = useState(null);
  const [formData, setFormData] = useState({
    term: '',
    synonyms: '',
    is_global: true
  });
  
  useEffect(() => {
    fetchSynonyms();
  }, []);
  
  const fetchSynonyms = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/api/v1/knowledge/synonyms');
      setSynonyms(response.data);
    } catch (error) {
      console.error('获取同义词失败:', error);
      alert('获取同义词失败');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // 验证表单
    if (!formData.term || !formData.synonyms) {
      alert('请填写完整的同义词信息');
      return;
    }
    
    // 解析同义词数组
    const synonymsArray = formData.synonyms.split(',').map(s => s.trim()).filter(s => s);
    if (synonymsArray.length === 0) {
      alert('请至少输入一个同义词');
      return;
    }
    
    setIsLoading(true);
    try {
      if (editingSynonym) {
        // 更新同义词
        await axios.put(`/api/v1/knowledge/synonyms/${editingSynonym.id}`, {
          synonyms: synonymsArray
        });
        alert('同义词已更新');
      } else {
        // 创建同义词
        await axios.post('/api/v1/knowledge/synonyms', {
          term: formData.term,
          synonyms: synonymsArray,
          is_global: formData.is_global
        });
        alert('同义词已添加');
      }
      
      // 重置表单
      setFormData({
        term: '',
        synonyms: '',
        is_global: true
      });
      setEditingSynonym(null);
      setShowModal(false);
      fetchSynonyms(); // 刷新列表
    } catch (error) {
      console.error(editingSynonym ? '更新同义词失败:' : '添加同义词失败:', error);
      alert(editingSynonym ? '更新失败' : '添加失败');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleEdit = (synonym) => {
    setEditingSynonym(synonym);
    setFormData({
      term: synonym.term,
      synonyms: synonym.synonyms.join(', '),
      is_global: synonym.is_global
    });
    setShowModal(true);
  };
  
  const handleDelete = async (id) => {
    if (window.confirm('确定要删除这个同义词吗？')) {
      setIsLoading(true);
      try {
        await axios.delete(`/api/v1/knowledge/synonyms/${id}`);
        alert('同义词已删除');
        fetchSynonyms(); // 刷新列表
      } catch (error) {
        console.error('删除同义词失败:', error);
        alert('删除失败');
      } finally {
        setIsLoading(false);
      }
    }
  };
  
  return (
    <div className="setting-card">
      <div className="setting-header">
        <h3>同义词管理</h3>
        <p>管理搜索查询的同义词映射</p>
      </div>
      
      <div className="synonym-actions">
        <button 
          className="add-btn" 
          onClick={() => {
            setEditingSynonym(null);
            setFormData({
              term: '',
              synonyms: '',
              is_global: true
            });
            setShowModal(true);
          }}
        >
          添加同义词
        </button>
      </div>
      
      {isLoading ? (
        <div className="loading">加载中...</div>
      ) : (
        <div className="synonym-table-container">
          <table className="synonym-table">
            <thead>
              <tr>
                <th>原词</th>
                <th>同义词</th>
                <th>全局有效</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {synonyms.map(synonym => (
                <tr key={synonym.id}>
                  <td>{synonym.term}</td>
                  <td>{synonym.synonyms.join(', ')}</td>
                  <td>{synonym.is_global ? '是' : '否'}</td>
                  <td>
                    <button 
                      className="edit-btn" 
                      onClick={() => handleEdit(synonym)}
                    >
                      编辑
                    </button>
                    <button 
                      className="delete-btn" 
                      onClick={() => handleDelete(synonym.id)}
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {synonyms.length === 0 && (
            <div className="no-data">暂无同义词数据</div>
          )}
        </div>
      )}
      
      {/* 添加/编辑同义词模态框 */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>{editingSynonym ? '编辑同义词' : '添加同义词'}</h3>
              <button 
                className="close-btn" 
                onClick={() => {
                  setShowModal(false);
                  setEditingSynonym(null);
                }}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSubmit} className="synonym-form">
              <div className="form-group">
                <label htmlFor="term">原词</label>
                <input 
                  type="text" 
                  id="term" 
                  name="term"
                  value={formData.term}
                  onChange={handleChange}
                  disabled={editingSynonym}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="synonyms">同义词（逗号分隔）</label>
                <input 
                  type="text" 
                  id="synonyms" 
                  name="synonyms"
                  value={formData.synonyms}
                  onChange={handleChange}
                  placeholder="例如：AI, artificial intelligence"
                  required
                />
              </div>
              <div className="form-group">
                <input 
                  type="checkbox" 
                  id="is_global" 
                  name="is_global"
                  checked={formData.is_global}
                  onChange={handleChange}
                />
                <label htmlFor="is_global">全局有效</label>
              </div>
              <div className="form-actions">
                <button type="button" className="cancel-btn" onClick={() => setShowModal(false)}>
                  取消
                </button>
                <button type="submit" className="save-btn" disabled={isLoading}>
                  {isLoading ? '保存中...' : '保存'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SynonymManagement;
```

#### 4.2.3 搜索权重配置组件

```jsx
// frontend/src/components/SearchManagement/SearchWeightConfig.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SearchWeightConfig = () => {
  const [weights, setWeights] = useState({
    entity_match: 1.5,
    concept_similarity: 1.3,
    context_relevance: 1.2,
    recency_boost: 1.1
  });
  const [isLoading, setIsLoading] = useState(false);
  
  useEffect(() => {
    fetchWeights();
  }, []);
  
  const fetchWeights = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get('/api/v1/knowledge/search-weights');
      setWeights(response.data);
    } catch (error) {
      console.error('获取搜索权重失败:', error);
      alert('获取搜索权重失败');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setWeights(prev => ({
      ...prev,
      [name]: parseFloat(value)
    }));
  };
  
  const handleSave = async () => {
    setIsLoading(true);
    try {
      const response = await axios.put('/api/v1/knowledge/search-weights', weights);
      setWeights(response.data);
      alert('搜索权重已保存');
    } catch (error) {
      console.error('保存搜索权重失败:', error);
      alert('保存失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };
  
  const weightItems = [
    {
      id: 'entity_match',
      name: '实体匹配',
      description: '匹配查询和文档中的实体（如人名、组织名等）的权重',
      value: weights.entity_match
    },
    {
      id: 'concept_similarity',
      name: '概念相似度',
      description: '查询和文档之间概念相似度的权重',
      value: weights.concept_similarity
    },
    {
      id: 'context_relevance',
      name: '上下文相关性',
      description: '查询和文档上下文相关性的权重',
      value: weights.context_relevance
    },
    {
      id: 'recency_boost',
      name: '时效性提升',
      description: '文档时效性的权重',
      value: weights.recency_boost
    }
  ];
  
  return (
    <div className="setting-card">
      <div className="setting-header">
        <h3>搜索权重配置</h3>
        <p>调整不同搜索特征对结果排序的影响（0-3）</p>
      </div>
      
      <div className="weight-config">
        {weightItems.map(item => (
          <div className="weight-item" key={item.id}>
            <div className="weight-info">
              <label htmlFor={item.id}>{item.name}</label>
              <p>{item.description}</p>
            </div>
            <div className="slider-container">
              <input 
                type="range" 
                id={item.id} 
                name={item.id}
                min="0" 
                max="3" 
                step="0.1"
                value={item.value}
                onChange={handleChange}
                disabled={isLoading}
              />
              <span className="slider-value">{item.value.toFixed(1)}</span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="setting-actions">
        <button 
          className="save-btn" 
          onClick={handleSave}
          disabled={isLoading}
        >
          {isLoading ? '保存中...' : '保存权重配置'}
        </button>
      </div>
    </div>
  );
};

export default SearchWeightConfig;
```

### 4.3 集成到现有Settings页面

需要修改frontend/src/pages/Settings.jsx文件，在activeSection === 'search'的部分引入并使用新创建的组件：

```jsx
// frontend/src/pages/Settings.jsx
// 在文件顶部添加导入
import SemanticSearchConfig from '../components/SearchManagement/SemanticSearchConfig';
import SynonymManagement from '../components/SearchManagement/SynonymManagement';
import SearchWeightConfig from '../components/SearchManagement/SearchWeightConfig';

// 在renderContent函数的activeSection === 'search'部分修改
case 'search':
  return (
    <div className="settings-content">
      <div className="content-header">
        <h2>搜索管理</h2>
        <p>配置搜索偏好和搜索引擎</p>
      </div>
      
      {/* 现有功能区块保持不变 */}
      <div className="search-section">
        <div className="setting-card">
          <div className="setting-header">
            <h3>默认搜索引擎</h3>
            <p>选择默认使用的搜索引擎</p>
          </div>
          <div className="setting-control">
            <select 
              className="search-select"
              value={searchEngine}
              onChange={(e) => setSearchEngine(e.target.value)}
            >
              <option value="google">Google</option>
              <option value="bing">Bing</option>
              <option value="duckduckgo">DuckDuckGo</option>
              <option value="baidu">百度</option>
            </select>
          </div>
        </div>
        
        <div className="setting-card">
          <div className="setting-header">
            <h3>搜索过滤设置</h3>
            <p>配置搜索结果的过滤选项</p>
          </div>
          <div className="filter-options">
            <div className="filter-item">
              <input 
                type="checkbox" 
                id="safe-search" 
                checked={safeSearch}
                onChange={(e) => setSafeSearch(e.target.checked)}
              />
              <label htmlFor="safe-search">启用安全搜索</label>
            </div>
            <div className="filter-item">
              <input 
                type="checkbox" 
                id="strict-filter" 
                checked={strictFilter}
                onChange={(e) => setStrictFilter(e.target.checked)}
              />
              <label htmlFor="strict-filter">严格内容过滤</label>
            </div>
            <div className="filter-item">
              <input 
                type="checkbox" 
                id="include-adult" 
                checked={includeAdult}
                onChange={(e) => setIncludeAdult(e.target.checked)}
              />
              <label htmlFor="include-adult">包含成人内容（需确认）</label>
            </div>
          </div>
        </div>
        
        <div className="setting-card">
          <div className="setting-header">
            <h3>搜索历史</h3>
            <p>管理您的搜索历史记录</p>
          </div>
          <div className="history-settings">
            <div className="history-option">
              <input 
                type="checkbox" 
                id="save-history" 
                checked={saveHistory}
                onChange={(e) => setSaveHistory(e.target.checked)}
              />
              <label htmlFor="save-history">保存搜索历史</label>
            </div>
            <div className="history-option">
              <select 
                className="history-duration"
                value={historyDuration}
                onChange={(e) => setHistoryDuration(e.target.value)}
              >
                <option value="30">保留30天</option>
                <option value="90">保留90天</option>
                <option value="180">保留180天</option>
                <option value="365">保留1年</option>
                <option value="forever">永久保留</option>
              </select>
            </div>
            <button className="clear-history-btn">清空搜索历史</button>
          </div>
        </div>
        
        {/* 新增功能区块 */}
        <SemanticSearchConfig 
          settings={{ 
            use_entities: true, 
            use_synonyms: true, 
            boost_recent: true, 
            semantic_boost: 0.3 
          }} 
          onUpdateSettings={(newSettings) => {
            // 更新本地状态
            console.log('更新的语义搜索参数:', newSettings);
          }} 
        />
        
        <SynonymManagement />
        
        <SearchWeightConfig />
      </div>
    </div>
  );
```

### 4.4 API调用封装

为了提高代码的可维护性，可以封装搜索管理相关的API调用：

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

// 同义词相关API
export const getSynonyms = async (isGlobal = null) => {
  const params = isGlobal !== null ? { is_global: isGlobal } : {};
  const response = await axios.get('/api/v1/knowledge/synonyms', { params });
  return response.data;
};

export const createSynonym = async (term, synonyms, isGlobal = true) => {
  const response = await axios.post('/api/v1/knowledge/synonyms', { term, synonyms, is_global: isGlobal });
  return response.data;
};

export const updateSynonym = async (id, synonyms) => {
  const response = await axios.put(`/api/v1/knowledge/synonyms/${id}`, { synonyms });
  return response.data;
};

export const deleteSynonym = async (id) => {
  await axios.delete(`/api/v1/knowledge/synonyms/${id}`);
};

// 搜索权重相关API
export const getSearchWeights = async (userId = null) => {
  const params = userId ? { user_id: userId } : {};
  const response = await axios.get('/api/v1/knowledge/search-weights', { params });
  return response.data;
};

export const updateSearchWeights = async (weights, userId = null) => {
  const params = userId ? { user_id: userId } : {};
  const response = await axios.put('/api/v1/knowledge/search-weights', weights, { params });
  return response.data;
};
```

### 4.5 文件结构

```
frontend/
└── src/
    ├── components/
    │   └── SearchManagement/           # 搜索管理组件
    │       ├── SemanticSearchConfig.jsx  # 语义搜索参数配置
    │       ├── SynonymManagement.jsx     # 同义词管理
    │       └── SearchWeightConfig.jsx    # 搜索权重配置
    ├── pages/
    │   └── Settings.jsx                # 设置页面（修改）
    └── services/
        └── searchManagementApi.js       # API调用封装
```

## 五、前后端交互设计

### 5.1 API调用流程

#### 5.1.1 页面加载流程

1. **搜索管理页面加载时**：
   - 调用`/api/v1/knowledge/search-settings`获取搜索设置（默认搜索引擎、过滤选项、语义搜索参数等）
   - 调用`/api/v1/knowledge/synonyms`获取同义词列表
   - 调用`/api/v1/knowledge/search-weights`获取搜索权重配置

#### 5.1.2 设置保存流程

1. **搜索设置保存**：
   - 用户修改搜索设置（如默认搜索引擎、过滤选项、语义搜索参数）
   - 点击"保存设置"按钮
   - 前端调用`PUT /api/v1/knowledge/search-settings`更新设置
   - 后端验证数据并更新数据库
   - 返回更新后的设置给前端
   - 前端更新本地状态并显示成功提示

2. **搜索权重保存**：
   - 用户调整搜索权重滑块
   - 点击"保存权重配置"按钮
   - 前端调用`PUT /api/v1/knowledge/search-weights`更新权重
   - 后端验证数据并更新数据库
   - 返回更新后的权重给前端
   - 前端更新本地状态并显示成功提示

#### 5.1.3 同义词管理流程

1. **添加同义词**：
   - 点击"添加同义词"按钮
   - 填写原词和同义词列表（逗号分隔）
   - 选择是否全局有效
   - 点击"保存"按钮
   - 前端调用`POST /api/v1/knowledge/synonyms`创建同义词
   - 后端验证数据并保存到数据库
   - 返回新创建的同义词给前端
   - 前端刷新同义词列表并显示成功提示

2. **编辑同义词**：
   - 点击同义词列表中的"编辑"按钮
   - 修改同义词列表
   - 点击"保存"按钮
   - 前端调用`PUT /api/v1/knowledge/synonyms/{id}`更新同义词
   - 后端验证数据并更新数据库
   - 返回更新后的同义词给前端
   - 前端刷新同义词列表并显示成功提示

3. **删除同义词**：
   - 点击同义词列表中的"删除"按钮
   - 确认删除操作
   - 前端调用`DELETE /api/v1/knowledge/synonyms/{id}`删除同义词
   - 后端从数据库中删除对应记录
   - 前端刷新同义词列表并显示成功提示

### 5.2 数据格式

#### 5.2.1 搜索设置数据格式

**请求/响应格式**：
```json
{
  "id": 1,
  "user_id": null,
  "default_search_engine": "google",
  "safe_search": true,
  "strict_filter": false,
  "include_adult": false,
  "save_history": true,
  "history_duration": 90,
  "use_entities": true,
  "use_synonyms": true,
  "boost_recent": true,
  "semantic_boost": 0.3,
  "created_at": "2025-12-19T10:00:00Z",
  "updated_at": "2025-12-19T10:00:00Z"
}
```

#### 5.2.2 同义词数据格式

**列表响应格式**：
```json
[
  {
    "id": 1,
    "term": "人工智能",
    "synonyms": ["AI", "artificial intelligence", "智能技术"],
    "is_global": true,
    "created_at": "2025-12-19T10:00:00Z",
    "updated_at": "2025-12-19T10:00:00Z"
  },
  {
    "id": 2,
    "term": "机器学习",
    "synonyms": ["ML", "machine learning", "深度学习"],
    "is_global": true,
    "created_at": "2025-12-19T10:00:00Z",
    "updated_at": "2025-12-19T10:00:00Z"
  }
]
```

**创建请求格式**：
```json
{
  "term": "自然语言处理",
  "synonyms": ["NLP", "natural language processing", "文本分析"],
  "is_global": true
}
```

**更新请求格式**：
```json
{
  "synonyms": ["NLP", "natural language processing", "文本分析", "语言理解"]
}
```

#### 5.2.3 搜索权重数据格式

**请求/响应格式**：
```json
{
  "id": 1,
  "user_id": null,
  "entity_match": 1.5,
  "concept_similarity": 1.3,
  "context_relevance": 1.2,
  "recency_boost": 1.1,
  "created_at": "2025-12-19T10:00:00Z",
  "updated_at": "2025-12-19T10:00:00Z"
}
```

### 5.3 错误处理

#### 5.3.1 后端错误响应格式

```json
{
  "detail": "错误信息描述"
}
```

#### 5.3.2 前端错误处理策略

1. **API请求错误**：
   - 显示友好的错误提示（如"保存失败，请重试"）
   - 记录详细错误信息到控制台，便于调试
   - 对于重要操作，提供重试功能

2. **表单验证错误**：
   - 在输入框附近显示具体的验证错误信息
   - 禁用提交按钮直到表单验证通过
   - 提供实时验证反馈

3. **网络错误**：
   - 显示网络连接错误提示
   - 建议用户检查网络连接并重试

### 5.4 认证与授权

1. **用户认证**：
   - 使用现有的认证机制（JWT Token）
   - API请求自动携带Token
   - 后端验证Token有效性

2. **权限控制**：
   - 全局搜索设置：管理员可管理
   - 用户级搜索设置：每个用户可管理自己的设置
   - 同义词管理：管理员可管理全局同义词，普通用户可管理自己的同义词
   - 搜索权重配置：管理员可管理全局权重，普通用户可管理自己的权重

### 5.5 性能优化

1. **API请求优化**：
   - 使用HTTP缓存减少重复请求
   - 合并相关API请求，减少网络往返
   - 使用适当的分页机制处理大量数据

2. **前端性能优化**：
   - 使用React.memo优化组件渲染
   - 延迟加载非关键组件
   - 合理使用useState和useEffect，避免不必要的重新渲染

3. **后端性能优化**：
   - 数据库查询添加索引
   - 使用缓存机制减少数据库压力
   - 优化查询逻辑，减少不必要的计算

## 六、测试计划

### 6.1 后端测试

#### 6.1.1 单元测试

**测试范围**：
- 服务层方法的正确性（SearchManagementService）
- 数据库模型的正确性（SearchSetting、SearchSynonym、SearchWeight）
- 数据校验逻辑的正确性（Pydantic Schemas）

**测试工具**：
- pytest（测试框架）
- pytest-mock（模拟依赖）
- sqlalchemy-utils（数据库测试辅助工具）

**测试示例**：
```python
# backend/tests/test_search_management_service.py
import pytest
from sqlalchemy.orm import Session
from app.modules.knowledge.services.search_management_service import SearchManagementService
from app.modules.knowledge.models.search_settings import SearchSetting

@pytest.fixture
def service():
    return SearchManagementService()

def test_get_search_settings_with_user_id(service, db: Session):
    """测试获取用户级搜索设置"""
    # 创建测试数据
    user_id = 1
    db.add(SearchSetting(user_id=user_id, default_search_engine="google"))
    db.commit()
    
    # 执行测试
    settings = service.get_search_settings(db, user_id)
    
    # 验证结果
    assert settings is not None
    assert settings.user_id == user_id
    assert settings.default_search_engine == "google"

def test_update_search_settings(service, db: Session):
    """测试更新搜索设置"""
    # 创建测试数据
    user_id = 1
    db.add(SearchSetting(user_id=user_id, default_search_engine="google"))
    db.commit()
    
    # 执行测试
    updated_settings = service.update_search_settings(
        db, 
        {"default_search_engine": "bing", "safe_search": False}, 
        user_id
    )
    
    # 验证结果
    assert updated_settings.default_search_engine == "bing"
    assert updated_settings.safe_search is False
```

#### 6.1.2 集成测试

**测试范围**：
- API接口的正确性和稳定性
- 前后端数据交互的正确性
- 异常情况的处理

**测试工具**：
- pytest
- fastapi.testclient（FastAPI测试客户端）

**测试示例**：
```python
# backend/tests/test_search_management_api.py
import pytest
from fastapi.testclient import TestClient
from app.api.v1.__init__ import api_router
from app.core.database import get_db

@pytest.fixture
def client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api_router)
    
    # 替换依赖的数据库会话
    def override_get_db():
        # 返回测试数据库会话
        pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    return TestClient(app)

def test_get_search_settings(client):
    """测试获取搜索设置API"""
    response = client.get("/api/v1/knowledge/search-settings")
    assert response.status_code == 200
    assert "default_search_engine" in response.json()
    assert "safe_search" in response.json()

def test_update_search_settings(client):
    """测试更新搜索设置API"""
    update_data = {
        "default_search_engine": "bing",
        "safe_search": False
    }
    response = client.put("/api/v1/knowledge/search-settings", json=update_data)
    assert response.status_code == 200
    assert response.json()["default_search_engine"] == "bing"
    assert response.json()["safe_search"] is False
```

#### 6.1.3 性能测试

**测试范围**：
- 搜索功能的响应时间
- 并发处理能力
- 数据库查询性能

**测试工具**：
- locust（性能测试工具）
- sqlalchemy-utils（数据库性能分析）

**测试场景**：
1. 模拟100个并发用户访问搜索设置API
2. 模拟100个并发用户管理同义词
3. 测试大数据量下的同义词查询性能

### 6.2 前端测试

#### 6.2.1 功能测试

**测试范围**：
- 页面组件的功能正确性
- 表单验证逻辑
- API调用的正确性

**测试工具**：
- jest（测试框架）
- react-testing-library（React组件测试）
- axios-mock-adapter（API模拟）

**测试示例**：
```jsx
// frontend/src/components/SearchManagement/__tests__/SemanticSearchConfig.test.jsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import axiosMock from 'axios-mock-adapter';
import axios from 'axios';
import SemanticSearchConfig from '../SemanticSearchConfig';

const mock = new axiosMock(axios);

describe('SemanticSearchConfig Component', () => {
  beforeEach(() => {
    mock.reset();
  });
  
  test('renders correctly', () => {
    render(<SemanticSearchConfig 
      settings={{ 
        use_entities: true, 
        use_synonyms: true, 
        boost_recent: true, 
        semantic_boost: 0.3 
      }} 
      onUpdateSettings={() => {}} 
    />);
    
    expect(screen.getByText('语义搜索参数配置')).toBeInTheDocument();
    expect(screen.getByLabelText('实体匹配')).toBeInTheDocument();
    expect(screen.getByLabelText('同义词扩展')).toBeInTheDocument();
    expect(screen.getByLabelText('时效性提升')).toBeInTheDocument();
    expect(screen.getByLabelText('语义提升权重')).toBeInTheDocument();
  });
  
  test('handles save button click', async () => {
    const mockUpdateSettings = jest.fn();
    
    mock.onPut('/api/v1/knowledge/search-settings').reply(200, {
      use_entities: false,
      use_synonyms: true,
      boost_recent: false,
      semantic_boost: 0.5
    });
    
    render(<SemanticSearchConfig 
      settings={{ 
        use_entities: true, 
        use_synonyms: true, 
        boost_recent: true, 
        semantic_boost: 0.3 
      }} 
      onUpdateSettings={mockUpdateSettings} 
    />);
    
    // 修改设置
    fireEvent.click(screen.getByLabelText('实体匹配')); // 取消选中
    fireEvent.click(screen.getByLabelText('时效性提升')); // 取消选中
    fireEvent.change(screen.getByLabelText('语义提升权重'), {
      target: { value: 0.5 }
    });
    
    // 点击保存
    fireEvent.click(screen.getByText('保存设置'));
    
    // 验证API调用
    expect(mock.history.put.length).toBe(1);
    expect(mock.history.put[0].data).toContain('use_entities=false');
    expect(mock.history.put[0].data).toContain('use_synonyms=true');
    expect(mock.history.put[0].data).toContain('boost_recent=false');
    expect(mock.history.put[0].data).toContain('semantic_boost=0.5');
  });
});
```

#### 6.2.2 交互测试

**测试范围**：
- 用户交互的流畅性
- 组件状态的正确更新
- 错误提示的显示

**测试工具**：
- cypress（端到端测试工具）

**测试场景**：
1. 测试语义搜索参数配置的开关和滑块交互
2. 测试同义词管理的添加、编辑、删除功能
3. 测试搜索权重配置的滑块交互

#### 6.2.3 兼容性测试

**测试范围**：
- 不同浏览器的兼容性（Chrome、Firefox、Safari、Edge）
- 不同设备的兼容性（桌面、平板、手机）
- 不同分辨率的兼容性

**测试工具**：
- browserstack（跨浏览器测试平台）
- responsive design checker（响应式设计测试工具）

### 6.3 端到端测试

**测试范围**：
- 前后端交互的完整性
- 用户场景的完整性
- 业务流程的正确性

**测试工具**：
- cypress（端到端测试工具）

**测试场景**：

1. **搜索设置管理场景**：
   - 登录系统
   - 进入搜索管理页面
   - 修改默认搜索引擎为Bing
   - 关闭安全搜索
   - 保存设置
   - 验证设置已更新

2. **同义词管理场景**：
   - 登录系统
   - 进入搜索管理页面
   - 点击"添加同义词"
   - 填写原词"自然语言处理"和同义词"NLP, natural language processing"
   - 保存同义词
   - 验证同义词已添加
   - 编辑同义词，添加"文本分析"
   - 保存修改
   - 验证同义词已更新
   - 删除同义词
   - 验证同义词已删除

3. **搜索权重配置场景**：
   - 登录系统
   - 进入搜索管理页面
   - 调整实体匹配权重为2.0
   - 调整概念相似度权重为1.5
   - 保存权重配置
   - 验证权重已更新

### 6.4 测试策略

1. **测试环境**：
   - 开发环境：用于开发过程中的单元测试和集成测试
   - 测试环境：用于完整的功能测试和性能测试
   - 预生产环境：用于端到端测试和回归测试

2. **测试数据**：
   - 使用真实的测试数据，包括各种边界情况
   - 确保测试数据的多样性和代表性

3. **测试报告**：
   - 使用测试报告工具生成详细的测试报告
   - 包括测试覆盖率、测试结果、性能指标等

4. **回归测试**：
   - 在每次代码更新后执行回归测试
   - 确保现有功能不受影响

### 6.5 测试覆盖率目标

- 后端单元测试覆盖率：≥80%
- 前端组件测试覆盖率：≥70%
- API接口测试覆盖率：100%
- 核心业务流程测试覆盖率：100%

## 七、部署计划

1. **后端部署**：
   - 更新数据库模型（执行数据库迁移）
   - 部署新的API接口
   - 更新服务层代码

2. **前端部署**：
   - 编译前端代码
   - 部署新的页面和组件
   - 清理缓存

## 八、开发时间表

| 阶段 | 时间 | 任务 |
|------|------|------|
| 需求分析 | 1天 | 分析现有功能和扩展需求 |
| 后端开发 | 3天 | 数据库模型、服务层、API接口实现 |
| 前端开发 | 2天 | 页面组件和功能实现 |
| 前后端联调 | 1天 | 实现前后端交互 |
| 测试 | 1天 | 功能测试和性能测试 |
| 优化 | 1天 | 用户体验和界面设计优化 |
| 部署 | 1天 | 部署到生产环境 |

总计：10天

## 九、风险评估

1. **技术风险**：
   - 语义搜索参数配置可能影响搜索性能
   - 同义词扩展可能导致搜索结果不准确

2. **解决方案**：
   - 实现参数验证和性能监控
   - 提供默认参数配置和重置功能

## 十、预期效果

1. **提升搜索体验**：
   - 支持个性化搜索设置
   - 提供更准确的搜索结果

2. **增强搜索功能**：
   - 支持语义搜索参数配置
   - 支持同义词管理和搜索权重配置

3. **提升用户满意度**：
   - 提供更灵活的搜索配置选项
   - 提升搜索结果的相关性和质量

## 十一、总结

本开发计划详细描述了搜索管理页面的前后端开发内容，包括功能需求、数据库设计、API接口、前端页面、前后端交互、测试和部署等方面。通过本计划的实施，将显著提升Py Copilot应用的搜索功能和用户体验。