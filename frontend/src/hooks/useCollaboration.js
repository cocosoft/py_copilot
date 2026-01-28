import { useState, useEffect, useCallback, useRef } from 'react';
import collaborationService, { COLLAB_EVENTS, OPERATION_TYPES } from '../services/collaborationService';
import conflictResolver from '../services/conflictResolver';
import collaborationHistory from '../services/collaborationHistory';

/**
 * 实时协作Hook
 */
const useCollaboration = (canvasState, elements, connections, selectedIds) => {
  const [collaborationState, setCollaborationState] = useState({
    isConnected: false,
    users: [],
    currentUser: null,
    roomId: null,
    sessionId: null,
    conflicts: [],
    historyStats: {}
  });

  const canvasStateRef = useRef(canvasState);
  const elementsRef = useRef(elements);
  const connectionsRef = useRef(connections);
  const selectedIdsRef = useRef(selectedIds);

  // 更新refs
  useEffect(() => {
    canvasStateRef.current = canvasState;
  }, [canvasState]);

  useEffect(() => {
    elementsRef.current = elements;
  }, [elements]);

  useEffect(() => {
    connectionsRef.current = connections;
  }, [connections]);

  useEffect(() => {
    selectedIdsRef.current = selectedIds;
  }, [selectedIds]);

  /**
   * 连接到协作房间
   */
  const connectToRoom = useCallback(async (serverUrl, userId, roomId) => {
    try {
      const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      await collaborationService.connect(serverUrl, userId, sessionId, roomId);
      
      // 设置冲突解决器
      collaborationService.setConflictResolver(conflictResolver);
      
      // 开始记录历史
      collaborationHistory.startRecording();
      
      setCollaborationState(prev => ({
        ...prev,
        isConnected: true,
        currentUser: { userId, sessionId },
        roomId,
        sessionId
      }));
      
      console.log('成功连接到协作房间:', roomId);
      
    } catch (error) {
      console.error('连接协作房间失败:', error);
      throw error;
    }
  }, []);

  /**
   * 断开连接
   */
  const disconnectFromRoom = useCallback(() => {
    collaborationService.disconnect();
    collaborationHistory.stopRecording();
    
    setCollaborationState(prev => ({
      ...prev,
      isConnected: false,
      users: [],
      conflicts: []
    }));
    
    console.log('已断开协作连接');
  }, []);

  /**
   * 发送画布操作
   */
  const sendCanvasOperation = useCallback((operationType, operationData) => {
    if (!collaborationState.isConnected) {
      console.warn('未连接到协作房间，无法发送操作');
      return false;
    }

    const success = collaborationService.sendCanvasOperation(operationType, operationData);
    
    if (success) {
      // 记录操作到历史
      collaborationHistory.recordOperation({
        action: operationType,
        data: operationData,
        userId: collaborationState.currentUser.userId,
        sessionId: collaborationState.sessionId,
        roomId: collaborationState.roomId,
        timestamp: Date.now()
      });
      
      // 记录到冲突解决器
      conflictResolver.recordOperation(operationType, operationData, collaborationState.currentUser.userId);
    }
    
    return success;
  }, [collaborationState]);

  /**
   * 发送选择变化
   */
  const sendSelectionChange = useCallback((selection) => {
    if (!collaborationState.isConnected) return false;
    
    return collaborationService.sendSelectionChange(selection);
  }, [collaborationState]);

  /**
   * 发送画布状态变化
   */
  const sendCanvasStateChange = useCallback((canvasState) => {
    if (!collaborationState.isConnected) return false;
    
    return collaborationService.sendCanvasStateChange(canvasState);
  }, [collaborationState]);

  /**
   * 处理远程操作
   */
  const handleRemoteOperation = useCallback((operation) => {
    console.log('处理远程操作:', operation);
    
    // 这里应该根据操作类型更新本地状态
    // 例如：添加元素、更新元素、删除元素等
    
    // 触发操作应用事件
    window.dispatchEvent(new CustomEvent('collaboration-operation', {
      detail: operation
    }));
  }, []);

  /**
   * 处理用户状态变化
   */
  const handleUserStateChange = useCallback((users) => {
    setCollaborationState(prev => ({
      ...prev,
      users
    }));
  }, []);

  /**
   * 处理操作冲突
   */
  const handleOperationConflict = useCallback((conflict) => {
    setCollaborationState(prev => ({
      ...prev,
      conflicts: [...prev.conflicts, conflict]
    }));
    
    // 显示冲突解决界面
    window.dispatchEvent(new CustomEvent('collaboration-conflict', {
      detail: conflict
    }));
  }, []);

  /**
   * 解决冲突
   */
  const resolveConflict = useCallback((conflictId, resolution) => {
    setCollaborationState(prev => ({
      ...prev,
      conflicts: prev.conflicts.filter(c => c.id !== conflictId)
    }));
    
    // 发送冲突解决结果
    collaborationService.sendMessage(COLLAB_EVENTS.OPERATION_RESOLVED, {
      conflictId,
      resolution
    });
  }, []);

  /**
   * 更新历史统计
   */
  const updateHistoryStats = useCallback(() => {
    const stats = collaborationHistory.getStats();
    setCollaborationState(prev => ({
      ...prev,
      historyStats: stats
    }));
  }, []);

  // 设置事件监听器
  useEffect(() => {
    if (!collaborationState.isConnected) return;

    // 用户加入事件
    collaborationService.on(COLLAB_EVENTS.USER_JOINED, (userData) => {
      console.log('用户加入:', userData);
      const users = collaborationService.getUsers();
      handleUserStateChange(users);
    });

    // 用户离开事件
    collaborationService.on(COLLAB_EVENTS.USER_LEFT, (userData) => {
      console.log('用户离开:', userData);
      const users = collaborationService.getUsers();
      handleUserStateChange(users);
    });

    // 画布操作事件
    const operationEvents = [
      COLLAB_EVENTS.ELEMENT_ADDED,
      COLLAB_EVENTS.ELEMENT_UPDATED,
      COLLAB_EVENTS.ELEMENT_REMOVED,
      COLLAB_EVENTS.CONNECTION_ADDED,
      COLLAB_EVENTS.CONNECTION_UPDATED,
      COLLAB_EVENTS.CONNECTION_REMOVED
    ];

    operationEvents.forEach(event => {
      collaborationService.on(event, (operation) => {
        handleRemoteOperation({
          type: event,
          ...operation
        });
      });
    });

    // 选择变化事件
    collaborationService.on(COLLAB_EVENTS.SELECTION_CHANGED, (selection) => {
      console.log('远程选择变化:', selection);
      // 更新远程用户的选择状态
    });

    // 操作冲突事件
    collaborationService.on(COLLAB_EVENTS.OPERATION_CONFLICT, (conflict) => {
      handleOperationConflict(conflict);
    });

    // 历史更新事件
    collaborationService.on(COLLAB_EVENTS.HISTORY_UPDATED, (history) => {
      updateHistoryStats();
    });

    // 连接状态事件
    collaborationService.on(COLLAB_EVENTS.CONNECT, () => {
      setCollaborationState(prev => ({ ...prev, isConnected: true }));
    });

    collaborationService.on(COLLAB_EVENTS.DISCONNECT, () => {
      setCollaborationState(prev => ({ ...prev, isConnected: false }));
    });

    // 清理事件监听器
    return () => {
      operationEvents.forEach(event => {
        collaborationService.off(event);
      });
      
      collaborationService.off(COLLAB_EVENTS.USER_JOINED);
      collaborationService.off(COLLAB_EVENTS.USER_LEFT);
      collaborationService.off(COLLAB_EVENTS.SELECTION_CHANGED);
      collaborationService.off(COLLAB_EVENTS.OPERATION_CONFLICT);
      collaborationService.off(COLLAB_EVENTS.HISTORY_UPDATED);
      collaborationService.off(COLLAB_EVENTS.CONNECT);
      collaborationService.off(COLLAB_EVENTS.DISCONNECT);
    };
  }, [collaborationState.isConnected, handleRemoteOperation, handleUserStateChange, handleOperationConflict, updateHistoryStats]);

  // 定期更新历史统计
  useEffect(() => {
    if (!collaborationState.isConnected) return;

    const interval = setInterval(() => {
      updateHistoryStats();
    }, 5000); // 每5秒更新一次

    return () => clearInterval(interval);
  }, [collaborationState.isConnected, updateHistoryStats]);

  /**
   * 导出协作历史
   */
  const exportHistory = useCallback((format = 'json') => {
    return collaborationHistory.exportHistory(format);
  }, []);

  /**
   * 导入协作历史
   */
  const importHistory = useCallback((data) => {
    return collaborationHistory.importHistory(data);
  }, []);

  /**
   * 清空协作历史
   */
  const clearHistory = useCallback(() => {
    collaborationHistory.clearHistory();
    updateHistoryStats();
  }, [updateHistoryStats]);

  /**
   * 回放历史
   */
  const replayHistory = useCallback((startTime, endTime, speed = 1) => {
    collaborationHistory.replayHistory(startTime, endTime, speed);
  }, []);

  /**
   * 获取用户信息
   */
  const getUserInfo = useCallback((userId) => {
    return collaborationService.getUser(userId);
  }, []);

  /**
   * 更新用户状态
   */
  const updateUserStatus = useCallback((status) => {
    if (!collaborationState.isConnected) return false;
    
    return collaborationService.sendMessage(COLLAB_EVENTS.USER_UPDATED, {
      userId: collaborationState.currentUser.userId,
      status,
      timestamp: Date.now()
    });
  }, [collaborationState]);

  return {
    // 状态
    collaborationState,
    
    // 连接管理
    connectToRoom,
    disconnectFromRoom,
    
    // 操作发送
    sendCanvasOperation,
    sendSelectionChange,
    sendCanvasStateChange,
    
    // 冲突解决
    resolveConflict,
    
    // 历史管理
    exportHistory,
    importHistory,
    clearHistory,
    replayHistory,
    
    // 用户管理
    getUserInfo,
    updateUserStatus
  };
};

export default useCollaboration;