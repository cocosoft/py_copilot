// 实时协作服务

/**
 * 协作事件类型
 */
export const COLLAB_EVENTS = {
  // 连接事件
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  RECONNECT: 'reconnect',
  
  // 用户事件
  USER_JOINED: 'user_joined',
  USER_LEFT: 'user_left',
  USER_UPDATED: 'user_updated',
  
  // 画布事件
  CANVAS_STATE_CHANGED: 'canvas_state_changed',
  ELEMENT_ADDED: 'element_added',
  ELEMENT_UPDATED: 'element_updated',
  ELEMENT_REMOVED: 'element_removed',
  CONNECTION_ADDED: 'connection_added',
  CONNECTION_UPDATED: 'connection_updated',
  CONNECTION_REMOVED: 'connection_removed',
  
  // 选择事件
  SELECTION_CHANGED: 'selection_changed',
  
  // 协作事件
  OPERATION_CONFLICT: 'operation_conflict',
  OPERATION_RESOLVED: 'operation_resolved',
  HISTORY_UPDATED: 'history_updated'
};

/**
 * 协作操作类型
 */
export const OPERATION_TYPES = {
  ADD_ELEMENT: 'add_element',
  UPDATE_ELEMENT: 'update_element',
  DELETE_ELEMENT: 'delete_element',
  MOVE_ELEMENT: 'move_element',
  RESIZE_ELEMENT: 'resize_element',
  ADD_CONNECTION: 'add_connection',
  UPDATE_CONNECTION: 'update_connection',
  DELETE_CONNECTION: 'delete_connection',
  CHANGE_SELECTION: 'change_selection',
  CHANGE_CANVAS_STATE: 'change_canvas_state'
};

/**
 * 实时协作服务类
 */
class CollaborationService {
  constructor() {
    this.ws = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000;
    this.eventListeners = new Map();
    this.userId = null;
    this.sessionId = null;
    this.roomId = null;
    this.users = new Map();
    this.operations = new Map();
    this.conflictResolver = null;
  }

  /**
   * 连接到协作服务器
   */
  connect(serverUrl, userId, sessionId, roomId) {
    return new Promise((resolve, reject) => {
      try {
        this.userId = userId;
        this.sessionId = sessionId;
        this.roomId = roomId;
        
        this.ws = new WebSocket(`${serverUrl}?userId=${userId}&sessionId=${sessionId}&roomId=${roomId}`);
        
        this.ws.onopen = () => {
          console.log('协作服务连接成功');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.emit(COLLAB_EVENTS.CONNECT);
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };
        
        this.ws.onclose = (event) => {
          console.log('协作服务连接关闭', event);
          this.isConnected = false;
          this.emit(COLLAB_EVENTS.DISCONNECT, { event });
          this.handleReconnect();
        };
        
        this.ws.onerror = (error) => {
          console.error('协作服务连接错误', error);
          this.emit(COLLAB_EVENTS.DISCONNECT, { error });
          reject(error);
        };
        
      } catch (error) {
        console.error('连接协作服务失败', error);
        reject(error);
      }
    });
  }

