# 语义搜索使用文档

## 概述

语义搜索服务是基于知识图谱的智能搜索系统，提供增强的语义理解和搜索功能。它结合了向量搜索、实体识别、同义词扩展和语义重排序等技术，能够更准确地理解用户查询意图并返回相关结果。

## 核心功能

### 1. 语义搜索
- **智能查询理解**：自动识别查询中的实体和关键概念
- **同义词扩展**：自动扩展查询词的同义词，提高召回率
- **语义重排序**：基于语义相关性对搜索结果进行智能重排序
- **性能监控**：详细的搜索性能统计和日志记录

### 2. 搜索建议
- **查询补全**：提供搜索查询的自动补全建议
- **同义词建议**：推荐相关的同义词和扩展查询
- **拼写纠正**：自动纠正拼写错误

### 3. 搜索分析
- **查询复杂度分析**：评估查询的复杂程度
- **搜索效果分析**：分析搜索结果的准确性和相关性
- **性能统计**：提供搜索性能的详细统计信息

## API 端点

### 健康检查
```http
GET /api/v1/semantic-search/health
```

**响应示例：**
```json
{
    "status": "healthy",
    "service": "semantic-search"
}
```

### 语义搜索
```http
POST /api/v1/semantic-search/search
```

**请求参数：**
```json
{
    "query": "人工智能技术",
    "n_results": 10,
    "knowledge_base_id": 1,
    "use_entities": true,
    "use_synonyms": true,
    "boost_recent": true,
    "semantic_boost": 0.3
}
```

**参数说明：**
- `query` (string, 必需): 搜索查询
- `n_results` (int, 可选, 默认10): 返回结果数量
- `knowledge_base_id` (int, 可选): 指定知识库ID
- `use_entities` (bool, 可选, 默认true): 是否使用实体识别
- `use_synonyms` (bool, 可选, 默认true): 是否使用同义词扩展
- `boost_recent` (bool, 可选, 默认true): 是否提升近期文档的权重
- `semantic_boost` (float, 可选, 默认0.3): 语义重排序的权重系数

**响应示例：**
```json
{
    "query": "人工智能技术",
    "results": [
        {
            "id": "doc_123",
            "title": "人工智能技术发展报告",
            "content": "人工智能技术正在快速发展...",
            "score": 0.95,
            "metadata": {
                "knowledge_base_id": 1,
                "created_at": "2024-01-15T10:30:00",
                "source": "技术报告"
            },
            "search_stats": {
                "query": "人工智能技术",
                "n_results": 10,
                "preprocessing_time": 0.012,
                "vector_search_time": 0.045,
                "reranking_time": 0.023,
                "total_time": 0.080,
                "base_results_count": 20,
                "final_results_count": 10,
                "success": true
            }
        }
    ],
    "count": 1,
    "search_type": "semantic",
    "analysis": {
        "query_complexity": "medium",
        "entity_usage": true,
        "synonym_usage": true,
        "semantic_boost": 0.3,
        "result_quality": "high",
        "suggestions": ["AI技术", "智能技术"]
    }
}
```

### 搜索建议
```http
GET /api/v1/semantic-search/suggestions?query=人工智能&limit=5
```

**查询参数：**
- `query` (string, 必需): 搜索查询
- `limit` (int, 可选, 默认5): 建议数量限制

**响应示例：**
```json
{
    "query": "人工智能",
    "suggestions": [
        {
            "suggestion": "AI",
            "score": 0.9,
            "type": "synonym"
        },
        {
            "suggestion": "artificial intelligence",
            "score": 0.85,
            "type": "synonym"
        },
        {
            "suggestion": "机器学习",
            "score": 0.7,
            "type": "expansion"
        }
    ],
    "count": 3
}
```

### 搜索分析
```http
POST /api/v1/semantic-search/analyze?query=人工智能&n_results=10&knowledge_base_id=1
```

**查询参数：**
- `query` (string, 必需): 搜索查询
- `n_results` (int, 可选, 默认10): 搜索结果数量
- `knowledge_base_id` (int, 可选): 指定知识库ID

**响应示例：**
```json
{
    "query": "人工智能",
    "analysis": {
        "query_complexity": "simple",
        "entity_usage": true,
        "synonym_usage": true,
        "semantic_boost": 0.3,
        "result_quality": "high",
        "suggestions": ["AI", "智能技术"]
    },
    "sample_results_count": 10
}
```

### 性能统计
```http
GET /api/v1/semantic-search/performance?knowledge_base_id=1&days=7
```

**查询参数：**
- `knowledge_base_id` (int, 可选): 指定知识库ID
- `days` (int, 可选, 默认7): 统计天数

