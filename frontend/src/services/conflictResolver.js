// 操作冲突解决器

/**
 * 冲突类型定义
 */
export const CONFLICT_TYPES = {
  // 元素操作冲突
  ELEMENT_MOVE_CONFLICT: 'element_move_conflict',
  ELEMENT_RESIZE_CONFLICT: 'element_resize_conflict',
  ELEMENT_DELETE_CONFLICT: 'element_delete_conflict',
  
  // 连接线操作冲突
  CONNECTION_UPDATE_CONFLICT: 'connection_update_conflict',
  
  // 状态冲突
  CANVAS_STATE_CONFLICT: 'canvas_state_conflict',
  SELECTION_CONFLICT: 'selection_conflict',
  
  // 数据冲突
  DATA_VERSION_CONFLICT: 'data_version_conflict'
};

/**
 * 冲突解决策略
 */
export const RESOLUTION_STRATEGIES = {
  // 时间戳策略
  LAST_WRITE_WINS: 'last_write_wins',
  FIRST_WRITE_WINS: 'first_write_wins',
  
  // 用户优先级策略
  OWNER_PRIORITY: 'owner_priority',
  ADMIN_PRIORITY: 'admin_priority',
  
  // 操作类型策略
  DELETE_PRIORITY: 'delete_priority',
  MOVE_PRIORITY: 'move_priority',
  
  // 合并策略
  MERGE_CHANGES: 'merge_changes',
  
  // 用户选择策略
  USER_CHOICE: 'user_choice'
};

/**
 * 操作冲突解决器类
 */
class ConflictResolver {
  constructor() {
    this.strategies = new Map();
    this.operationHistory = new Map();
    this.setupDefaultStrategies();
  }

  /**
   * 设置默认解决策略
   */
  setupDefaultStrategies() {
    // 元素移动冲突 - 最后写入获胜
    this.setStrategy(CONFLICT_TYPES.ELEMENT_MOVE_CONFLICT, RESOLUTION_STRATEGIES.LAST_WRITE_WINS);
    
    // 元素调整大小冲突 - 最后写入获胜
    this.setStrategy(CONFLICT_TYPES.ELEMENT_RESIZE_CONFLICT, RESOLUTION_STRATEGIES.LAST_WRITE_WINS);
    
    // 元素删除冲突 - 删除优先
    this.setStrategy(CONFLICT_TYPES.ELEMENT_DELETE_CONFLICT, RESOLUTION_STRATEGIES.DELETE_PRIORITY);
    
    // 连接线更新冲突 - 最后写入获胜
    this.setStrategy(CONFLICT_TYPES.CONNECTION_UPDATE_CONFLICT, RESOLUTION_STRATEGIES.LAST_WRITE_WINS);
    
    // 画布状态冲突 - 最后写入获胜
    this.setStrategy(CONFLICT_TYPES.CANVAS_STATE_CONFLICT, RESOLUTION_STRATEGIES.LAST_WRITE_WINS);
    
    // 选择冲突 - 合并选择
    this.setStrategy(CONFLICT_TYPES.SELECTION_CONFLICT, RESOLUTION_STRATEGIES.MERGE_CHANGES);
    
    // 数据版本冲突 - 用户选择
    this.setStrategy(CONFLICT_TYPES.DATA_VERSION_CONFLICT, RESOLUTION_STRATEGIES.USER_CHOICE);
  }

  /**
   * 设置冲突解决策略
   */
  setStrategy(conflictType, strategy) {
    this.strategies.set(conflictType, strategy);
  }

  /**
   * 检测操作冲突
   */
  detectConflict(operationType, operationData, userId) {
    const elementId = operationData.elementId || operationData.id;
    
    if (!elementId) {
      return null; // 没有元素ID，无法检测冲突
    }
    
    // 获取元素的操作历史
    const elementHistory = this.operationHistory.get(elementId) || [];
    
    // 检查最近的冲突操作
    const recentOperations = elementHistory.filter(op => 
      Date.now() - op.timestamp < 5000 // 5秒内的操作
    );
    
    for (const recentOp of recentOperations) {
      const conflict = this.checkOperationConflict(
        operationType, 
        operationData, 
        userId,
        recentOp.type, 
        recentOp.data, 
        recentOp.userId
      );
      
      if (conflict) {
        return conflict;
      }
    }
    
    return null;
  }