  /**
   * 断开连接
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
    this.users.clear();
    this.operations.clear();
  }

  /**
   * 处理重连
   */
  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('达到最大重连次数，停止重连');
      return;
    }
    
    this.reconnectAttempts++;
    console.log(`尝试重连，第${this.reconnectAttempts}次`);
    
    setTimeout(() => {
      if (this.userId && this.sessionId && this.roomId) {
        this.connect(this.ws.url.split('?')[0], this.userId, this.sessionId, this.roomId)
          .then(() => {
            this.emit(COLLAB_EVENTS.RECONNECT);
          })
          .catch(error => {
            console.error('重连失败', error);
          });
      }
    }, this.reconnectInterval);
  }

  /**
   * 处理接收到的消息
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      const { type, payload, timestamp, userId, operationId } = data;
      
      console.log('收到协作消息:', type, payload);
      
      // 记录操作
      if (operationId) {
        this.operations.set(operationId, {
          ...data,
          receivedAt: Date.now()
        });
      }
      
      // 根据消息类型分发处理
      switch (type) {
        case COLLAB_EVENTS.USER_JOINED:
          this.handleUserJoined(payload);
          break;
          
        case COLLAB_EVENTS.USER_LEFT:
          this.handleUserLeft(payload);
          break;
          
        case COLLAB_EVENTS.USER_UPDATED:
          this.handleUserUpdated(payload);
          break;
          
        case COLLAB_EVENTS.ELEMENT_ADDED:
        case COLLAB_EVENTS.ELEMENT_UPDATED:
        case COLLAB_EVENTS.ELEMENT_REMOVED:
        case COLLAB_EVENTS.CONNECTION_ADDED:
        case COLLAB_EVENTS.CONNECTION_UPDATED:
        case COLLAB_EVENTS.CONNECTION_REMOVED:
          this.handleCanvasOperation(type, payload, userId);
          break;
          
        case COLLAB_EVENTS.SELECTION_CHANGED:
          this.handleSelectionChanged(payload, userId);
          break;
          
        case COLLAB_EVENTS.OPERATION_CONFLICT:
          this.handleOperationConflict(payload);
          break;
          
        case COLLAB_EVENTS.OPERATION_RESOLVED:
          this.handleOperationResolved(payload);
          break;
          
        case COLLAB_EVENTS.HISTORY_UPDATED:
          this.handleHistoryUpdated(payload);
          break;
          
        default:
          console.warn('未知的协作消息类型:', type);
      }
      
      // 触发对应的事件
      this.emit(type, { ...payload, userId, timestamp, operationId });
      
    } catch (error) {
      console.error('处理协作消息失败', error, event.data);
    }
  }

  /**
   * 发送协作消息
   */
  sendMessage(type, payload, operationId = null) {
    if (!this.isConnected || !this.ws) {
      console.warn('协作服务未连接，无法发送消息');
      return false;
    }
    
    try {
      const message = {
        type,
        payload,
        userId: this.userId,
        sessionId: this.sessionId,
        roomId: this.roomId,
        timestamp: Date.now(),
        operationId: operationId || this.generateOperationId()
      };
      
      this.ws.send(JSON.stringify(message));
      return true;
      
    } catch (error) {
      console.error('发送协作消息失败', error);
      return false;
    }
  }

  /**
   * 生成操作ID
   */
  generateOperationId() {
    return `${this.userId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 处理用户加入
   */
  handleUserJoined(userData) {
    this.users.set(userData.userId, userData);
    console.log('用户加入:', userData);
  }

  /**
   * 处理用户离开
   */
  handleUserLeft(userData) {
    this.users.delete(userData.userId);
    console.log('用户离开:', userData);
  }

  /**
   * 处理用户更新
   */
  handleUserUpdated(userData) {
    this.users.set(userData.userId, { ...this.users.get(userData.userId), ...userData });
  }

  /**
   * 处理画布操作
   */
  handleCanvasOperation(type, payload, userId) {
    console.log('处理画布操作:', type, payload, '来自用户:', userId);
    
    // 这里可以添加操作冲突检测和解决逻辑
    if (this.conflictResolver) {
      const conflict = this.conflictResolver.detectConflict(type, payload, userId);
      if (conflict) {
        this.sendMessage(COLLAB_EVENTS.OPERATION_CONFLICT, conflict);
        return;
      }
    }
  }

  /**
   * 处理选择变化
   */
  handleSelectionChanged(selection, userId) {
    console.log('用户选择变化:', userId, selection);
    
    // 更新用户选择状态
    const user = this.users.get(userId);
    if (user) {
      user.selection = selection;
      this.users.set(userId, user);
    }
  }

  /**
   * 处理操作冲突
   */
  handleOperationConflict(conflict) {
    console.log('检测到操作冲突:', conflict);
    
    // 触发冲突解决流程
    if (this.conflictResolver) {
      const resolution = this.conflictResolver.resolveConflict(conflict);
      if (resolution) {
        this.sendMessage(COLLAB_EVENTS.OPERATION_RESOLVED, resolution);
      }
    }
  }

  /**
   * 处理操作解决
   */
  handleOperationResolved(resolution) {
    console.log('操作冲突已解决:', resolution);
    
    // 应用解决方案
    if (resolution.apply) {
      // 这里可以应用解决方案到本地状态
    }
  }

  /**
   * 处理历史更新
   */
  handleHistoryUpdated(history) {
    console.log('协作历史更新:', history);
  }

  /**
   * 发送画布操作
   */
  sendCanvasOperation(operationType, elementData) {
    return this.sendMessage(operationType, elementData);
  }

  /**
   * 发送选择变化
   */
  sendSelectionChange(selection) {
    return this.sendMessage(COLLAB_EVENTS.SELECTION_CHANGED, selection);
  }

  /**
   * 发送画布状态变化
   */
  sendCanvasStateChange(canvasState) {
    return this.sendMessage(COLLAB_EVENTS.CANVAS_STATE_CHANGED, canvasState);
  }

  /**
   * 获取当前房间用户列表
   */
  getUsers() {
    return Array.from(this.users.values());
  }

  /**
   * 获取指定用户信息
   */
  getUser(userId) {
    return this.users.get(userId);
  }

  /**
   * 设置冲突解决器
   */
  setConflictResolver(resolver) {
    this.conflictResolver = resolver;
  }

  /**
   * 事件监听
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, new Set());
    }
    this.eventListeners.get(event).add(callback);
  }

  /**
   * 取消事件监听
   */
  off(event, callback) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).delete(callback);
    }
  }

  /**
   * 触发事件
   */
  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('执行事件回调失败', error);
        }
      });
    }
  }
}

// 创建单例实例
const collaborationService = new CollaborationService();

export { CollaborationService, COLLAB_EVENTS, OPERATION_TYPES };
export default collaborationService;