# 分层知识图谱架构设计方案

## 1. 需求分析

### 1.1 核心需求
构建三层知识图谱体系：
- **全局知识图谱 (Global)**: 跨所有知识库的全局视角
- **知识库图谱 (Knowledge Base)**: 单一知识库内的知识整合
- **文档图谱 (Document)**: 单一文档的微观知识结构

### 1.2 设计目标
- 层次清晰：三层图谱各司其职，数据逐层聚合
- 实体关联：跨层实体链接，支持上下钻取
- 关系继承：下层关系可向上层聚合
- 查询灵活：支持分层查询和跨层导航

---

## 2. 架构设计

### 2.1 三层架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    全局知识图谱 (Global Graph)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - 跨知识库实体链接                                      │   │
│  │  - 全局实体消歧                                          │   │
│  │  - 跨库关系发现                                          │   │
│  │  - 全局语义网络                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ 实体链接、关系聚合
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  知识库图谱 (Knowledge Base Graph)                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - 库内实体整合                                          │   │
│  │  - 跨文档实体链接                                        │   │
│  │  - 库级关系网络                                          │   │
│  │  - 主题聚类                                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ 实体提取、关系构建
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    文档图谱 (Document Graph)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  - 文档内实体识别                                        │   │
│  │  - 文档内关系提取                                        │   │
│  │  - 局部语义结构                                          │   │
│  │  - 上下文关系                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 数据模型设计

#### 2.2.1 实体分层模型

```python
# 文档级实体 (已存在)
class DocumentEntity(Base):
    """文档级实体 - 最细粒度"""
    __tablename__ = "document_entities"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"))
    entity_text = Column(String(200))      # 实体文本
    entity_type = Column(String(50))       # 实体类型
    start_pos = Column(Integer)            # 起始位置
    end_pos = Column(Integer)              # 结束位置
    confidence = Column(Float)             # 置信度
    
    # 层级关联
    kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"), nullable=True)
    global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=True)


# 知识库级实体 (新增)
class KBEntity(Base):
    """知识库级实体 - 跨文档整合"""
    __tablename__ = "kb_entities"
    
    id = Column(Integer, primary_key=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    
    # 实体信息
    canonical_name = Column(String(200))   # 规范名称
    entity_type = Column(String(50))       # 实体类型
    aliases = Column(JSON)                 # 别名列表
    
    # 统计信息
    document_count = Column(Integer, default=0)  # 出现文档数
    occurrence_count = Column(Integer, default=0) # 总出现次数
    
    # 层级关联
    global_entity_id = Column(Integer, ForeignKey("global_entities.id"), nullable=True)
    
    # 关联的文档级实体
    document_entities = relationship("DocumentEntity", back_populates="kb_entity")


# 全局级实体 (新增)
class GlobalEntity(Base):
    """全局级实体 - 跨知识库统一"""
    __tablename__ = "global_entities"
    
    id = Column(Integer, primary_key=True)
    
    # 实体信息
    global_name = Column(String(200))      # 全局规范名称
    entity_type = Column(String(50))       # 实体类型
    all_aliases = Column(JSON)             # 所有别名
    
    # 统计信息
    kb_count = Column(Integer, default=0)  # 出现知识库数
    document_count = Column(Integer, default=0)  # 出现文档数
    
    # 关联的下层实体
    kb_entities = relationship("KBEntity", back_populates="global_entity")
    document_entities = relationship("DocumentEntity", back_populates="global_entity")
```

#### 2.2.2 关系分层模型

