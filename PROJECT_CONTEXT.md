# Py Copilot 项目上下文与AI交互指南

## 目录

1. [项目基本信息](#一项目基本信息)
   - [项目名称](#11-项目名称)
   - [项目目标](#12-项目目标)
   - [主要功能](#13-主要功能)
   - [技术栈](#14-技术栈)
2. [项目结构](#二项目结构)
   - [整体架构](#21-整体架构)
   - [核心模块](#22-核心模块)
3. [API规范](#三api规范)
   - [路由命名规则](#31-路由命名规则)
   - [核心API列表](#32-核心api列表)
4. [开发与部署流程](#四开发与部署流程)
   - [环境配置](#41-环境配置)
   - [开发环境启动](#42-开发环境启动)
   - [代码规范](#43-代码规范)
   - [数据库迁移](#44-数据库迁移)
   - [测试](#45-测试)
   - [构建](#46-构建)
   - [部署](#47-部署)
   - [日志与监控](#48-日志与监控)
   - [常见问题与解决方案](#49-常见问题与解决方案)
   - [数据库](#410-数据库)
5. [AI交互指南](#五ai交互指南)
   - [任务优先级](#51-任务优先级)
   - [约束与规则](#52-约束与规则)
   - [沟通方式](#53-沟通方式)
6. [关键注意事项](#六关键注意事项)
   - [模块优先原则](#61-模块优先原则)
   - [前后端协调](#62-前后端协调)
   - [数据处理](#63-数据处理)
7. [版本历史变更记录](#七版本历史变更记录)
   - [文档维护说明](#71-文档维护说明)
   - [版本更新记录](#72-版本更新记录)

## 一、项目基本信息

### 1.1 项目名称
Py Copilot - 个人桌面AI辅助工具

### 1.2 项目目标
开发一个个人桌面助手，能够管理主流AI模型，按分类（类型）、能力等配合归一化参数，实现对AI大模型的灵活调用。支持智能体、工作流、全局记忆（含身份设定）、技能（Skills）等功能，适应不同场景下对不同AI的调用需求。

### 1.3 主要功能
- **AI模型管理**：支持市面主流AI模型的集成与管理
- **模型分类与能力**：按类型、能力维度对AI模型进行分类
- **归一化参数**：统一不同模型的参数格式，实现灵活调用
- **智能体系统**：支持多智能体协作与管理
- **工作流管理**：可视化构建和执行AI工作流
- **全局记忆系统**：包含身份设定、上下文记忆和历史记录
- **技能系统（Skills）**：支持扩展AI的功能和能力
- **场景化调用**：适应不同应用场景下的AI调用需求
- **代码生成与补全**：编程辅助功能
- **知识图谱集成**：增强AI的知识理解能力
- **编程辅助建议**：提高开发效率和质量

### 1.4 技术栈

#### 1.4.1 后端技术栈
- **核心框架**：Python 3.10+, FastAPI 0.104.1
- **Web服务器**：uvicorn[standard] 0.24.0.post1
- **数据验证**：Pydantic 2.5.2, Pydantic-settings 2.1.0
- **环境配置**：python-dotenv 1.0.0
- **ORM**：SQLAlchemy 2.0.23
- **数据库迁移**：Alembic 1.12.1
- **数据库**：
  - 开发环境：SQLite
  - 生产环境：支持PostgreSQL (psycopg2-binary 2.9.9)
- **AI框架与库**：
  - LangChain 0.1.5
  - OpenAI SDK 1.6.0
  - Hugging Face Hub 0.19.4
  - Transformers 4.35.2
- **缓存**：Redis 5.0.1
- **文件处理**：
  - python-multipart 0.0.6 (表单数据处理)
  - aiofiles 23.2.1 (异步文件操作)
  - PyPDF2 3.0.1 (PDF处理)
- **安全**：PyCryptodome 3.19.1 (加密功能)
- **NLP处理**：jieba 0.42.1 (中文分词)
- **图形处理**：NetworkX 3.2.1 (图论算法)
- **机器学习**：scikit-learn 1.3.2
- **社区发现**：python-louvain 0.16
- **科学计算**：numpy 1.24.3

#### 1.4.2 前端技术栈
- **核心框架**：React 18.2.0, React DOM 18.2.0
- **路由**：React Router DOM 6.22.0
- **HTTP客户端**：Axios 1.13.2
- **构建工具**：Vite 5.0.8, @vitejs/plugin-react 4.2.1
- **代码质量**：ESLint 8.55.0, eslint-plugin-react 7.33.2
- **可视化**：
  - D3.js 7.9.0 (数据可视化)
  - ReactFlow 11.11.4 (工作流可视化)
- **数学公式**：KaTeX 0.16.25, react-katex 3.1.0
- **Markdown渲染**：React Markdown 10.1.0, remark-math 6.0.0, rehype-katex 7.0.1
- **文件处理**：
  - Mammoth 1.11.0 (Word文档处理)
  - pdfjs-dist 5.4.449 (PDF文档处理)
- **图标**：React Icons 5.5.0
- **开发语言**：JavaScript/TypeScript

#### 1.4.3 AI模型支持
- OpenAI API模型
- Hugging Face Transformers模型
- 主流AI模型的统一调用接口

## 二、项目结构

### 2.1 整体架构

项目采用模块化架构设计，详细的项目结构规范、目录组织和代码规范请参考 [PROJECT_STRUCTURE_GUIDELINES.md](./PROJECT_STRUCTURE_GUIDELINES.md) 文件。

### 2.2 核心模块

#### 2.2.1 模型能力分类 (Capability Category)
- **路径**：`backend/app/modules/capability_category/`
- **功能**：管理模型的能力分类和维度
- **主要API**：
  - GET `/v1/categories/` - 获取所有分类
  - GET `/v1/categories/by-dimension` - 按维度获取分类

#### 2.2.2 模型参数管理
- **功能**：管理模型的参数模板和配置
- **主要API**：
  - GET `/suppliers/{supplier_id}/models/{model_id}/parameters` - 获取模型参数

#### 2.2.3 知识图谱集成
- **功能**：与知识图谱系统的集成
- **主要API**：
  - GET `/knowledge-graph/entities` - 获取知识图谱实体

#### 2.2.4 智能体管理
- **功能**：管理智能体的创建、配置和协作
- **主要API**：
  - GET `/agents/` - 获取所有智能体
  - POST `/agents/` - 创建智能体
  - PUT `/agents/{agent_id}/` - 更新智能体
  - DELETE `/agents/{agent_id}/` - 删除智能体

#### 2.2.5 工作流管理
- **功能**：可视化构建和执行AI工作流
- **主要API**：
  - GET `/workflows/` - 获取所有工作流
  - POST `/workflows/` - 创建工作流
  - PUT `/workflows/{workflow_id}/` - 更新工作流
  - POST `/workflows/{workflow_id}/execute` - 执行工作流

#### 2.2.6 全局记忆系统
- **功能**：管理用户身份、上下文记忆和历史记录
- **主要API**：
  - GET `/memory/` - 获取记忆内容
  - POST `/memory/` - 添加记忆
  - PUT `/memory/{memory_id}/` - 更新记忆
  - DELETE `/memory/{memory_id}/` - 删除记忆

#### 2.2.7 技能系统（Skills）
- **功能**：扩展AI的功能和能力
- **主要API**：
  - GET `/skills/` - 获取所有技能
  - POST `/skills/` - 创建技能
  - PUT `/skills/{skill_id}/` - 更新技能
  - DELETE `/skills/{skill_id}/` - 删除技能

## 三、API规范

### 3.1 路由命名规则
- 使用小写字母和连字符（如`/knowledge-graph`，不使用`/knowledgeGraph`）
- 不使用`/api`前缀（项目约定）
- 模块化路由通过`app/modules/`注册

### 3.2 核心API列表

#### 3.2.1 认证相关API
- **用户注册**：POST `/register` - 创建新用户
- **用户登录(OAuth2)**：POST `/login` - 使用标准OAuth2格式登录
- **用户登录(JSON)**：POST `/login/json` - 使用JSON格式登录
- **获取当前用户信息**：GET `/me` - 获取当前登录用户的详细信息
- **修改密码**：POST `/change-password` - 更新用户密码
- **更新用户信息**：PUT `/me` - 修改用户个人信息

#### 3.2.2 模型分类相关API
- **获取所有分类**：GET `/categories` - 获取所有模型分类列表
- **按维度分组获取分类**：GET `/categories/by-dimension` - 按维度分组返回所有分类
- **获取所有分类维度**：GET `/categories/dimensions/all` - 获取系统中所有分类维度
- **获取单个分类**：GET `/categories/{category_id}` - 获取指定分类的详细信息
- **创建分类**：POST `/categories` - 创建新的模型分类
- **更新分类**：PUT `/categories/{category_id}` - 更新分类信息
- **删除分类**：DELETE `/categories/{category_id}` - 删除指定分类
- **获取分类树形结构**：GET `/categories/tree/all` - 获取完整的分类树结构
- **获取分类统计信息**：GET `/categories/statistics` - 获取分类使用统计数据
- **获取分类默认参数**：GET `/categories/{category_id}/parameters` - 获取分类的默认参数
- **设置分类默认参数**：POST `/categories/{category_id}/parameters` - 更新分类的默认参数
- **删除分类特定参数**：DELETE `/categories/{category_id}/parameters/{param_name}` - 删除分类默认参数中的特定参数
- **获取分类层级参数**：GET `/categories/{category_id}/hierarchy/parameters` - 获取分类及其父分类的参数层级
- **根据维度获取分类**：GET `/categories/dimension/{dimension}` - 获取指定维度的所有分类
- **批量创建分类**：POST `/categories/batch` - 批量创建多个分类
- **批量删除分类**：DELETE `/categories/batch` - 批量删除多个分类

#### 3.2.3 模型与分类关联API
- **创建模型分类关联**：POST `/categories/associations` - 将模型与分类关联
- **删除模型分类关联**：DELETE `/categories/associations/model/{model_id}/category/{category_id}` - 移除模型与分类的关联
- **获取分类下的所有模型**：GET `/categories/{category_id}/models` - 获取属于指定分类的所有模型
- **获取模型的所有分类**：GET `/categories/model/{model_id}/categories` - 获取指定模型的所有分类
- **根据多个分类获取模型**：POST `/categories/models/by-categories` - 根据多个分类筛选模型
- **批量添加模型到分类**：POST `/categories/batch/model-associations` - 批量将多个模型添加到指定分类

#### 3.2.4 工作流相关API
- **获取工作流列表**：GET `/workflows` - 获取所有工作流
- **创建工作流**：POST `/workflows` - 创建新的工作流
- **获取工作流详情**：GET `/workflows/{workflow_id}` - 获取指定工作流的详细信息
- **更新工作流**：PUT `/workflows/{workflow_id}` - 更新工作流配置
- **删除工作流**：DELETE `/workflows/{workflow_id}` - 删除指定工作流
- **执行工作流**：POST `/workflows/{workflow_id}/execute` - 启动工作流执行
- **获取执行历史**：GET `/executions` - 获取所有工作流执行记录
- **获取执行详情**：GET `/executions/{execution_id}` - 获取指定执行记录的详细信息
- **测试知识搜索节点**：POST `/workflows/knowledge-search/test` - 测试知识搜索功能
- **测试实体抽取节点**：POST `/workflows/entity-extraction/test` - 测试实体抽取功能
- **测试关系分析节点**：POST `/workflows/relationship-analysis/test` - 测试关系分析功能

#### 3.2.5 知识图谱相关API
- **实体提取**：POST `/extract-entities` - 从文档或文本中提取实体和关系
- **获取文档实体**：GET `/documents/{document_id}/entities` - 获取指定文档的所有实体
- **获取文档实体(单复数变体)**：GET `/document/{document_id}/entities` - 获取指定文档的所有实体（单复数路径变体）
- **获取文档关系**：GET `/documents/{document_id}/relationships` - 获取指定文档的所有关系
- **获取文档关系(单复数变体)**：GET `/document/{document_id}/relationships` - 获取指定文档的所有关系（单复数路径变体）
- **搜索实体**：GET `/search-entities` - 根据文本搜索实体
- **获取实体关系**：GET `/entities/{entity_id}/relationships` - 获取指定实体的所有关系
- **获取图谱数据**：GET `/graph-data` - 获取知识图谱数据用于可视化
- **构建知识图谱**：POST `/build-graph` - 构建或重建知识图谱
- **获取文档图谱**：GET `/documents/{document_id}/graph` - 获取指定文档的知识图谱
- **获取知识库图谱**：GET `/knowledge-bases/{knowledge_base_id}/graph` - 获取指定知识库的知识图谱
- **分析图谱**：GET `/graphs/{graph_id}/analyze` - 分析知识图谱结构
- **查找相似节点**：GET `/graphs/{graph_id}/similar-nodes` - 查找相似的实体节点
- **查找节点路径**：GET `/graphs/{graph_id}/path` - 查找两个节点之间的路径
- **分析文档语义**：GET `/documents/{document_id}/semantics` - 分析文档的语义特征
- **获取图谱统计**：GET `/statistics` - 获取知识图谱的统计信息

#### 3.2.6 模型参数相关API
- **获取模型参数**：GET `/suppliers/{supplier_id}/models/{model_id}/parameters` - 获取指定模型的参数
- **获取模型参数层级**：GET `/categories/model/{model_id}/parameters/hierarchy` - 根据分类层级获取模型参数

#### 3.2.7 模型能力相关API
- **创建模型能力**：POST `/model/capabilities` - 创建新的模型能力
- **获取模型能力列表**：GET `/model/capabilities` - 获取所有模型能力
- **获取单个模型能力**：GET `/model/capabilities/{capability_id}` - 获取指定模型能力的详细信息
- **更新模型能力**：PUT `/model/capabilities/{capability_id}` - 更新模型能力信息
- **删除模型能力**：DELETE `/model/capabilities/{capability_id}` - 删除指定模型能力

#### 3.2.8 分类模板相关API
- **创建分类模板**：POST `/templates` - 创建新的分类模板
- **获取分类模板列表**：GET `/templates` - 获取所有分类模板
- **获取单个分类模板**：GET `/templates/{template_id}` - 获取指定分类模板的详细信息
- **更新分类模板**：PUT `/templates/{template_id}` - 更新分类模板信息
- **删除分类模板**：DELETE `/templates/{template_id}` - 删除指定分类模板
- **应用分类模板**：POST `/templates/{template_id}/apply` - 将分类模板应用到模型
- **导出分类模板**：GET `/templates/export` - 导出分类模板配置
- **导入分类模板**：POST `/templates/import` - 导入分类模板配置

#### 3.2.9 知识模块API
- **创建知识库**：POST `/knowledge-bases` - 创建新的知识库
- **获取知识库列表**：GET `/knowledge-bases` - 获取所有知识库
- **获取单个知识库**：GET `/knowledge-bases/{knowledge_base_id}` - 获取指定知识库的详细信息
- **更新知识库**：PUT `/knowledge-bases/{knowledge_base_id}` - 更新知识库信息
- **删除知识库**：DELETE `/knowledge-bases/{knowledge_base_id}` - 删除指定知识库
- **创建文档**：POST `/documents` - 创建新的文档
- **上传文档**：POST `/documents/upload` - 上传文档到知识库
- **获取文档列表**：GET `/documents` - 获取所有文档列表
- **获取文档**：GET `/documents/{document_id}` - 获取文档内容
- **更新文档**：PUT `/documents/{document_id}` - 更新文档信息
- **删除文档**：DELETE `/documents/{document_id}` - 删除指定文档
- **下载文档**：GET `/documents/{document_id}/download` - 下载文档文件
- **获取文档分块**：GET `/documents/{document_id}/chunks` - 获取文档的分段内容
- **搜索**：GET `/search` - 在知识库中搜索内容
- **高级搜索**：POST `/search/advanced` - 高级搜索功能
- **混合搜索**：POST `/search/hybrid` - 混合搜索功能
- **提取关键词**：POST `/extract-keywords` - 从文本中提取关键词
- **计算文本相似度**：POST `/calculate-similarity` - 计算两段文本的相似度
- **获取文档片段**：POST `/get-document-chunks` - 获取文档的分段内容
- **获取文档关键词**：GET `/documents/{document_id}/keywords` - 获取指定文档的关键词
- **文档向量化**：POST `/documents/{document_id}/vectorize` - 将文档转换为向量表示
- **文档标签管理**：
  - **获取所有标签**：GET `/tags` - 获取所有标签
  - **获取文档标签**：GET `/documents/{document_id}/tags` - 获取文档的所有标签
  - **添加文档标签**：POST `/documents/{document_id}/tags` - 为文档添加标签
  - **删除文档标签**：DELETE `/documents/{document_id}/tags/{tag_id}` - 删除文档的标签
  - **获取标签下的文档**：GET `/tags/{tag_id}/documents` - 获取具有指定标签的所有文档
- **文档版本管理**：
  - **获取文档版本历史**：GET `/documents/{document_id}/versions` - 获取文档的版本历史
  - **获取特定版本文档**：GET `/documents/{document_id}/versions/{version_id}` - 获取文档的特定版本
  - **恢复文档版本**：POST `/documents/{document_id}/versions/{version_id}/restore` - 恢复文档到指定版本
- **知识库统计**：GET `/stats` - 获取知识库统计信息

#### 3.2.10 实体配置API
- **获取实体类型配置**：GET `/entity-types` - 获取所有实体类型配置
- **创建实体类型**：POST `/entity-types/{entity_type}` - 创建新的实体类型配置
- **更新实体类型**：PUT `/entity-types/{entity_type}` - 更新实体类型配置
- **获取提取规则**：GET `/extraction-rules` - 获取所有实体提取规则
- **创建提取规则**：POST `/extraction-rules/{entity_type}` - 创建新的实体提取规则
- **获取实体词典**：GET `/dictionaries/{entity_type}` - 获取指定实体类型的词典
- **添加词典条目**：POST `/dictionaries/{entity_type}` - 向指定实体类型的词典添加条目
- **测试实体提取**：POST `/test-extraction` - 测试实体提取规则
- **导出实体配置**：POST `/export-config` - 导出实体配置
- **导入实体配置**：POST `/import-config` - 导入实体配置
- **重置实体配置**：POST `/reset-config` - 重置实体配置为默认状态

#### 3.2.11 供应商和模型管理API
- **创建供应商**：POST `/suppliers` - 创建新的供应商
- **获取供应商列表**：GET `/suppliers-list` - 获取所有供应商
- **获取单个供应商**：GET `/suppliers/{supplier_id}` - 获取指定供应商的详细信息
- **获取所有供应商**：GET `/suppliers/all` - 获取所有供应商的完整列表
- **更新供应商**：PUT `/suppliers/{supplier_id}` - 更新供应商信息
- **更新供应商状态**：PATCH `/suppliers/{supplier_id}/status` - 更新供应商的状态
- **删除供应商**：DELETE `/suppliers/{supplier_id}` - 删除指定供应商
- **获取模型列表**：GET `/models` - 获取所有模型
- **获取供应商的模型**：GET `/suppliers/{supplier_id}/models` - 获取指定供应商的所有模型
- **获取单个模型**：GET `/suppliers/{supplier_id}/models/{model_id}` - 获取指定模型的详细信息
- **创建模型**：POST `/suppliers/{supplier_id}/models` - 创建新的模型
- **更新模型**：PUT `/suppliers/{supplier_id}/models/{model_id}` - 更新模型信息
- **删除模型**：DELETE `/suppliers/{supplier_id}/models/{model_id}` - 删除指定模型
- **获取模型参数**：GET `/suppliers/{supplier_id}/models/{model_id}/parameters` - 获取模型的参数
- **添加模型参数**：POST `/suppliers/{supplier_id}/models/{model_id}/parameters` - 添加模型参数
- **更新模型参数**：PUT `/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_name}` - 更新指定参数
- **删除模型参数**：DELETE `/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_name}` - 删除指定参数
- **批量更新模型参数**：POST `/suppliers/{supplier_id}/models/{model_id}/parameters/batch` - 批量更新模型参数
- **设置默认模型**：POST `/suppliers/{supplier_id}/models/set-default/{model_id}` - 设置供应商的默认模型
- **获取参数版本**：GET `/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_id}/versions` - 获取参数的版本历史
- **恢复参数版本**：POST `/suppliers/{supplier_id}/models/{model_id}/parameters/{parameter_id}/revert/{version_number}` - 恢复参数到指定版本
- **批量转换参数**：POST `/suppliers/{supplier_id}/auto-convert-parameters` - 批量转换供应商所有模型的参数
- **同步模型参数**：POST `/suppliers/{supplier_id}/models/{model_id}/sync-parameters` - 同步模型参数
- **获取供应商开发模式模型**：GET `/dev/suppliers/{supplier_id}/models` - 获取开发模式下的供应商模型
- **获取所有参数**：GET `/parameters` - 获取所有参数
- **获取供应商模型列表**：POST `/suppliers/{supplier_id}/fetch-models` - 从供应商获取模型列表
- **测试供应商API**：POST `/suppliers/{supplier_id}/test-api` - 测试供应商API连接

#### 3.2.12 能力和能力维度API
- **创建能力**：POST `/capabilities` - 创建新的能力
- **获取能力列表**：GET `/capabilities` - 获取所有能力
- **获取单个能力**：GET `/capabilities/{capability_id}` - 获取指定能力的详细信息
- **更新能力**：PUT `/capabilities/{capability_id}` - 更新能力信息
- **删除能力**：DELETE `/capabilities/{capability_id}` - 删除指定能力
- **获取能力参数模板**：GET `/capabilities/{capability_id}/parameter-templates` - 获取能力的参数模板
- **获取分类默认能力**：GET `/capability/categories/{category_id}/default-capabilities` - 获取分类的默认能力
- **设置分类默认能力**：POST `/capability/categories/{category_id}/default-capabilities` - 设置分类的默认能力
- **创建能力维度**：POST `/capability-dimensions` - 创建新的能力维度
- **获取能力维度列表**：GET `/capability-dimensions` - 获取所有能力维度
- **获取单个能力维度**：GET `/capability-dimensions/{dimension_id}` - 获取指定能力维度的详细信息
- **更新能力维度**：PUT `/capability-dimensions/{dimension_id}` - 更新能力维度信息
- **删除能力维度**：DELETE `/capability-dimensions/{dimension_id}` - 删除指定能力维度
- **创建能力子维度**：POST `/capability-dimensions/subdimensions` - 创建新的能力子维度
- **获取能力子维度列表**：GET `/capability-dimensions/subdimensions` - 获取所有能力子维度
- **获取单个能力子维度**：GET `/capability-dimensions/subdimensions/{subdimension_id}` - 获取指定能力子维度的详细信息
- **更新能力子维度**：PUT `/capability-dimensions/subdimensions/{subdimension_id}` - 更新能力子维度信息
- **删除能力子维度**：DELETE `/capability-dimensions/subdimensions/{subdimension_id}` - 删除指定能力子维度
- **创建能力类型**：POST `/capability-types` - 创建新的能力类型

#### 3.2.13 模型能力相关API
- **创建模型能力**：POST `/model-capabilities` - 创建新的模型能力
- **获取模型能力列表**：GET `/model-capabilities` - 获取所有模型能力
- **获取单个模型能力**：GET `/model-capabilities/{capability_id}` - 获取指定模型能力的详细信息
- **更新模型能力**：PUT `/model-capabilities/{capability_id}` - 更新模型能力信息
- **删除模型能力**：DELETE `/model-capabilities/{capability_id}` - 删除指定模型能力
- **创建模型能力关联**：POST `/model-capabilities/associations` - 创建模型与能力的关联
- **更新模型能力关联**：PUT `/model-capabilities/associations/model/{model_id}/capability/{capability_id}` - 更新模型与能力的关联
- **删除模型能力关联**：DELETE `/model-capabilities/associations/model/{model_id}/capability/{capability_id}` - 删除模型与能力的关联
- **批量创建模型能力**：POST `/model-capabilities/batch` - 批量创建多个模型能力
- **批量更新模型能力**：PUT `/model-capabilities/batch` - 批量更新多个模型能力
- **批量删除模型能力**：DELETE `/model-capabilities/batch` - 批量删除多个模型能力
- **批量创建模型能力关联**：POST `/model-capabilities/associations/batch` - 批量创建模型与能力的关联
- **批量删除模型能力关联**：DELETE `/model-capabilities/associations/batch` - 批量删除模型与能力的关联
- **批量更新模型能力关联**：PUT `/model-capabilities/associations/batch` - 批量更新模型与能力的关联
- **获取能力的所有模型**：GET `/model-capabilities/{capability_id}/models` - 获取具有指定能力的所有模型
- **获取模型的所有能力**：GET `/model-capabilities/model/{model_id}/capabilities` - 获取指定模型的所有能力
- **能力评估**：POST `/model-capabilities/assessments/assess` - 评估模型的能力
- **能力基准测试**：POST `/model-capabilities/assessments/benchmark` - 基准测试模型的能力
- **模型能力比较**：POST `/model-capabilities/assessments/compare` - 比较多个模型的能力
- **任务推荐**：POST `/model-capabilities/assessments/recommend` - 根据任务推荐模型
- **获取评估历史**：GET `/model-capabilities/assessments/history/model/{model_id}/capability/{capability_id}` - 获取评估历史
- **创建能力版本**：POST `/model-capabilities/{capability_id}/versions` - 创建能力的新版本
- **获取能力版本历史**：GET `/model-capabilities/{capability_id}/versions` - 获取能力的版本历史
- **获取单个能力版本**：GET `/model-capabilities/{capability_id}/versions/{version_id}` - 获取指定版本的能力
- **设置当前版本**：PUT `/model-capabilities/{capability_id}/versions/{version_id}/set-current` - 设置能力的当前版本
- **设置稳定版本**：PUT `/model-capabilities/{capability_id}/versions/{version_id}/set-stable` - 设置能力的稳定版本

#### 3.2.14 参数模板和参数映射API
- **创建参数模板**：POST `/parameter-templates` - 创建新的参数模板
- **获取参数模板列表**：GET `/parameter-templates` - 获取所有参数模板
- **获取单个参数模板**：GET `/parameter-templates/{template_id}` - 获取指定参数模板的详细信息
- **更新参数模板**：PUT `/parameter-templates/{template_id}` - 更新参数模板信息
- **删除参数模板**：DELETE `/parameter-templates/{template_id}` - 删除指定参数模板
- **根据维度获取参数模板**：GET `/parameter-templates/dimension/{dimension_id}` - 获取指定维度的参数模板
- **根据子维度获取参数模板**：GET `/parameter-templates/subdimension/{subdimension_id}` - 获取指定子维度的参数模板
- **根据能力获取参数模板**：GET `/parameter-templates/capability/{capability_id}` - 获取指定能力的参数模板
- **根据层级获取参数模板**：GET `/parameter-templates/level/{level}` - 获取指定层级的参数模板
- **根据层级ID获取参数模板**：GET `/parameter-templates/level/{level}/{level_id}` - 获取指定层级和ID的参数模板
- **获取合并参数**：GET `/parameter-templates/{template_id}/merged-parameters` - 获取合并后的参数
- **应用参数标准化**：POST `/parameter-templates/{template_id}/apply-normalization` - 应用参数标准化规则
- **转换模型参数**：POST `/suppliers/{supplier_id}/models/{model_id}/parameters/convert` - 转换模型参数格式
- **反标准化参数**：POST `/suppliers/{supplier_id}/models/{model_id}/denormalize-parameters` - 将标准化参数转换为原始格式

#### 3.2.15 智能体相关API
- **创建智能体**：POST `/agents` - 创建新的智能体
- **获取智能体列表**：GET `/agents` - 获取所有智能体
- **获取单个智能体**：GET `/agents/{agent_id}` - 获取指定智能体的详细信息
- **更新智能体**：PUT `/agents/{agent_id}` - 更新智能体信息
- **删除智能体**：DELETE `/agents/{agent_id}` - 删除指定智能体
- **创建智能体分类**：POST `/agent-categories` - 创建新的智能体分类
- **获取智能体分类列表**：GET `/agent-categories` - 获取所有智能体分类
- **获取单个智能体分类**：GET `/agent-categories/{category_id}` - 获取指定智能体分类的详细信息
- **更新智能体分类**：PUT `/agent-categories/{category_id}` - 更新智能体分类信息
- **删除智能体分类**：DELETE `/agent-categories/{category_id}` - 删除指定智能体分类
- **获取智能体参数**：GET `/agents/{agent_id}/parameters` - 获取智能体的参数
- **更新智能体参数**：PUT `/agents/{agent_id}/parameters` - 更新智能体的参数

#### 3.2.16 系统和辅助API
- **获取系统参数**：GET `/system-parameters` - 获取系统参数
- **更新系统参数**：PUT `/system-parameters/{parameter_name}` - 更新系统参数
- **获取维度层次结构**：GET `/dimension-hierarchy` - 获取维度层次结构
- **更新维度层次结构**：PUT `/dimension-hierarchy` - 更新维度层次结构
- **搜索管理**：GET `/search` - 全局搜索功能
- **聊天对话**：POST `/conversations` - 创建新的对话
- **获取对话列表**：GET `/conversations` - 获取所有对话
- **获取单个对话**：GET `/conversations/{conversation_id}` - 获取指定对话的详细信息
- **更新对话**：PUT `/conversations/{conversation_id}` - 更新对话信息
- **删除对话**：DELETE `/conversations/{conversation_id}` - 删除指定对话
- **LLM调用**：POST `/llm/invoke` - 调用LLM模型
- **LLM聊天**：POST `/llm/chat` - 与LLM模型聊天

#### 3.2.17 技能系统API
- **创建技能**：POST `/skills` - 创建新的技能
- **获取技能列表**：GET `/skills` - 获取所有技能
- **获取单个技能**：GET `/skills/{skill_id}` - 获取指定技能的详细信息
- **更新技能**：PUT `/skills/{skill_id}` - 更新技能信息
- **删除技能**：DELETE `/skills/{skill_id}` - 删除指定技能
- **创建技能分类**：POST `/skill-categories` - 创建新的技能分类
- **获取技能分类列表**：GET `/skill-categories` - 获取所有技能分类
- **获取单个技能分类**：GET `/skill-categories/{category_id}` - 获取指定技能分类的详细信息
- **更新技能分类**：PUT `/skill-categories/{category_id}` - 更新技能分类信息
- **删除技能分类**：DELETE `/skill-categories/{category_id}` - 删除指定技能分类
- **将技能分配给智能体**：POST `/agents/{agent_id}/skills` - 为智能体分配技能
- **获取智能体的技能**：GET `/agents/{agent_id}/skills` - 获取智能体的所有技能
- **从智能体移除技能**：DELETE `/agents/{agent_id}/skills/{skill_id}` - 从智能体移除指定技能

#### 3.2.18 外部集成API
- **获取分类列表(外部)**：GET `/categories/external/all` - 外部API获取分类列表
- **获取单个分类(外部)**：GET `/categories/external/{category_id}` - 外部API获取单个分类
- **根据维度获取分类(外部)**：GET `/categories/external/by-dimension/{dimension}` - 外部API按维度获取分类
- **获取分类统计(外部)**：GET `/categories/external/statistics` - 外部API获取分类统计
- **为模型添加分类(外部)**：POST `/categories/external/models/{model_id}/categories` - 外部API为模型添加分类
- **从模型移除分类(外部)**：DELETE `/categories/external/models/{model_id}/categories/{category_id}` - 外部API移除模型分类

#### 3.2.19 语义搜索API
- **健康检查**：GET `/health` - 检查语义搜索服务状态
- **语义搜索**：POST `/search` - 执行语义搜索
- **获取搜索建议**：GET `/suggestions` - 获取搜索建议
- **分析搜索请求**：POST `/analyze` - 分析搜索请求
- **获取性能指标**：GET `/performance` - 获取搜索性能指标
- **优化搜索**：POST `/optimize` - 优化搜索性能

## 四、开发与部署流程

### 4.1 环境配置

#### 4.1.1 后端环境配置
1. **安装依赖**：
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **环境变量配置**：
   - 复制`.env.example`文件为`.env`
   - 根据实际情况修改`.env`文件中的配置项
   - 主要配置项包括：
     - 数据库连接信息
     - 日志级别
     - API密钥
     - Redis连接信息

3. **数据库初始化**：
   ```bash
   # 创建数据库表
   python -m app.core.database
   ```

#### 4.1.2 前端环境配置
1. **安装依赖**：
   ```bash
   cd frontend
   npm install
   ```

2. **环境变量配置**：
   - 复制`.env.example`文件为`.env`
   - 根据实际情况修改`.env`文件中的配置项
   - 主要配置项包括：
     - 后端API地址
     - 开发服务器端口

### 4.2 开发环境启动

#### 4.2.1 后端
```bash
cd backend
python run_server.py
```
- 后端服务默认运行在`http://localhost:8000`
- API文档地址：`http://localhost:8000/docs`

#### 4.2.2 前端
```bash
cd frontend
npm run dev
```
- 前端服务默认运行在`http://localhost:5173`

### 4.3 代码规范

#### 4.3.1 后端规范
- **编码风格**：遵循PEP 8
- **缩进**：使用4空格缩进
- **行长度**：每行不超过100字符
- **命名约定**：
  - 类名：PascalCase
  - 函数名：snake_case
  - 变量名：snake_case
  - 常量名：ALL_CAPS
- **文档字符串**：使用Google风格的文档字符串

#### 4.3.2 前端规范
- **编码风格**：使用ESLint
- **缩进**：使用2空格缩进
- **组件命名**：使用PascalCase
- **变量命名**：
  - 组件属性：camelCase
  - 局部变量：camelCase
  - 常量：ALL_CAPS
- **样式**：使用CSS Modules或Styled Components

### 4.4 数据库迁移

#### 4.4.1 创建迁移脚本
```bash
cd backend
alembic revision --autogenerate -m "描述迁移内容"
```

#### 4.4.2 执行迁移
```bash
cd backend
alembic upgrade head
```

#### 4.4.3 回滚迁移
```bash
cd backend
alembic downgrade <revision_id>
```

### 4.5 测试

#### 4.5.1 后端测试
```bash
cd backend
pytest
```

#### 4.5.2 前端测试
```bash
cd frontend
npm test
```

### 4.6 构建

#### 4.6.1 后端构建
```bash
cd backend
python -m build
```

#### 4.6.2 前端构建
```bash
cd frontend
npm run build
```

### 4.7 部署

#### 4.7.1 后端部署
- **生产环境**：建议使用Gunicorn + Nginx
- **Docker部署**：
  ```bash
  cd backend
  docker build -t py-copilot-backend .
  docker run -d -p 8000:8000 py-copilot-backend
  ```

#### 4.7.2 前端部署
- **静态文件服务**：使用Nginx或CDN
- **Docker部署**：
  ```bash
  cd frontend
  docker build -t py-copilot-frontend .
  docker run -d -p 80:80 py-copilot-frontend
  ```

### 4.8 日志与监控

#### 4.8.1 日志
- 后端日志存储在`backend/logs/`目录下
- 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
- 生产环境建议使用INFO或更高级别

#### 4.8.2 监控
- 使用Prometheus + Grafana进行监控
- 监控指标包括：
  - API响应时间
  - 请求成功率
  - 资源使用率
  - 错误率

### 4.9 常见问题与解决方案

1. **数据库连接失败**：
   - 检查数据库服务是否启动
   - 检查数据库连接配置
   - 检查数据库用户权限

2. **API调用失败**：
   - 检查后端服务是否启动
   - 检查API端点是否正确
   - 检查请求参数是否符合要求

3. **前端页面白屏**：
   - 检查前端依赖是否安装完整
   - 检查浏览器控制台错误信息
   - 检查后端API地址是否正确

### 4.10 数据库

#### 4.10.1 数据库概述
- 开发环境使用SQLite，数据库文件：`backend/py_copilot.db`
- 生产环境支持扩展到MySQL/PostgreSQL
- 使用SQLAlchemy ORM进行数据库操作，支持模型自动映射和关系管理
- 数据库模型基于单一Base类（`app/models/base.py`）继承，实现统一管理

#### 4.10.2 核心数据模型

##### 4.10.2.1 用户管理
- **users**：用户信息表
  - 主要字段：id, username, email, hashed_password, full_name, is_active, is_superuser, is_verified
  - 特点：支持用户状态管理和权限控制

##### 4.10.2.2 供应商和模型管理
- **suppliers**：AI供应商信息表
  - 主要字段：id, name, display_name, description, api_endpoint, api_key_required, _api_key（加密存储）, is_active
  - 特点：API密钥加密存储，支持供应商状态管理
- **models**：AI模型信息表
  - 主要字段：id, model_id, model_name, description, supplier_id, context_window, max_tokens, is_default, is_active
  - 特点：关联到供应商，支持默认模型设置
- **model_parameters**：模型参数表
  - 主要字段：id, model_id, parameter_name, parameter_type, parameter_value, is_default, description, parameter_source
  - 特点：支持参数版本管理和默认参数设置
- **parameter_versions**：参数版本历史表
  - 主要字段：id, parameter_id, version_number, parameter_value, updated_at, updated_by
  - 特点：记录参数变更历史，支持版本回滚

##### 4.10.2.3 模型分类和能力
- **model_categories**：模型分类表
  - 主要字段：id, name, display_name, description, parent_id, dimension, default_parameters, is_active, is_system
  - 特点：支持层级分类和多维分类，同一维度下分类名称唯一
- **model_category_associations**：模型分类关联表
  - 主要字段：id, model_id, category_id, weight, association_type
  - 特点：支持多对多关系和关联权重设置
- **capability_dimensions**：能力维度表
  - 主要字段：id, name, display_name, description, is_active, is_system
  - 特点：定义AI能力的主要维度（如理解能力、生成能力）
- **capability_subdimensions**：能力子维度表
  - 主要字段：id, name, display_name, description, dimension_id, is_active, is_system
  - 特点：支持能力维度的层级划分
- **model_capabilities**：模型能力表
  - 主要字段：id, name, display_name, description, dimension_id, subdimension_id, is_active
  - 特点：定义具体的AI能力项目
- **model_capability_associations**：模型能力关联表
  - 主要字段：id, model_id, capability_id, assessment_score, is_active
  - 特点：记录模型具备的能力和评估分数

##### 4.10.2.4 参数模板和标准化
- **parameter_templates**：参数模板表
  - 主要字段：id, name, display_name, description, level, level_id, parameters, is_active
  - 特点：支持层级参数模板和标准化参数定义

##### 4.10.2.5 智能体和工作流
- **agents**：智能体表
  - 主要字段：id, name, display_name, description, type, is_active
  - 特点：支持不同类型智能体的管理
- **agent_parameters**：智能体参数表
  - 主要字段：id, agent_id, parameter_name, parameter_type, parameter_value, is_default
  - 特点：存储智能体的配置参数
- **workflows**：工作流表
  - 主要字段：id, name, display_name, description, workflow_json, is_active
  - 特点：存储工作流定义和配置
- **workflow_executions**：工作流执行记录表
  - 主要字段：id, workflow_id, execution_id, status, start_time, end_time, result
  - 特点：记录工作流的执行历史和结果

##### 4.10.2.6 知识管理
- **knowledge_bases**：知识库表
  - 主要字段：id, name, display_name, description, is_active
  - 特点：支持多知识库管理
- **documents**：文档表
  - 主要字段：id, knowledge_base_id, title, content, document_type, is_active
  - 特点：存储知识库中的文档内容
- **document_chunks**：文档分块表
  - 主要字段：id, document_id, chunk_content, chunk_index, is_active
  - 特点：支持文档的分段存储和检索
- **entities**：实体表
  - 主要字段：id, name, type, description, is_active
  - 特点：存储知识图谱中的实体
- **relationships**：关系表
  - 主要字段：id, source_entity_id, target_entity_id, relationship_type, description
  - 特点：存储知识图谱中的实体关系

#### 4.10.3 数据安全
- API密钥使用加密存储（`_api_key`字段），通过属性方法自动加解密
- 密码使用哈希存储（`hashed_password`字段）
- 敏感数据字段在模型中使用下划线前缀，通过属性方法控制访问

#### 4.10.4 数据库迁移
- 使用SQLAlchemy的自动迁移功能进行数据库结构更新
- 开发环境下，数据库会在应用启动时自动创建
- 生产环境建议使用Alembic等工具进行数据库迁移管理

#### 4.10.5 表关系概述
- 用户与会话：一对多关系
- 供应商与模型：一对多关系
- 模型与参数：一对多关系
- 模型与分类：多对多关系（通过关联表）
- 模型与能力：多对多关系（通过关联表）
- 能力维度与子维度：一对多关系
- 智能体与参数：一对多关系
- 工作流与执行记录：一对多关系
- 知识库与文档：一对多关系
- 文档与分块：一对多关系
- 实体与关系：多对多关系（通过关联表）

## 五、AI交互指南

### 5.1 任务优先级
1. **功能实现**：优先完成用户明确要求的功能开发
2. **代码质量**：确保代码符合项目规范和最佳实践
3. **性能优化**：在不影响功能的前提下优化性能
4. **文档完善**：确保代码有适当的注释和文档

### 5.2 约束与规则

#### 5.2.1 文件操作
- 优先编辑现有文件，避免创建不必要的新文件
- 遵循项目结构规范，将文件放在正确的目录

#### 5.2.2 API开发
- 遵循RESTful设计原则
- 使用Pydantic模型进行请求/响应验证
- 统一的错误处理和状态码

#### 5.2.3 代码风格
- 严格遵循项目的代码规范
- 使用有意义的变量和函数命名
- 避免重复代码，提取可复用的函数和组件

#### 5.2.4 安全考虑
- 不暴露敏感信息和密钥
- 验证所有用户输入
- 遵循安全最佳实践

### 5.3 沟通方式
- 明确描述任务需求和预期结果
- 提供必要的上下文信息
- 及时反馈进展和遇到的问题

## 六、关键注意事项

### 6.1 模块优先原则
优先使用模块化结构（`backend/app/modules/`）进行开发，避免在传统的`api/v1/`目录下添加新路由。

### 6.2 前后端协调
前端API调用前缀：
- 正确路径：`/v1/categories/`（后端实际路径）
- 避免错误路径：`/v1/model/categories/`

### 6.3 数据处理
- 注意数据过滤条件，避免遗漏重要数据
- 确保数据格式的一致性和兼容性

## 七、版本历史变更记录

### 7.1 文档维护说明
- 当项目结构或核心功能发生变化时，应及时更新本文件
- 新增API或模块时，应在相应章节添加描述
- AI交互规则需要调整时，应更新相关内容

### 7.2 版本更新记录

| 版本号 | 更新日期 | 更新内容 | 负责人 |
|--------|----------|----------|--------|
| v1.0 | 2025-12-29 | 初始版本 | 系统 |
| v1.1 | 2025-12-29 | 补充技术栈详细信息 | 系统 |
| v1.2 | 2025-12-29 | 完善数据库结构信息 | 系统 |
| v1.3 | 2025-12-29 | 修复重复模块编号问题 | 系统 |
| v1.4 | 2025-12-29 | 添加技能系统API模块 | 系统 |
| v1.5 | 2025-12-29 | 完善开发与部署流程 | 系统 |
| v1.6 | 2025-12-29 | 修复章节编号冲突 | 系统 |
| v1.7 | 2025-12-29 | 补充知识模块API和语义搜索API，优化文档结构 | 系统 |

**创建日期**：2025-12-29
**最新更新日期**：2025-12-29
**当前文档版本**：v1.7