  /**
   * 检查两个操作是否冲突
   */
  checkOperationConflict(op1Type, op1Data, op1User, op2Type, op2Data, op2User) {
    // 同一个用户的操作不冲突
    if (op1User === op2User) {
      return null;
    }
    
    const op1Element = op1Data.elementId || op1Data.id;
    const op2Element = op2Data.elementId || op2Data.id;
    
    // 不同元素的操作不冲突
    if (op1Element !== op2Element) {
      return null;
    }
    
    // 检查特定类型的冲突
    switch (op1Type) {
      case 'element_updated':
        if (op2Type === 'element_updated') {
          return this.detectElementUpdateConflict(op1Data, op2Data, op1User, op2User);
        } else if (op2Type === 'element_removed') {
          return this.detectUpdateDeleteConflict(op1Data, op2Data, op1User, op2User);
        }
        break;
        
      case 'element_removed':
        if (op2Type === 'element_updated') {
          return this.detectDeleteUpdateConflict(op1Data, op2Data, op1User, op2User);
        } else if (op2Type === 'element_removed') {
          return this.detectDeleteDeleteConflict(op1Data, op2Data, op1User, op2User);
        }
        break;
        
      case 'connection_updated':
        if (op2Type === 'connection_updated') {
          return this.detectConnectionUpdateConflict(op1Data, op2Data, op1User, op2User);
        }
        break;
        
      case 'canvas_state_changed':
        if (op2Type === 'canvas_state_changed') {
          return this.detectCanvasStateConflict(op1Data, op2Data, op1User, op2User);
        }
        break;
    }
    
    return null;
  }

  /**
   * 检测元素更新冲突
   */
  detectElementUpdateConflict(op1Data, op2Data, op1User, op2User) {
    const conflictAreas = [];
    
    // 检查位置冲突
    if (op1Data.x !== undefined && op2Data.x !== undefined &&
        op1Data.y !== undefined && op2Data.y !== undefined) {
      const distance = Math.sqrt(
        Math.pow(op1Data.x - op2Data.x, 2) + 
        Math.pow(op1Data.y - op2Data.y, 2)
      );
      
      if (distance > 10) { // 位置差异较大
        conflictAreas.push('position');
      }
    }
    
    // 检查尺寸冲突
    if (op1Data.width !== undefined && op2Data.width !== undefined &&
        op1Data.height !== undefined && op2Data.height !== undefined) {
      const sizeDiff = Math.abs(op1Data.width - op2Data.width) + 
                      Math.abs(op1Data.height - op2Data.height);
      
      if (sizeDiff > 20) { // 尺寸差异较大
        conflictAreas.push('size');
      }
    }
    
    if (conflictAreas.length > 0) {
      return {
        type: conflictAreas.includes('position') ? 
              CONFLICT_TYPES.ELEMENT_MOVE_CONFLICT : 
              CONFLICT_TYPES.ELEMENT_RESIZE_CONFLICT,
        elementId: op1Data.elementId || op1Data.id,
        operations: [
          { type: 'element_updated', data: op1Data, userId: op1User },
          { type: 'element_updated', data: op2Data, userId: op2User }
        ],
        conflictAreas,
        timestamp: Date.now()
      };
    }
    
    return null;
  }

  /**
   * 检测更新-删除冲突
   */
  detectUpdateDeleteConflict(updateData, deleteData, updateUser, deleteUser) {
    return {
      type: CONFLICT_TYPES.ELEMENT_DELETE_CONFLICT,
      elementId: updateData.elementId || updateData.id,
      operations: [
        { type: 'element_updated', data: updateData, userId: updateUser },
        { type: 'element_removed', data: deleteData, userId: deleteUser }
      ],
      conflictAreas: ['existence'],
      timestamp: Date.now()
    };
  }

