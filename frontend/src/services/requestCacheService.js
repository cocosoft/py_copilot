/**
 * 请求缓存服务 - FE-003 请求缓存优化
 *
 * 实现前端请求缓存机制，减少重复请求
 *
 * @task FE-003
 * @phase 前端界面优化
 */

import { queryClient } from '../config/queryClient';

/**
 * 缓存配置
 */
const CACHE_CONFIG = {
  // 默认缓存时间（毫秒）
  defaultTTL: 5 * 60 * 1000, // 5分钟

  // 不同接口的缓存时间配置
  ttlConfig: {
    // 知识库列表 - 变化较少，缓存时间长
    'knowledge.bases': 10 * 60 * 1000, // 10分钟

    // 文档列表 - 变化频繁，缓存时间短
    'knowledge.documents': 2 * 60 * 1000, // 2分钟

    // 文档详情 - 中等缓存
    'knowledge.document': 5 * 60 * 1000, // 5分钟

    // 片段列表 - 变化频繁
    'knowledge.chunks': 1 * 60 * 1000, // 1分钟

    // 实体列表 - 中等缓存
    'knowledge.entities': 3 * 60 * 1000, // 3分钟

    // 搜索结果 - 短缓存
    'knowledge.search': 30 * 1000, // 30秒

    // 统计信息 - 长缓存
    'knowledge.stats': 15 * 60 * 1000, // 15分钟

    // 模型列表 - 长缓存
    'models.list': 10 * 60 * 1000, // 10分钟

    // 供应商列表 - 长缓存
    'suppliers.list': 10 * 60 * 1000, // 10分钟

    // 用户配置 - 很长缓存
    'user.settings': 30 * 60 * 1000, // 30分钟
  },

  // 最大缓存条目数
  maxCacheSize: 1000,

  // 缓存清理间隔
  cleanupInterval: 60 * 1000, // 1分钟
};

/**
 * 内存缓存存储
 */
class MemoryCache {
  constructor() {
    this.cache = new Map();
    this.accessTimes = new Map();
    this.hitCount = 0;
    this.missCount = 0;
  }

  /**
   * 生成缓存键
   */
  generateKey(key, params = {}) {
    const paramsString = Object.keys(params).length
      ? JSON.stringify(params)
      : '';
    return paramsString ? `${key}:${paramsString}` : key;
  }

  /**
   * 获取缓存
   */
  get(key, params) {
    const cacheKey = this.generateKey(key, params);
    const item = this.cache.get(cacheKey);

    if (!item) {
      this.missCount++;
      return null;
    }

    // 检查是否过期
    if (Date.now() > item.expiresAt) {
      this.cache.delete(cacheKey);
      this.accessTimes.delete(cacheKey);
      this.missCount++;
      return null;
    }

    // 更新访问时间
    this.accessTimes.set(cacheKey, Date.now());
    this.hitCount++;

    return item.data;
  }

  /**
   * 设置缓存
   */
  set(key, params, data, ttl = CACHE_CONFIG.defaultTTL) {
    const cacheKey = this.generateKey(key, params);

    // 检查缓存大小，如果超过限制则清理
    if (this.cache.size >= CACHE_CONFIG.maxCacheSize) {
      this.cleanup();
    }

    this.cache.set(cacheKey, {
      data,
      expiresAt: Date.now() + ttl,
      createdAt: Date.now(),
    });

    this.accessTimes.set(cacheKey, Date.now());
  }

  /**
   * 删除缓存
   */
  delete(key, params) {
    const cacheKey = this.generateKey(key, params);
    this.cache.delete(cacheKey);
    this.accessTimes.delete(cacheKey);
  }

  /**
   * 清除所有缓存
   */
  clear() {
    this.cache.clear();
    this.accessTimes.clear();
    this.hitCount = 0;
    this.missCount = 0;
  }

  /**
   * 清理过期缓存
   */
  cleanup() {
    const now = Date.now();
    let deletedCount = 0;

    // 首先删除过期项
    for (const [key, item] of this.cache.entries()) {
      if (now > item.expiresAt) {
        this.cache.delete(key);
        this.accessTimes.delete(key);
        deletedCount++;
      }
    }

    // 如果还是超过限制，删除最久未访问的
    if (this.cache.size >= CACHE_CONFIG.maxCacheSize) {
      const sortedEntries = Array.from(this.accessTimes.entries()).sort(
        (a, b) => a[1] - b[1]
      );

      const toDelete = Math.ceil(this.cache.size * 0.2); // 删除20%
      for (let i = 0; i < toDelete && i < sortedEntries.length; i++) {
        this.cache.delete(sortedEntries[i][0]);
        this.accessTimes.delete(sortedEntries[i][0]);
        deletedCount++;
      }
    }

    return deletedCount;
  }