```python
# 文档级关系 (已存在)
class EntityRelationship(Base):
    """文档级关系"""
    __tablename__ = "entity_relationships"
    
    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id"))
    source_id = Column(Integer, ForeignKey("document_entities.id"))
    target_id = Column(Integer, ForeignKey("document_entities.id"))
    relationship_type = Column(String(100))
    confidence = Column(Float)


# 知识库级关系 (新增)
class KBRelationship(Base):
    """知识库级关系 - 跨文档聚合"""
    __tablename__ = "kb_relationships"
    
    id = Column(Integer, primary_key=True)
    knowledge_base_id = Column(Integer, ForeignKey("knowledge_bases.id"))
    
    # 关联的KB级实体
    source_kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"))
    target_kb_entity_id = Column(Integer, ForeignKey("kb_entities.id"))
    
    # 关系信息
    relationship_type = Column(String(100))
    aggregated_count = Column(Integer, default=0)  # 聚合的关系数量
    
    # 来源文档关系
    source_relationships = Column(JSON)  # [doc_rel_id1, doc_rel_id2, ...]


# 全局级关系 (新增)
class GlobalRelationship(Base):
    """全局级关系 - 跨知识库发现"""
    __tablename__ = "global_relationships"
    
    id = Column(Integer, primary_key=True)
    
    # 关联的全局实体
    source_global_entity_id = Column(Integer, ForeignKey("global_entities.id"))
    target_global_entity_id = Column(Integer, ForeignKey("global_entities.id"))
    
    # 关系信息
    relationship_type = Column(String(100))
    aggregated_count = Column(Integer, default=0)
    
    # 来源知识库
    source_kbs = Column(JSON)  # [kb_id1, kb_id2, ...]
```

---

## 3. 构建流程设计

### 3.1 自底向上构建流程

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: 文档级图谱构建 (Document Level)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  输入: 文档内容                                          │   │
│  │  处理:                                                   │   │
│  │    1. 实体识别 (spaCy NER)                               │   │
│  │    2. 关系提取 (依存句法分析)                             │   │
│  │    3. 构建文档内实体关系图                                 │   │
│  │  输出: DocumentEntity + EntityRelationship               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: 知识库级图谱构建 (Knowledge Base Level)                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  输入: 知识库内所有文档的实体关系                         │   │
│  │  处理:                                                   │   │
│  │    1. 实体对齐 (Entity Alignment)                        │   │
│  │       - 文本相似度匹配                                    │   │
│  │       - 语义相似度匹配 (Embedding)                        │   │
│  │    2. 实体聚类 (Entity Clustering)                       │   │
│  │       - 同一指代实体合并                                  │   │
│  │    3. 关系聚合                                           │   │
│  │       - 相同关系类型聚合                                  │   │
│  │  输出: KBEntity + KBRelationship                         │   │
│  │         + DocumentEntity.kb_entity_id 关联               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: 全局级图谱构建 (Global Level)                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  输入: 所有知识库的KB级实体                              │   │
│  │  处理:                                                   │   │
│  │    1. 跨库实体链接 (Cross-KB Entity Linking)             │   │
│  │       - 全局实体消歧                                      │   │
│  │       - 同义词扩展匹配                                    │   │
│  │    2. 全局实体整合                                        │   │
│  │    3. 跨库关系发现                                        │   │
│  │  输出: GlobalEntity + GlobalRelationship                 │   │
│  │         + KBEntity.global_entity_id 关联                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 构建触发机制

| 层级 | 触发条件 | 构建方式 |
|------|----------|----------|
| 文档级 | 文档上传/更新 | 实时构建 |
| 知识库级 | 文档级完成 + 定时任务 | 异步构建 |
| 全局级 | 知识库级完成 + 定时任务 | 异步构建 |

---

## 4. API 接口设计

### 4.1 分层查询接口

```python
# 文档级图谱查询
GET /api/knowledge/documents/{document_id}/graph
Response: {
    "level": "document",
    "nodes": [...],      # DocumentEntity
    "edges": [...],      # EntityRelationship
    "statistics": {...}
}

# 知识库级图谱查询
GET /api/knowledge/bases/{kb_id}/graph
Query Params:
    - include_documents: bool  # 是否包含下层文档节点
Response: {
    "level": "knowledge_base",
    "nodes": [...],      # KBEntity (+ DocumentEntity if requested)
    "edges": [...],      # KBRelationship
    "statistics": {...}
}

# 全局级图谱查询
GET /api/knowledge/graph/global
Query Params:
    - include_kbs: bool        # 是否包含知识库节点
    - include_documents: bool  # 是否包含文档节点
Response: {
    "level": "global",
    "nodes": [...],      # GlobalEntity (+ KBEntity + DocumentEntity)
    "edges": [...],      # GlobalRelationship
    "statistics": {...}
}
```