  /**
   * 检测删除-更新冲突
   */
  detectDeleteUpdateConflict(deleteData, updateData, deleteUser, updateUser) {
    return this.detectUpdateDeleteConflict(updateData, deleteData, updateUser, deleteUser);
  }

  /**
   * 检测删除-删除冲突
   */
  detectDeleteDeleteConflict(op1Data, op2Data, op1User, op2User) {
    // 两个删除操作通常不冲突，可以同时执行
    return null;
  }

  /**
   * 检测连接线更新冲突
   */
  detectConnectionUpdateConflict(op1Data, op2Data, op1User, op2User) {
    // 检查连接线端点是否被不同用户修改
    const endpointsChanged = 
      (op1Data.from && op2Data.from && 
       (op1Data.from.x !== op2Data.from.x || op1Data.from.y !== op2Data.from.y)) ||
      (op1Data.to && op2Data.to && 
       (op1Data.to.x !== op2Data.to.x || op1Data.to.y !== op2Data.to.y));
    
    if (endpointsChanged) {
      return {
        type: CONFLICT_TYPES.CONNECTION_UPDATE_CONFLICT,
        connectionId: op1Data.connectionId || op1Data.id,
        operations: [
          { type: 'connection_updated', data: op1Data, userId: op1User },
          { type: 'connection_updated', data: op2Data, userId: op2User }
        ],
        conflictAreas: ['endpoints'],
        timestamp: Date.now()
      };
    }
    
    return null;
  }

  /**
   * 检测画布状态冲突
   */
  detectCanvasStateConflict(op1Data, op2Data, op1User, op2User) {
    // 检查缩放和位置是否冲突
    const scaleConflict = op1Data.scale !== undefined && op2Data.scale !== undefined &&
                         Math.abs(op1Data.scale - op2Data.scale) > 0.1;
    
    const positionConflict = op1Data.position && op2Data.position &&
                            (Math.abs(op1Data.position.x - op2Data.position.x) > 50 ||
                             Math.abs(op1Data.position.y - op2Data.position.y) > 50);
    
    if (scaleConflict || positionConflict) {
      return {
        type: CONFLICT_TYPES.CANVAS_STATE_CONFLICT,
        operations: [
          { type: 'canvas_state_changed', data: op1Data, userId: op1User },
          { type: 'canvas_state_changed', data: op2Data, userId: op2User }
        ],
        conflictAreas: scaleConflict && positionConflict ? ['scale', 'position'] : 
                      scaleConflict ? ['scale'] : ['position'],
        timestamp: Date.now()
      };
    }
    
    return null;
  }

  /**
   * 解决操作冲突
   */
  resolveConflict(conflict) {
    const strategy = this.strategies.get(conflict.type) || RESOLUTION_STRATEGIES.LAST_WRITE_WINS;
    
    console.log('解决冲突:', conflict.type, '使用策略:', strategy);
    
    switch (strategy) {
      case RESOLUTION_STRATEGIES.LAST_WRITE_WINS:
        return this.resolveLastWriteWins(conflict);
        
      case RESOLUTION_STRATEGIES.FIRST_WRITE_WINS:
        return this.resolveFirstWriteWins(conflict);
        
      case RESOLUTION_STRATEGIES.DELETE_PRIORITY:
        return this.resolveDeletePriority(conflict);
        
      case RESOLUTION_STRATEGIES.MERGE_CHANGES:
        return this.resolveMergeChanges(conflict);
        
      case RESOLUTION_STRATEGIES.USER_CHOICE:
        return this.resolveUserChoice(conflict);
        
      default:
        return this.resolveLastWriteWins(conflict);
    }
  }

  /**
   * 最后写入获胜策略
   */
  resolveLastWriteWins(conflict) {
    const latestOp = conflict.operations.reduce((latest, op) => {
      return op.timestamp > latest.timestamp ? op : latest;
    });
    
    return {
      conflictId: conflict.type + '-' + Date.now(),
      resolvedOperation: latestOp,
      strategy: RESOLUTION_STRATEGIES.LAST_WRITE_WINS,
      timestamp: Date.now(),
      apply: true
    };
  }