  /**
   * 获取缓存统计
   */
  getStats() {
    const total = this.hitCount + this.missCount;
    return {
      size: this.cache.size,
      hitCount: this.hitCount,
      missCount: this.missCount,
      hitRate: total > 0 ? (this.hitCount / total) * 100 : 0,
    };
  }

  /**
   * 获取所有缓存键
   */
  getKeys() {
    return Array.from(this.cache.keys());
  }
}

// 创建全局内存缓存实例
const memoryCache = new MemoryCache();

/**
 * 请求缓存服务
 */
class RequestCacheService {
  constructor() {
    this.memoryCache = memoryCache;
    this.enabled = true;

    // 启动定时清理
    this.startCleanupTimer();
  }

  /**
   * 启动清理定时器
   */
  startCleanupTimer() {
    setInterval(() => {
      const deleted = this.memoryCache.cleanup();
      if (deleted > 0 && import.meta.env.DEV) {
        console.log(`[RequestCache] Cleaned up ${deleted} expired items`);
      }
    }, CACHE_CONFIG.cleanupInterval);
  }

  /**
   * 获取缓存时间
   */
  getTTL(key) {
    return CACHE_CONFIG.ttlConfig[key] || CACHE_CONFIG.defaultTTL;
  }

  /**
   * 获取缓存
   */
  get(key, params) {
    if (!this.enabled) return null;
    return this.memoryCache.get(key, params);
  }

  /**
   * 设置缓存
   */
  set(key, params, data, customTTL) {
    if (!this.enabled) return;
    const ttl = customTTL || this.getTTL(key);
    this.memoryCache.set(key, params, data, ttl);
  }

  /**
   * 删除缓存
   */
  invalidate(key, params) {
    this.memoryCache.delete(key, params);

    // 同时清除 React Query 缓存
    if (!params) {
      queryClient.invalidateQueries({ queryKey: [key] });
    }
  }

  /**
   * 根据模式删除缓存
   */
  invalidatePattern(pattern) {
    const keys = this.memoryCache.getKeys();
    const regex = new RegExp(pattern);

    keys.forEach((key) => {
      if (regex.test(key)) {
        this.memoryCache.cache.delete(key);
        this.memoryCache.accessTimes.delete(key);
      }
    });
  }

  /**
   * 清除所有缓存
   */
  clear() {
    this.memoryCache.clear();
    queryClient.clear();
  }

  /**
   * 启用/禁用缓存
   */
  setEnabled(enabled) {
    this.enabled = enabled;
  }

  /**
   * 获取统计信息
   */
  getStats() {
    return {
      memory: this.memoryCache.getStats(),
      reactQuery: {
        queries: queryClient.getQueryCache().getAll().length,
      },
    };
  }

  /**
   * 带缓存的请求包装器
   */
  async request(key, params, requestFn, options = {}) {
    const { skipCache = false, customTTL, onCacheHit, onCacheMiss } = options;

    // 如果不跳过缓存，先尝试从缓存获取
    if (!skipCache && this.enabled) {
      const cached = this.get(key, params);
      if (cached !== null) {
        onCacheHit?.(cached);
        return cached;
      }
    }

    // 执行请求
    onCacheMiss?.();
    const data = await requestFn();

    // 缓存结果
    if (this.enabled) {
      this.set(key, params, data, customTTL);
    }

    return data;
  }

  /**
   * 预加载缓存
   */
  async preload(key, params, requestFn) {
    const data = await requestFn();
    this.set(key, params, data);
    return data;
  }

  /**
   * 刷新缓存
   */
  async refresh(key, params, requestFn) {
    // 删除旧缓存
    this.invalidate(key, params);

    // 获取新数据
    const data = await requestFn();

    // 设置新缓存
    this.set(key, params, data);

    return data;
  }
}

// 创建单例实例
const requestCacheService = new RequestCacheService();

export default requestCacheService;
export { memoryCache, CACHE_CONFIG };