### 4.2 跨层导航接口

```python
# 从文档实体向上导航
GET /api/knowledge/entities/{doc_entity_id}/hierarchy
Response: {
    "document_entity": {...},
    "kb_entity": {...},       # 所属KB级实体
    "global_entity": {...}    # 所属全局级实体
}

# 从全局实体向下钻取
GET /api/knowledge/global-entities/{global_entity_id}/instances
Query Params:
    - kb_id: int?             # 筛选特定知识库
    - document_id: int?       # 筛选特定文档
Response: {
    "global_entity": {...},
    "kb_entities": [...],     # 所有KB级实例
    "document_entities": [...] # 所有文档级实例
}

# 实体搜索（跨层）
GET /api/knowledge/entities/search?q={query}&level={level}
Query Params:
    - q: str                  # 搜索关键词
    - level: str             # 搜索层级: document|kb|global|all
    - kb_id: int?            # 限制知识库
Response: {
    "results": [
        {"level": "global", "entity": {...}},
        {"level": "kb", "entity": {...}},
        {"level": "document", "entity": {...}}
    ]
}
```

---

## 5. 核心算法设计

### 5.1 实体对齐算法 (Entity Alignment)

```python
class EntityAlignmentService:
    """实体对齐服务 - 用于知识库级实体整合"""
    
    def align_entities(self, entities: List[DocumentEntity]) -> List[KBEntity]:
        """
        对齐流程:
        1. 按实体类型分组
        2. 组内相似度计算
        3. 层次聚类
        4. 生成KB级实体
        """
        # 1. 按类型分组
        groups = self._group_by_type(entities)
        
        kb_entities = []
        for entity_type, type_entities in groups.items():
            # 2. 计算相似度矩阵
            similarity_matrix = self._compute_similarity(type_entities)
            
            # 3. 层次聚类
            clusters = self._hierarchical_clustering(
                type_entities, 
                similarity_matrix,
                threshold=0.75
            )
            
            # 4. 为每个聚类生成KB实体
            for cluster in clusters:
                kb_entity = self._create_kb_entity(cluster)
                kb_entities.append(kb_entity)
        
        return kb_entities
    
    def _compute_similarity(self, entities: List[DocumentEntity]) -> np.ndarray:
        """计算实体间相似度（多维度）"""
        n = len(entities)
        similarity = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i+1, n):
                # 文本相似度 (Jaro-Winkler)
                text_sim = self._text_similarity(
                    entities[i].entity_text,
                    entities[j].entity_text
                )
                
                # 语义相似度 (Embedding cosine)
                semantic_sim = self._semantic_similarity(
                    entities[i].entity_text,
                    entities[j].entity_text
                )
                
                # 上下文相似度
                context_sim = self._context_similarity(
                    entities[i].document_id,
                    entities[j].document_id
                )
                
                # 加权组合
                similarity[i][j] = similarity[j][i] = (
                    0.4 * text_sim +
                    0.4 * semantic_sim +
                    0.2 * context_sim
                )
        
        return similarity
```

### 5.2 跨库实体链接算法 (Cross-KB Entity Linking)

```python
class CrossKBEntityLinkingService:
    """跨知识库实体链接服务"""
    
    def link_entities_across_kbs(self, kb_entities: List[KBEntity]) -> List[GlobalEntity]:
        """
        跨库链接流程:
        1. 构建实体索引 (FAISS)
        2. 相似实体检索
        3. 链接验证
        4. 生成全局实体
        """
        # 1. 构建向量索引
        index = self._build_faiss_index(kb_entities)
        
        global_entities = []
        processed = set()
        
        for entity in kb_entities:
            if entity.id in processed:
                continue
            
            # 2. 检索相似实体
            similar_entities = self._search_similar(index, entity, top_k=10)
            
            # 3. 验证链接
            linked_entities = self._verify_links(entity, similar_entities)
            linked_entities.append(entity)
            
            # 4. 生成全局实体
            global_entity = self._create_global_entity(linked_entities)
            global_entities.append(global_entity)
            
            processed.update([e.id for e in linked_entities])
        
        return global_entities
    
    def _verify_links(self, source: KBEntity, candidates: List[KBEntity]) -> List[KBEntity]:
        """验证候选链接是否有效"""
        verified = []
        for candidate in candidates:
            # 规则1: 类型必须一致
            if candidate.entity_type != source.entity_type:
                continue
            
            # 规则2: 名称相似度阈值
            name_sim = self._name_similarity(
                source.canonical_name,
                candidate.canonical_name
            )
            if name_sim < 0.6:
                continue
            
            # 规则3: 语义相似度阈值
            semantic_sim = self._semantic_similarity(
                source.canonical_name,
                candidate.canonical_name
            )
            if semantic_sim < 0.7:
                continue
            
            verified.append(candidate)
        
        return verified
```

