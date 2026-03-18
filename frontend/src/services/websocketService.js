/**
 * WebSocket服务
 *
 * 提供WebSocket连接管理和消息处理功能，用于实时推送文档处理进度
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.clientId = null;
    this.messageHandlers = new Map(); // 存储消息类型对应的处理器列表
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.isConnecting = false;
    this.subscribedDocuments = new Set();
    this.pendingSubscriptions = []; // 待处理的订阅请求
  }

  /**
   * 生成客户端ID
   * @returns {string} 客户端ID
   */
  generateClientId() {
    return `web_client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 获取WebSocket URL
   * @returns {string} WebSocket URL
   */
  getWebSocketUrl() {
    // 开发环境使用 Vite 代理
    // 生产环境使用当前页面的host
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';

    // 开发环境通过 Vite 代理连接 WebSocket
    if (window.location.port === '5173' || window.location.port === '3000') {
      // 使用相对路径，通过 Vite 代理
      return `${protocol}//${window.location.host}/api/v1/websocket/connect/${this.clientId}`;
    }

    // 生产环境使用当前页面的host
    const host = window.location.host;
    return `${protocol}//${host}/api/v1/websocket/connect/${this.clientId}`;
  }

  /**
   * 连接到WebSocket服务器
   * @returns {Promise<void>}
   */
  async connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    if (this.isConnecting) {
      // 返回一个等待连接完成的Promise
      return new Promise((resolve, reject) => {
        const checkInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            clearInterval(checkInterval);
            resolve();
          } else if (!this.isConnecting) {
            clearInterval(checkInterval);
            reject(new Error('连接失败'));
          }
        }, 100);
        // 10秒超时
        setTimeout(() => {
          clearInterval(checkInterval);
          reject(new Error('连接超时'));
        }, 10000);
      });
    }

    this.isConnecting = true;
    this.clientId = this.generateClientId();

    return new Promise((resolve, reject) => {
      try {
        const wsUrl = this.getWebSocketUrl();

        this.ws = new WebSocket(wsUrl);

        // 设置连接超时
        const connectionTimeout = setTimeout(() => {
          if (this.ws?.readyState !== WebSocket.OPEN) {
            this.isConnecting = false;
            reject(new Error('WebSocket连接超时'));
          }
        }, 10000);

        this.ws.onopen = () => {
          clearTimeout(connectionTimeout);
          this.isConnecting = false;
          this.reconnectAttempts = 0;

          // 处理待处理的订阅请求
          if (this.pendingSubscriptions.length > 0) {
            this.subscribeToDocumentProgress(this.pendingSubscriptions);
            this.pendingSubscriptions = [];
          }

          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onclose = (event) => {
          this.isConnecting = false;

          // 如果不是正常关闭且不是手动断开，尝试重连
          if (event.code !== 1000 && event.code !== 1001 && !this._manualDisconnect) {
            this.attemptReconnect();
          }
        };

        this.ws.onerror = (error) => {
          clearTimeout(connectionTimeout);
          console.error('WebSocket错误:', error);
          this.isConnecting = false;
          reject(error);
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * 尝试重新连接
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连次数超过限制');
      return;
    }

    this.reconnectAttempts++;

    setTimeout(() => {
      this.connect().catch(error => {
        console.error('WebSocket重连失败:', error);
      });
    }, this.reconnectDelay);
  }

  /**
   * 断开WebSocket连接
   */
  disconnect() {
    // 标记为手动断开，防止自动重连
    this._manualDisconnect = true;

    // 如果正在连接中，等待连接完成或超时后再关闭
    if (this.isConnecting && this.ws?.readyState === WebSocket.CONNECTING) {
      // 延迟关闭，让连接有机会完成或失败
      setTimeout(() => {
        if (this.ws) {
          this.ws.close(1000, '客户端主动断开');
          this.ws = null;
        }
        this._manualDisconnect = false;
      }, 500);
      return;
    }

    if (this.ws) {
      this.ws.close(1000, '客户端主动断开');
      this.ws = null;
    }
    this.subscribedDocuments.clear();
    this.pendingSubscriptions = [];

    // 重置手动断开标记（延迟，确保onclose事件已经处理）
    setTimeout(() => {
      this._manualDisconnect = false;
    }, 100);
  }

  /**
   * 发送消息
   * @param {Object} message 消息对象
   */
  send(message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket未连接，无法发送消息');
    }
  }

  /**
   * 处理接收到的消息
   * @param {string} data 消息数据
   */
  handleMessage(data) {
    try {
      const message = JSON.parse(data);

      // 根据消息类型分发到对应的处理器
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('执行消息处理器失败:', error);
          }
        });
      } else {
        // 忽略系统消息类型的警告
        const systemMessageTypes = [
          'connection_established', 
          'pong', 
          'heartbeat',
          'document_progress_subscribe_ack',
          'document_progress_unsubscribe_ack'
        ];
        if (!systemMessageTypes.includes(message.type)) {
          console.warn(`未找到消息类型 '${message.type}' 的处理器`);
        }
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
    }
  }

  /**
   * 注册消息处理器
   * @param {string} messageType 消息类型
   * @param {Function} handler 处理函数
   * @returns {Function} 取消注册函数
   */
  on(messageType, handler) {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    const handlers = this.messageHandlers.get(messageType);
    handlers.push(handler);
    
    // 返回取消注册函数
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
        if (handlers.length === 0) {
          this.messageHandlers.delete(messageType);
        }
      }
    };
  }

  /**
   * 取消注册消息处理器
   * @param {string} messageType 消息类型
   * @param {Function} handler 处理函数（可选，如果不提供则移除所有该类型的处理器）
   */
  off(messageType, handler) {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      if (handler) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      } else {
        // 移除所有该类型的处理器
        this.messageHandlers.delete(messageType);
      }
    }
  }

  /**
   * 订阅文档处理进度
   * @param {number|number[]} documentIds 文档ID或ID数组
   */
  subscribeToDocumentProgress(documentIds) {
    const ids = Array.isArray(documentIds) ? documentIds : [documentIds];

    // 将所有ID转换为数字类型，确保一致性
    const normalizedIds = ids.map(id => Number(id));

    // 如果未连接，将订阅请求加入待处理队列
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.pendingSubscriptions.push(...normalizedIds);
      this.connect().catch(error => {
        console.error('WebSocket连接失败:', error);
      });
      return;
    }

    // 过滤掉已订阅的文档
    const newIds = normalizedIds.filter(id => !this.subscribedDocuments.has(id));
    if (newIds.length === 0) {
      return;
    }

    // 添加到已订阅集合
    newIds.forEach(id => this.subscribedDocuments.add(id));

    // 发送订阅消息
    this.send({
      type: 'document_progress_subscribe',
      id: `sub_${Date.now()}`,
      timestamp: new Date().toISOString(),
      document_ids: newIds
    });

  }

  /**
   * 取消订阅文档处理进度
   * @param {number|number[]} documentIds 文档ID或ID数组
   */
  unsubscribeFromDocumentProgress(documentIds) {
    const ids = Array.isArray(documentIds) ? documentIds : [documentIds];

    // 将所有ID转换为数字类型，确保一致性
    const normalizedIds = ids.map(id => Number(id));

    // 从已订阅集合中移除
    normalizedIds.forEach(id => this.subscribedDocuments.delete(id));

    // 如果未连接，无需发送取消订阅消息
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }

    // 发送取消订阅消息
    this.send({
      type: 'document_progress_unsubscribe',
      id: `unsub_${Date.now()}`,
      timestamp: new Date().toISOString(),
      document_ids: ids
    });

  }

  /**
   * 检查是否已订阅文档
   * @param {number} documentId 文档ID
   * @returns {boolean} 是否已订阅
   */
  isSubscribed(documentId) {
    // 将ID转换为数字类型，确保一致性
    return this.subscribedDocuments.has(Number(documentId));
  }

  /**
   * 获取已订阅的文档ID列表
   * @returns {number[]} 文档ID数组
   */
  getSubscribedDocuments() {
    return Array.from(this.subscribedDocuments);
  }
}

// 创建单例实例
const websocketService = new WebSocketService();

export default websocketService;
