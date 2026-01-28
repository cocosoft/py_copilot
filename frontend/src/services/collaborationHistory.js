// 协作历史管理器

/**
 * 历史记录类型
 */
export const HISTORY_TYPES = {
  OPERATION: 'operation',
  SNAPSHOT: 'snapshot',
  CHECKPOINT: 'checkpoint',
  UNDO: 'undo',
  REDO: 'redo'
};

/**
 * 历史记录操作
 */
export const HISTORY_ACTIONS = {
  ADD: 'add',
  UPDATE: 'update',
  DELETE: 'delete',
  MOVE: 'move',
  RESIZE: 'resize',
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  SELECT: 'select',
  DESELECT: 'deselect'
};

/**
 * 协作历史管理器类
 */
class CollaborationHistory {
  constructor() {
    this.history = [];
    this.currentIndex = -1;
    this.maxHistorySize = 1000;
    this.snapshotInterval = 60000; // 1分钟
    this.checkpointInterval = 300000; // 5分钟
    this.lastSnapshotTime = 0;
    this.lastCheckpointTime = 0;
    this.undoStack = [];
    this.redoStack = [];
    this.isRecording = true;
  }

  /**
   * 开始记录历史
   */
  startRecording() {
    this.isRecording = true;
    console.log('开始记录协作历史');
  }

  /**
   * 停止记录历史
   */
  stopRecording() {
    this.isRecording = false;
    console.log('停止记录协作历史');
  }

  /**
   * 记录操作到历史
   */
  recordOperation(operation) {
    if (!this.isRecording) return;

    const historyEntry = {
      id: this.generateHistoryId(),
      type: HISTORY_TYPES.OPERATION,
      action: operation.action,
      data: operation.data,
      userId: operation.userId,
      timestamp: operation.timestamp || Date.now(),
      operationId: operation.operationId,
      sessionId: operation.sessionId,
      roomId: operation.roomId
    };

    // 如果当前不在历史记录的末尾，截断后面的记录
    if (this.currentIndex < this.history.length - 1) {
      this.history = this.history.slice(0, this.currentIndex + 1);
    }

    // 添加新记录
    this.history.push(historyEntry);
    this.currentIndex = this.history.length - 1;

    // 限制历史记录大小
    if (this.history.length > this.maxHistorySize) {
      this.history = this.history.slice(-this.maxHistorySize);
      this.currentIndex = this.history.length - 1;
    }

    // 清理重做栈
    this.redoStack = [];

    console.log('记录操作到历史:', historyEntry);

    // 检查是否需要创建快照
    this.checkSnapshot();
    
    // 检查是否需要创建检查点
    this.checkCheckpoint();

    return historyEntry;
  }