---

## 6. 存储设计

### 6.1 数据库存储

```sql
-- 文档级实体 (已存在)
-- document_entities 表

-- 知识库级实体 (新增)
CREATE TABLE kb_entities (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_bases(id),
    canonical_name VARCHAR(200) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    aliases JSONB DEFAULT '[]',
    document_count INTEGER DEFAULT 0,
    occurrence_count INTEGER DEFAULT 0,
    global_entity_id INTEGER REFERENCES global_entities(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kb_entities_kb ON kb_entities(knowledge_base_id);
CREATE INDEX idx_kb_entities_type ON kb_entities(entity_type);
CREATE INDEX idx_kb_entities_global ON kb_entities(global_entity_id);

-- 全局级实体 (新增)
CREATE TABLE global_entities (
    id SERIAL PRIMARY KEY,
    global_name VARCHAR(200) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    all_aliases JSONB DEFAULT '[]',
    kb_count INTEGER DEFAULT 0,
    document_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_global_entities_type ON global_entities(entity_type);

-- 知识库级关系 (新增)
CREATE TABLE kb_relationships (
    id SERIAL PRIMARY KEY,
    knowledge_base_id INTEGER REFERENCES knowledge_bases(id),
    source_kb_entity_id INTEGER REFERENCES kb_entities(id),
    target_kb_entity_id INTEGER REFERENCES kb_entities(id),
    relationship_type VARCHAR(100) NOT NULL,
    aggregated_count INTEGER DEFAULT 0,
    source_relationships JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_kb_relations_kb ON kb_relationships(knowledge_base_id);
CREATE INDEX idx_kb_relations_source ON kb_relationships(source_kb_entity_id);
CREATE INDEX idx_kb_relations_target ON kb_relationships(target_kb_entity_id);

-- 全局级关系 (新增)
CREATE TABLE global_relationships (
    id SERIAL PRIMARY KEY,
    source_global_entity_id INTEGER REFERENCES global_entities(id),
    target_global_entity_id INTEGER REFERENCES global_entities(id),
    relationship_type VARCHAR(100) NOT NULL,
    aggregated_count INTEGER DEFAULT 0,
    source_kbs JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_global_relations_source ON global_relationships(source_global_entity_id);
CREATE INDEX idx_global_relations_target ON global_relationships(target_global_entity_id);
```

### 6.2 图数据库存储 (可选增强)

对于复杂图查询，可引入Neo4j：

```cypher
// 全局实体节点
CREATE (ge:GlobalEntity {
    id: 1,
    name: "人工智能",
    type: "概念",
    kb_count: 5,
    doc_count: 100
})

// 知识库实体节点
CREATE (ke:KBEntity {
    id: 1,
    kb_id: 1,
    name: "AI",
    type: "概念",
    doc_count: 20
})

// 文档实体节点
CREATE (de:DocumentEntity {
    id: 1,
    doc_id: 1,
    text: "人工智能",
    type: "概念",
    confidence: 0.95
})

// 层级关系
CREATE (de)-[:BELONGS_TO]->(ke)
CREATE (ke)-[:BELONGS_TO]->(ge)

// 语义关系
CREATE (ge)-[:RELATED_TO {type: "包含", weight: 0.9}]->(ge2)
```

---

## 7. 缓存策略

### 7.1 分层缓存

