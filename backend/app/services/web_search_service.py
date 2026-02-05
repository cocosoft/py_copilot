"""联网搜索服务"""
import requests
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# 配置日志
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()


class WebSearchService:
    """联网搜索服务，支持多种搜索引擎和安全搜索选项"""
    
    def __init__(self):
        """初始化搜索服务"""
        # 搜索引擎映射
        self.search_engines = {
            "google": self._search_google,
            "bing": self._search_bing,
            "baidu": self._search_baidu
        }
        
        # 搜索结果缓存
        self.search_cache = {}
        self.cache_timeout = timedelta(minutes=30)
        
        # 加载API密钥
        self.api_keys = {
            "google": os.getenv("GOOGLE_SEARCH_API_KEY"),
            "bing": os.getenv("BING_SEARCH_API_KEY"),
            "baidu": os.getenv("BAIDU_SEARCH_API_KEY")
        }
        
        # 默认搜索参数
        self.default_params = {
            "num_results": 5,
            "timeout": 10
        }
    
    def search(self, query: str, engine: str = "google", safe_search: bool = True, **kwargs) -> Dict[str, Any]:
        """
        执行联网搜索
        
        Args:
            query: 搜索查询词
            engine: 搜索引擎名称（google, bing, baidu）
            safe_search: 是否启用安全搜索
            **kwargs: 其他搜索参数
                - num_results: 返回结果数量
                - timeout: 请求超时时间
                - context: 搜索上下文信息
                - use_cache: 是否使用缓存
        
        Returns:
            搜索结果字典，包含查询信息和结果列表
        """
        if not query:
            raise ValueError("搜索查询词不能为空")
        
        engine = engine.lower()
        if engine not in self.search_engines:
            raise ValueError(f"不支持的搜索引擎: {engine}，支持的搜索引擎有: {list(self.search_engines.keys())}")
        
        # 合并参数
        params = self.default_params.copy()
        params.update(kwargs)
        
        # 检查缓存
        use_cache = params.get("use_cache", True)
        cache_key = self._generate_cache_key(query, engine, safe_search, params)
        if use_cache and cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            if datetime.now() - cached_result["timestamp"] < self.cache_timeout:
                logger.info(f"使用缓存的搜索结果: {query[:50]}...")
                return cached_result["data"]
            else:
                # 缓存过期，删除
                del self.search_cache[cache_key]
        
        try:
            logger.info(f"执行搜索: 引擎={engine}, 查询={query[:50]}..., 安全搜索={safe_search}")
            
            # 增强查询
            enhanced_query = self._enhance_query(query, params.get("context"))
            
            # 调用对应搜索引擎的搜索方法
            search_func = self.search_engines[engine]
            results = search_func(enhanced_query, safe_search, params)
            
            # 优化搜索结果
            optimized_results = self._optimize_results(results, params)
            
            # 构建响应
            response = {
                "query": query,
                "enhanced_query": enhanced_query,
                "engine": engine,
                "safe_search": safe_search,
                "results": optimized_results,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            # 保存到缓存
            if use_cache:
                self.search_cache[cache_key] = {
                    "timestamp": datetime.now(),
                    "data": response
                }
            
            return response
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return {
                "query": query,
                "engine": engine,
                "safe_search": safe_search,
                "results": [],
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_cache_key(self, query: str, engine: str, safe_search: bool, params: Dict[str, Any]) -> str:
        """
        生成搜索缓存的键
        """
        cache_data = {
            "query": query,
            "engine": engine,
            "safe_search": safe_search,
            "num_results": params.get("num_results"),
            "timeout": params.get("timeout")
        }
        
        # 使用哈希函数生成唯一键
        cache_string = str(cache_data)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _enhance_query(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        使用上下文增强查询
        
        Args:
            query: 原始查询
            context: 上下文信息
            
        Returns:
            增强后的查询
        """
        if not context:
            return query
        
        enhanced_query = query
        
        # 添加时间约束
        if "time_filter" in context and context["time_filter"] is not None:
            time_filter = context["time_filter"]
            if time_filter == "today":
                enhanced_query += " after:" + datetime.now().strftime("%Y-%m-%d")
            elif time_filter == "week":
                week_ago = datetime.now() - timedelta(days=7)
                enhanced_query += " after:" + week_ago.strftime("%Y-%m-%d")
            elif time_filter == "month":
                month_ago = datetime.now() - timedelta(days=30)
                enhanced_query += " after:" + month_ago.strftime("%Y-%m-%d")
        
        # 添加领域约束
        if "domain" in context and context["domain"] is not None:
            enhanced_query += " site:" + context["domain"]
        
        # 添加语言约束
        if "language" in context and context["language"] is not None:
            enhanced_query += " lang:" + context["language"]
        
        return enhanced_query
    
    def _optimize_results(self, results: List[Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        优化搜索结果
        
        Args:
            results: 原始搜索结果
            params: 搜索参数
            
        Returns:
            优化后的搜索结果
        """
        if not results:
            return []
        
        optimized_results = []
        max_results = params.get("num_results", 5)
        
        for i, result in enumerate(results):
            if i >= max_results:
                break
            
            # 过滤低质量结果
            if not result.get("title") or not result.get("url"):
                continue
            
            # 优化结果格式
            optimized_result = {
                "id": i + 1,
                "title": result["title"],
                "url": result["url"],
                "description": result.get("description", ""),
                "engine": result.get("engine", "unknown"),
                "relevance_score": self._calculate_relevance_score(result, params)
            }
            
            optimized_results.append(optimized_result)
        
        # 按相关性排序
        optimized_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return optimized_results
    
    def _calculate_relevance_score(self, result: Dict[str, Any], params: Dict[str, Any]) -> float:
        """
        计算结果相关性分数
        
        Args:
            result: 搜索结果
            params: 搜索参数
            
        Returns:
            相关性分数（0-1）
        """
        query = params.get("query", "")
        if not query:
            return 0.5
        
        score = 0.0
        query_keywords = query.lower().split()
        
        # 标题匹配分数
        title = result.get("title", "").lower()
        title_matches = sum(1 for keyword in query_keywords if keyword in title)
        title_score = title_matches / len(query_keywords) if query_keywords else 0
        score += title_score * 0.5
        
        # 描述匹配分数
        description = result.get("description", "").lower()
        desc_matches = sum(1 for keyword in query_keywords if keyword in description)
        desc_score = desc_matches / len(query_keywords) if query_keywords else 0
        score += desc_score * 0.3
        
        # URL匹配分数
        url = result.get("url", "").lower()
        url_matches = sum(1 for keyword in query_keywords if keyword in url)
        url_score = url_matches / len(query_keywords) if query_keywords else 0
        score += url_score * 0.2
        
        return min(1.0, max(0.0, score))
    
    def _search_google(self, query: str, safe_search: bool, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Google搜索实现"""
        logger.info("使用Google搜索引擎")
        
        # 检查API密钥
        api_key = self.api_keys.get("google")
        if not api_key:
            logger.error("Google API密钥未配置")
            raise ValueError("Google搜索服务未配置API密钥")
        
        try:
            # 调用Google Search API
            # https://developers.google.com/custom-search/v1/overview
            url = "https://www.googleapis.com/customsearch/v1"
            search_params = {
                "key": api_key,
                "cx": os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID"),
                "q": query,
                "num": params.get("num_results", 5),
                "safe": "active" if safe_search else "off",
                "fields": "items(title,link,snippet)"
            }
            
            response = requests.get(url, params=search_params, timeout=params.get("timeout", 10))
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "items" in data:
                for item in data["items"]:
                    results.append({
                        "title": item["title"],
                        "url": item["link"],
                        "description": item["snippet"],
                        "engine": "google"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Google搜索API调用失败: {str(e)}")
            # 直接抛出异常，不使用模拟结果
            raise
    
    def _search_bing(self, query: str, safe_search: bool, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Bing搜索实现"""
        logger.info("使用Bing搜索引擎")
        
        # 检查API密钥
        api_key = self.api_keys.get("bing")
        if not api_key:
            logger.error("Bing API密钥未配置")
            raise ValueError("Bing搜索服务未配置API密钥")
        
        try:
            # 调用Bing Search API
            # https://www.microsoft.com/en-us/bing/apis/bing-web-search-api
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {
                "Ocp-Apim-Subscription-Key": api_key
            }
            search_params = {
                "q": query,
                "count": params.get("num_results", 5),
                "safeSearch": "Strict" if safe_search else "Off",
                "responseFilter": "Webpages"
            }
            
            response = requests.get(url, headers=headers, params=search_params, timeout=params.get("timeout", 10))
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"]:
                    results.append({
                        "title": item["name"],
                        "url": item["url"],
                        "description": item["snippet"],
                        "engine": "bing"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Bing搜索API调用失败: {str(e)}")
            # 直接抛出异常，不使用模拟结果
            raise
    
    def _search_baidu(self, query: str, safe_search: bool, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """百度搜索实现"""
        logger.info("使用百度搜索引擎")
        
        # 检查API密钥
        api_key = self.api_keys.get("baidu")
        if not api_key:
            logger.error("百度API密钥未配置")
            raise ValueError("百度搜索服务未配置API密钥")
        
        try:
            # 调用百度搜索API
            # https://api.baidu.com/
            url = "https://api.baidu.com/rest/2.0/search/web"
            search_params = {
                "q": query,
                "count": params.get("num_results", 5),
                "ak": api_key,
                "rn": params.get("num_results", 5)
            }
            
            response = requests.get(url, params=search_params, timeout=params.get("timeout", 10))
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "results" in data:
                for item in data["results"]:
                    results.append({
                        "title": item["title"],
                        "url": item["url"],
                        "description": item["content"],
                        "engine": "baidu"
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"百度搜索API调用失败: {str(e)}")
            # 直接抛出异常，不使用模拟结果
            raise
    
    # TODO: 移除模拟数据 - 类型：搜索结果模拟
    # 原因：当API调用失败时返回模拟数据，应改为抛出异常
    # 处理方案：删除此方法，修改错误处理逻辑
    def _mock_search_result(self, query: str, engine: str) -> List[Dict[str, Any]]:
        """生成模拟搜索结果"""
        return [
            {
                "title": f"{engine}搜索结果 - {query}",
                "url": f"https://www.{engine}.com/search?q={query.replace(' ', '+')}",
                "description": f"这是{engine}关于'{query}'的搜索结果描述",
                "engine": engine
            },
            {
                "title": f"{engine}搜索结果2 - {query}",
                "url": f"https://www.example.com/{query}/page2",
                "description": f"这是{engine}关于'{query}'的第二个搜索结果描述",
                "engine": engine
            },
            {
                "title": f"{engine}搜索结果3 - {query}",
                "url": f"https://www.example.com/{query}/page3",
                "description": f"这是{engine}关于'{query}'的第三个搜索结果描述",
                "engine": engine
            }
        ]
    
    def clear_cache(self):
        """清除搜索结果缓存"""
        self.search_cache.clear()
        logger.info("已清除所有搜索结果缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "cache_size": len(self.search_cache),
            "cache_timeout": str(self.cache_timeout),
            "cached_queries": list(self.search_cache.keys())
        }


# 创建全局搜索服务实例
web_search_service = WebSearchService()