**响应示例：**
```json
{
    "average_response_time": 0.15,
    "success_rate": 0.98,
    "total_searches": 1500,
    "popular_queries": [
        {"query": "人工智能", "count": 120},
        {"query": "机器学习", "count": 95},
        {"query": "自然语言处理", "count": 78}
    ],
    "coverage_percentage": 0.85
}
```

## 使用示例

### Python 客户端示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:8001/api/v1/semantic-search"

# 语义搜索示例
def semantic_search(query, n_results=10):
    url = f"{BASE_URL}/search"
    payload = {
        "query": query,
        "n_results": n_results,
        "use_entities": True,
        "use_synonyms": True,
        "boost_recent": True,
        "semantic_boost": 0.3
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"搜索失败: {response.status_code}")
        return None

# 搜索建议示例
def get_suggestions(query, limit=5):
    url = f"{BASE_URL}/suggestions"
    params = {
        "query": query,
        "limit": limit
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取建议失败: {response.status_code}")
        return None

# 使用示例
if __name__ == "__main__":
    # 执行语义搜索
    results = semantic_search("人工智能技术")
    if results:
        print(f"找到 {results['count']} 个结果")
        for result in results['results'][:3]:
            print(f"- {result['title']} (分数: {result['score']:.3f})")
    
    # 获取搜索建议
    suggestions = get_suggestions("人工智能")
    if suggestions:
        print(f"\n搜索建议:")
        for suggestion in suggestions['suggestions']:
            print(f"- {suggestion['suggestion']} ({suggestion['type']}, 分数: {suggestion['score']:.3f})")
```

### cURL 示例

```bash
# 健康检查
curl -X GET "http://localhost:8001/api/v1/semantic-search/health"

# 语义搜索
curl -X POST "http://localhost:8001/api/v1/semantic-search/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "人工智能技术",
    "n_results": 5,
    "use_entities": true,
    "use_synonyms": true
  }'

# 搜索建议
curl -X GET "http://localhost:8001/api/v1/semantic-search/suggestions?query=人工智能&limit=3"

# 搜索分析
curl -X POST "http://localhost:8001/api/v1/semantic-search/analyze?query=人工智能&n_results=10"
```

## 高级功能

### 1. 实体识别和匹配

语义搜索服务会自动识别查询中的实体（如人名、地名、技术术语等），并在搜索结果中优先匹配包含这些实体的文档。

**示例：**
- 查询："Python编程语言" → 识别实体："Python"（编程语言）
- 效果：优先返回包含"Python"相关内容的文档

### 2. 同义词扩展

系统内置了同义词词典，可以自动扩展查询词的同义词，提高搜索的召回率。

**示例：**
- 查询："机器学习" → 扩展为："机器学习" + "ML" + "machine learning"
- 效果：返回更多相关结果

### 3. 语义重排序

基于以下因素对搜索结果进行智能重排序：
- **实体匹配分数**：文档中实体与查询实体的匹配程度
- **概念相似度**：文档内容与查询概念的语义相似度
- **上下文相关性**：查询词在文档中的分布和密度
- **时效性**：近期文档的权重提升

### 4. 性能监控

每个搜索请求都会包含详细的性能统计信息：
- 预处理时间
- 向量搜索时间
- 语义重排序时间
- 总响应时间
- 搜索结果数量统计

## 错误处理

### 常见错误码

- `400 Bad Request`：请求参数错误
- `404 Not Found`：资源不存在
- `500 Internal Server Error`：服务器内部错误

### 错误响应格式

```json
{
    "detail": "错误描述信息"
}
```

## 最佳实践

### 1. 查询优化
- 使用具体的关键词而非模糊的描述
- 避免过长的查询（建议不超过50个字符）
- 使用专业术语和标准名称

### 2. 参数调优
- 对于技术文档搜索，建议启用实体识别和同义词扩展
- 对于新闻类内容，建议启用时效性提升
- 根据搜索结果质量调整语义重排序权重

### 3. 性能优化
- 合理设置`n_results`参数，避免返回过多结果
- 使用`knowledge_base_id`参数限制搜索范围
- 定期监控搜索性能统计

## 技术架构

语义搜索服务基于以下技术栈构建：

- **后端框架**：FastAPI
- **向量数据库**：ChromaDB
- **文本处理**：自定义高级文本处理器
- **实体识别**：基于规则和词典的实体提取
- **语义相似度**：向量嵌入和相似度计算

## 版本信息

- **当前版本**：v1.0.0
- **API 版本**：v1
- **最后更新**：2024-12-19

---

如有问题或建议，请联系开发团队。