```python
class HierarchicalGraphCache:
    """分层知识图谱缓存"""
    
    def __init__(self):
        # 文档级缓存 - 短TTL（内容可能变化）
        self.document_cache = GraphCache(ttl=1800)  # 30分钟
        
        # 知识库级缓存 - 中等TTL
        self.kb_cache = GraphCache(ttl=3600)  # 1小时
        
        # 全局级缓存 - 长TTL（相对稳定）
        self.global_cache = GraphCache(ttl=7200)  # 2小时
    
    def get_graph(self, level: str, id: int) -> Optional[Dict]:
        cache = {
            "document": self.document_cache,
            "kb": self.kb_cache,
            "global": self.global_cache
        }.get(level)
        
        return cache.get(id) if cache else None
    
    def invalidate_downstream(self, level: str, id: int):
        """使下游缓存失效"""
        if level == "document":
            # 文档变化影响知识库和全局
            self.kb_cache.invalidate_by_document(id)
            self.global_cache.invalidate_by_document(id)
        elif level == "kb":
            # 知识库变化影响全局
            self.global_cache.invalidate_by_kb(id)
```

---

## 8. 可视化设计

### 8.1 分层可视化策略

```
┌─────────────────────────────────────────────────────────────────┐
│  全局视图 (Global View)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • 显示: GlobalEntity 节点                              │   │
│  │  • 颜色: 按实体类型区分                                  │   │
│  │  • 大小: 按出现文档数                                    │   │
│  │  • 交互: 点击下钻到知识库视图                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  知识库视图 (KB View)                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • 显示: KBEntity 节点 + 关联的 DocumentEntity           │   │
│  │  • 布局: 力导向图，KB实体为中心                          │   │
│  │  • 交互: 点击KB实体展开文档实体                          │   │
│  │  • 面包屑: 全局 > 知识库名称                             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  文档视图 (Document View)                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • 显示: DocumentEntity + EntityRelationship             │   │
│  │  • 布局: 语义力导向图                                     │   │
│  │  • 高亮: 显示实体在原文中的位置                           │   │
│  │  • 面包屑: 全局 > 知识库 > 文档                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 交互设计

| 操作 | 响应 |
|------|------|
| 点击全局实体 | 下钻显示该实体在各知识库的分布 |
| 点击KB实体 | 下钻显示该实体在各文档中的实例 |
| 点击文档实体 | 高亮原文位置，显示上下文 |
| 双击节点 | 展开/收起关联节点 |
| 右键菜单 | 查看详情、复制名称、搜索相关 |

---

## 9. 实施计划

### Phase 1: 基础架构 (2周)
- [ ] 数据库表设计实现
- [ ] 实体分层模型实现
- [ ] 基础API接口实现

### Phase 2: 核心算法 (2周)
- [ ] 实体对齐算法实现
- [ ] 跨库实体链接实现
- [ ] 关系聚合逻辑实现

### Phase 3: 构建流程 (1周)
- [ ] 文档级构建集成
- [ ] 知识库级构建集成
- [ ] 全局级构建集成
- [ ] 定时任务配置

### Phase 4: API与可视化 (1周)
- [ ] 分层查询API实现
- [ ] 跨层导航API实现
- [ ] 前端可视化组件

### Phase 5: 优化与测试 (1周)
- [ ] 性能优化
- [ ] 缓存策略调优
- [ ] 集成测试

---

## 10. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 实体对齐准确率不高 | 中 | 多维度相似度计算 + 人工校验机制 |
| 大规模数据性能问题 | 高 | 分批处理 + 异步构建 + 缓存优化 |
| 存储空间膨胀 | 中 | 数据压缩 + 定期清理 + 分层存储 |
| 跨库实体歧义 | 中 | 置信度阈值 + 歧义消解策略 |

---

## 11. 后续扩展

1. **时序知识图谱**: 支持实体和关系的时间维度
2. **多语言支持**: 跨语言实体链接
3. **主动学习**: 基于用户反馈优化对齐质量
4. **图神经网络**: 利用GNN进行关系推理
5. **知识推理**: 基于图谱进行知识发现和推理