  /**
   * 最先写入获胜策略
   */
  resolveFirstWriteWins(conflict) {
    const firstOp = conflict.operations.reduce((first, op) => {
      return op.timestamp < first.timestamp ? op : first;
    });
    
    return {
      conflictId: conflict.type + '-' + Date.now(),
      resolvedOperation: firstOp,
      strategy: RESOLUTION_STRATEGIES.FIRST_WRITE_WINS,
      timestamp: Date.now(),
      apply: true
    };
  }

  /**
   * 删除优先策略
   */
  resolveDeletePriority(conflict) {
    const deleteOp = conflict.operations.find(op => op.type === 'element_removed');
    
    if (deleteOp) {
      return {
        conflictId: conflict.type + '-' + Date.now(),
        resolvedOperation: deleteOp,
        strategy: RESOLUTION_STRATEGIES.DELETE_PRIORITY,
        timestamp: Date.now(),
        apply: true
      };
    }
    
    // 如果没有删除操作，回退到最后写入获胜
    return this.resolveLastWriteWins(conflict);
  }

  /**
   * 合并变更策略
   */
  resolveMergeChanges(conflict) {
    if (conflict.type === CONFLICT_TYPES.SELECTION_CONFLICT) {
      // 合并选择：取所有操作的选择并集
      const mergedSelection = conflict.operations.reduce((selection, op) => {
        return [...new Set([...selection, ...(op.data.selection || [])])];
      }, []);
      
      return {
        conflictId: conflict.type + '-' + Date.now(),
        resolvedOperation: {
          type: 'selection_changed',
          data: { selection: mergedSelection },
          userId: 'system'
        },
        strategy: RESOLUTION_STRATEGIES.MERGE_CHANGES,
        timestamp: Date.now(),
        apply: true
      };
    }
    
    // 对于其他类型的冲突，回退到最后写入获胜
    return this.resolveLastWriteWins(conflict);
  }

  /**
   * 用户选择策略
   */
  resolveUserChoice(conflict) {
    // 这里应该显示冲突解决界面让用户选择
    // 暂时回退到最后写入获胜
    return this.resolveLastWriteWins(conflict);
  }

  /**
   * 记录操作历史
   */
  recordOperation(operationType, operationData, userId) {
    const elementId = operationData.elementId || operationData.id;
    
    if (!elementId) return;
    
    if (!this.operationHistory.has(elementId)) {
      this.operationHistory.set(elementId, []);
    }
    
    const history = this.operationHistory.get(elementId);
    history.push({
      type: operationType,
      data: operationData,
      userId,
      timestamp: Date.now()
    });
    
    // 保持历史记录数量限制
    if (history.length > 100) {
      history.splice(0, history.length - 100);
    }
  }

  /**
   * 清理过期的操作历史
   */
  cleanupOldOperations(maxAge = 300000) { // 5分钟
    const now = Date.now();
    
    for (const [elementId, history] of this.operationHistory.entries()) {
      const filteredHistory = history.filter(op => now - op.timestamp < maxAge);
      
      if (filteredHistory.length === 0) {
        this.operationHistory.delete(elementId);
      } else {
        this.operationHistory.set(elementId, filteredHistory);
      }
    }
  }

  /**
   * 获取操作历史统计
   */
  getOperationStats() {
    const stats = {
      totalElements: this.operationHistory.size,
      totalOperations: 0,
      recentOperations: 0,
      conflictCount: 0
    };
    
    const fiveMinutesAgo = Date.now() - 300000;
    
    for (const history of this.operationHistory.values()) {
      stats.totalOperations += history.length;
      stats.recentOperations += history.filter(op => op.timestamp > fiveMinutesAgo).length;
    }
    
    return stats;
  }
}

// 创建单例实例
const conflictResolver = new ConflictResolver();

// 定期清理过期操作
setInterval(() => {
  conflictResolver.cleanupOldOperations();
}, 60000); // 每分钟清理一次

export { ConflictResolver, CONFLICT_TYPES, RESOLUTION_STRATEGIES };
export default conflictResolver;