  /**
   * 生成历史记录ID
   */
  generateHistoryId() {
    return `history-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 检查是否需要创建快照
   */
  checkSnapshot() {
    const now = Date.now();
    if (now - this.lastSnapshotTime >= this.snapshotInterval) {
      this.createSnapshot();
      this.lastSnapshotTime = now;
    }
  }

  /**
   * 检查是否需要创建检查点
   */
  checkCheckpoint() {
    const now = Date.now();
    if (now - this.lastCheckpointTime >= this.checkpointInterval) {
      this.createCheckpoint();
      this.lastCheckpointTime = now;
    }
  }

  /**
   * 创建画布快照
   */
  createSnapshot(canvasState = null) {
    const snapshot = {
      id: this.generateHistoryId(),
      type: HISTORY_TYPES.SNAPSHOT,
      timestamp: Date.now(),
      data: {
        canvasState,
        historyLength: this.history.length,
        currentIndex: this.currentIndex
      }
    };

    this.history.push(snapshot);
    this.currentIndex = this.history.length - 1;

    console.log('创建画布快照:', snapshot);
    return snapshot;
  }

  /**
   * 创建检查点
   */
  createCheckpoint() {
    const checkpoint = {
      id: this.generateHistoryId(),
      type: HISTORY_TYPES.CHECKPOINT,
      timestamp: Date.now(),
      data: {
        history: [...this.history],
        currentIndex: this.currentIndex,
        undoStack: [...this.undoStack],
        redoStack: [...this.redoStack]
      }
    };

    console.log('创建检查点:', checkpoint);
    return checkpoint;
  }

  /**
   * 撤销操作
   */
  undo() {
    if (this.currentIndex < 0) {
      console.log('没有可撤销的操作');
      return null;
    }

    // 找到上一个操作记录
    let undoIndex = this.currentIndex;
    while (undoIndex >= 0 && this.history[undoIndex].type !== HISTORY_TYPES.OPERATION) {
      undoIndex--;
    }

    if (undoIndex < 0) {
      console.log('没有可撤销的操作');
      return null;
    }

    const operationToUndo = this.history[undoIndex];
    
    // 计算撤销操作
    const undoOperation = this.calculateUndoOperation(operationToUndo);
    
    if (undoOperation) {
      // 记录撤销操作
      const undoEntry = {
        id: this.generateHistoryId(),
        type: HISTORY_TYPES.UNDO,
        action: 'undo',
        data: undoOperation,
        timestamp: Date.now(),
        originalOperation: operationToUndo
      };

      this.undoStack.push(undoEntry);
      this.currentIndex = undoIndex - 1;

      console.log('执行撤销操作:', undoOperation);
      return undoOperation;
    }

    return null;
  }

  /**
   * 重做操作
   */
  redo() {
    if (this.currentIndex >= this.history.length - 1) {
      console.log('没有可重做的操作');
      return null;
    }

    // 找到下一个操作记录
    let redoIndex = this.currentIndex + 1;
    while (redoIndex < this.history.length && this.history[redoIndex].type !== HISTORY_TYPES.OPERATION) {
      redoIndex++;
    }

    if (redoIndex >= this.history.length) {
      console.log('没有可重做的操作');
      return null;
    }

    const operationToRedo = this.history[redoIndex];
    
    // 计算重做操作
    const redoOperation = this.calculateRedoOperation(operationToRedo);
    
    if (redoOperation) {
      // 记录重做操作
      const redoEntry = {
        id: this.generateHistoryId(),
        type: HISTORY_TYPES.REDO,
        action: 'redo',
        data: redoOperation,
        timestamp: Date.now(),
        originalOperation: operationToRedo
      };

      this.redoStack.push(redoEntry);
      this.currentIndex = redoIndex;

      console.log('执行重做操作:', redoOperation);
      return redoOperation;
    }

    return null;
  }

  /**
   * 计算撤销操作
   */
  calculateUndoOperation(operation) {
    switch (operation.action) {
      case HISTORY_ACTIONS.ADD:
        return {
          action: HISTORY_ACTIONS.DELETE,
          elementId: operation.data.elementId,
          elementType: operation.data.elementType
        };
        
      case HISTORY_ACTIONS.DELETE:
        return {
          action: HISTORY_ACTIONS.ADD,
          elementData: operation.data.originalData
        };
        
      case HISTORY_ACTIONS.UPDATE:
        return {
          action: HISTORY_ACTIONS.UPDATE,
          elementId: operation.data.elementId,
          updates: operation.data.originalState
        };
        
      case HISTORY_ACTIONS.MOVE:
        return {
          action: HISTORY_ACTIONS.MOVE,
          elementId: operation.data.elementId,
          from: operation.data.to,
          to: operation.data.from
        };
        
      default:
        return null;
    }
  }

  /**
   * 计算重做操作
   */
  calculateRedoOperation(operation) {
    // 重做操作就是原始操作本身
    return {
      action: operation.action,
      ...operation.data
    };
  }

  /**
   * 获取历史记录
   */
  getHistory(startIndex = 0, endIndex = this.history.length) {
    return this.history.slice(startIndex, endIndex);
  }

  /**
   * 获取指定时间范围内的历史记录
   */
  getHistoryByTimeRange(startTime, endTime) {
    return this.history.filter(entry => 
      entry.timestamp >= startTime && entry.timestamp <= endTime
    );
  }

  /**
   * 获取用户的操作历史
   */
  getUserHistory(userId, limit = 100) {
    const userOperations = this.history.filter(entry => 
      entry.userId === userId && entry.type === HISTORY_TYPES.OPERATION
    );
    
    return userOperations.slice(-limit);
  }

  /**
   * 获取元素的操作历史
   */
  getElementHistory(elementId, limit = 50) {
    const elementOperations = this.history.filter(entry => {
      if (entry.type !== HISTORY_TYPES.OPERATION) return false;
      
      const elementIdInData = entry.data.elementId || entry.data.id;
      return elementIdInData === elementId;
    });
    
    return elementOperations.slice(-limit);
  }

  /**
   * 搜索历史记录
   */
  searchHistory(keyword, field = 'all') {
    return this.history.filter(entry => {
      if (field === 'all') {
        return JSON.stringify(entry).toLowerCase().includes(keyword.toLowerCase());
      } else {
        const value = entry[field];
        return value && value.toString().toLowerCase().includes(keyword.toLowerCase());
      }
    });
  }

  /**
   * 导出历史记录
   */
  exportHistory(format = 'json') {
    const exportData = {
      version: '1.0.0',
      exportedAt: new Date().toISOString(),
      totalEntries: this.history.length,
      currentIndex: this.currentIndex,
      history: this.history
    };

    switch (format) {
      case 'json':
        return JSON.stringify(exportData, null, 2);
        
      case 'csv':
        return this.exportToCSV(exportData);
        
      default:
        throw new Error(`不支持的导出格式: ${format}`);
    }
  }

  /**
   * 导出为CSV格式
   */
  exportToCSV(data) {
    const headers = ['时间戳', '类型', '操作', '用户ID', '元素ID', '数据'];
    const rows = data.history.map(entry => [
      new Date(entry.timestamp).toISOString(),
      entry.type,
      entry.action || '',
      entry.userId || '',
      (entry.data && (entry.data.elementId || entry.data.id)) || '',
      JSON.stringify(entry.data || {})
    ]);

    const csvContent = [headers, ...rows]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n');

    return csvContent;
  }

  /**
   * 导入历史记录
   */
  importHistory(data) {
    try {
      const importData = typeof data === 'string' ? JSON.parse(data) : data;
      
      if (importData.version !== '1.0.0') {
        throw new Error('不支持的导入数据版本');
      }
      
      this.history = importData.history || [];
      this.currentIndex = importData.currentIndex || -1;
      
      console.log('成功导入历史记录:', this.history.length, '条记录');
      return true;
      
    } catch (error) {
      console.error('导入历史记录失败:', error);
      return false;
    }
  }

  /**
   * 清空历史记录
   */
  clearHistory() {
    this.history = [];
    this.currentIndex = -1;
    this.undoStack = [];
    this.redoStack = [];
    console.log('清空历史记录');
  }

  /**
   * 获取历史统计信息
   */
  getStats() {
    const now = Date.now();
    const oneHourAgo = now - 3600000;
    const oneDayAgo = now - 86400000;

    const stats = {
      totalOperations: this.history.filter(entry => entry.type === HISTORY_TYPES.OPERATION).length,
      totalSnapshots: this.history.filter(entry => entry.type === HISTORY_TYPES.SNAPSHOT).length,
      totalCheckpoints: this.history.filter(entry => entry.type === HISTORY_TYPES.CHECKPOINT).length,
      operationsLastHour: this.history.filter(entry => 
        entry.type === HISTORY_TYPES.OPERATION && entry.timestamp > oneHourAgo
      ).length,
      operationsLastDay: this.history.filter(entry => 
        entry.type === HISTORY_TYPES.OPERATION && entry.timestamp > oneDayAgo
      ).length,
      uniqueUsers: new Set(this.history
        .filter(entry => entry.userId)
        .map(entry => entry.userId)
      ).size,
      canUndo: this.currentIndex >= 0,
      canRedo: this.currentIndex < this.history.length - 1,
      undoStackSize: this.undoStack.length,
      redoStackSize: this.redoStack.length
    };

    return stats;
  }

  /**
   * 回放历史记录
   */
  replayHistory(startTime, endTime, speed = 1) {
    const operations = this.getHistoryByTimeRange(startTime, endTime)
      .filter(entry => entry.type === HISTORY_TYPES.OPERATION)
      .sort((a, b) => a.timestamp - b.timestamp);

    if (operations.length === 0) {
      console.log('指定时间范围内没有操作记录');
      return;
    }

    console.log(`开始回放 ${operations.length} 个操作，速度: ${speed}x`);

    let currentIndex = 0;
    const startTimestamp = operations[0].timestamp;

    const replayNext = () => {
      if (currentIndex >= operations.length) {
        console.log('回放完成');
        return;
      }

      const operation = operations[currentIndex];
      const delay = (operation.timestamp - startTimestamp) / speed;

      setTimeout(() => {
        console.log('回放操作:', operation);
        // 这里应该触发操作应用事件
        currentIndex++;
        replayNext();
      }, delay);
    };

    replayNext();
  }
}

// 创建单例实例
const collaborationHistory = new CollaborationHistory();

export { CollaborationHistory, HISTORY_TYPES, HISTORY_ACTIONS };
export default collaborationHistory;