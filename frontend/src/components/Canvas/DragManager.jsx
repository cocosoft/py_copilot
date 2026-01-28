import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { throttle } from './utils';

/**
 * 拖拽管理器上下文
 */
const DragContext = createContext();

/**
 * 拖拽状态类型定义
 */
const DRAG_ACTIONS = {
  START_DRAG: 'START_DRAG',
  UPDATE_DRAG: 'UPDATE_DRAG',
  END_DRAG: 'END_DRAG',
  CLEAR_DRAG: 'CLEAR_DRAG'
};

/**
 * 拖拽状态reducer
 */
const dragReducer = (state, action) => {
  switch (action.type) {
    case DRAG_ACTIONS.START_DRAG:
      return {
        ...state,
        isDragging: true,
        dragType: action.payload.dragType,
        dragData: action.payload.dragData,
        startPosition: action.payload.startPosition,
        currentPosition: action.payload.startPosition,
        selectedElements: action.payload.selectedElements || []
      };
    
    case DRAG_ACTIONS.UPDATE_DRAG:
      return {
        ...state,
        currentPosition: action.payload.position,
        delta: {
          x: action.payload.position.x - state.startPosition.x,
          y: action.payload.position.y - state.startPosition.y
        }
      };
    
    case DRAG_ACTIONS.END_DRAG:
      return {
        ...state,
        isDragging: false,
        endPosition: action.payload.position,
        totalDelta: {
          x: action.payload.position.x - state.startPosition.x,
          y: action.payload.position.y - state.startPosition.y
        }
      };
    
    case DRAG_ACTIONS.CLEAR_DRAG:
      return {
        isDragging: false,
        dragType: null,
        dragData: null,
        startPosition: null,
        currentPosition: null,
        endPosition: null,
        delta: null,
        totalDelta: null,
        selectedElements: []
      };
    
    default:
      return state;
  }
};

/**
 * 初始拖拽状态
 */
const initialDragState = {
  isDragging: false,
  dragType: null, // 'element', 'selection', 'connection'
  dragData: null,
  startPosition: null,
  currentPosition: null,
  endPosition: null,
  delta: null,
  totalDelta: null,
  selectedElements: []
};

/**
 * 拖拽管理器提供者组件
 */
export const DragManagerProvider = ({ children }) => {
  const [dragState, dispatch] = useReducer(dragReducer, initialDragState);

  // 开始拖拽
  const startDrag = useCallback((dragType, dragData, startPosition, selectedElements = []) => {
    dispatch({
      type: DRAG_ACTIONS.START_DRAG,
      payload: {
        dragType,
        dragData,
        startPosition,
        selectedElements
      }
    });
  }, []);

  // 更新拖拽位置（节流处理）
  const updateDrag = useCallback(throttle((position) => {
    if (!dragState.isDragging) return;
    
    dispatch({
      type: DRAG_ACTIONS.UPDATE_DRAG,
      payload: { position }
    });
  }, 16), [dragState.isDragging]);

  // 结束拖拽
  const endDrag = useCallback((position) => {
    if (!dragState.isDragging) return;
    
    dispatch({
      type: DRAG_ACTIONS.END_DRAG,
      payload: { position }
    });
  }, [dragState.isDragging]);

  // 清除拖拽状态
  const clearDrag = useCallback(() => {
    dispatch({ type: DRAG_ACTIONS.CLEAR_DRAG });
  }, []);

  // 计算拖拽偏移量
  const getDragOffset = useCallback((elementId) => {
    if (!dragState.isDragging || !dragState.delta) {
      return { x: 0, y: 0 };
    }
    
    // 如果是多选拖拽，检查元素是否在选中列表中
    if (dragState.selectedElements.length > 0) {
      const isSelected = dragState.selectedElements.some(el => el.id === elementId);
      return isSelected ? dragState.delta : { x: 0, y: 0 };
    }
    
    // 单个元素拖拽
    return dragState.dragData?.id === elementId ? dragState.delta : { x: 0, y: 0 };
  }, [dragState]);

  // 检查是否正在拖拽特定元素
  const isDraggingElement = useCallback((elementId) => {
    return dragState.isDragging && 
           dragState.dragType === 'element' && 
           dragState.dragData?.id === elementId;
  }, [dragState]);

  // 检查是否正在拖拽选择框
  const isDraggingSelection = useCallback(() => {
    return dragState.isDragging && dragState.dragType === 'selection';
  }, [dragState]);

  const value = {
    dragState,
    startDrag,
    updateDrag,
    endDrag,
    clearDrag,
    getDragOffset,
    isDraggingElement,
    isDraggingSelection
  };

  return (
    <DragContext.Provider value={value}>
      {children}
    </DragContext.Provider>
  );
};

/**
 * 使用拖拽管理器的hook
 */
export const useDragManager = () => {
  const context = useContext(DragContext);
  if (!context) {
    throw new Error('useDragManager must be used within a DragManagerProvider');
  }
  return context;
};

/**
 * 选择框组件
 */
export const SelectionBox = ({ start, end, onSelectionChange }) => {
  if (!start || !end) return null;

  const width = Math.abs(end.x - start.x);
  const height = Math.abs(end.y - start.y);
  const left = Math.min(start.x, end.x);
  const top = Math.min(start.y, end.y);

  const style = {
    position: 'absolute',
    left: `${left}px`,
    top: `${top}px`,
    width: `${width}px`,
    height: `${height}px`,
    border: '2px dashed var(--ui-color-primary-500)',
    backgroundColor: 'rgba(52, 152, 219, 0.1)',
    pointerEvents: 'none',
    zIndex: 'var(--ui-z-index-modal)'
  };

  return <div className="selection-box" style={style} />;
};

/**
 * 拖拽指示器组件
 */
export const DragIndicator = ({ dragState }) => {
  if (!dragState.isDragging || !dragState.delta) return null;

  const style = {
    position: 'fixed',
    top: '10px',
    left: '10px',
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    color: 'white',
    padding: '8px 12px',
    borderRadius: '4px',
    fontSize: '12px',
    zIndex: 'var(--ui-z-index-tooltip)'
  };

  return (
    <div style={style}>
      拖拽中: Δx={Math.round(dragState.delta.x)}, Δy={Math.round(dragState.delta.y)}
    </div>
  );
};

/**
 * 拖拽辅助线组件
 */
export const DragGuides = ({ dragState, elements, gridSize = 20 }) => {
  if (!dragState.isDragging || !dragState.delta) return null;

  const guides = [];
  
  // 网格对齐辅助线
  if (dragState.currentPosition) {
    const snappedX = Math.round(dragState.currentPosition.x / gridSize) * gridSize;
    const snappedY = Math.round(dragState.currentPosition.y / gridSize) * gridSize;
    
    // 水平辅助线
    guides.push(
      <div
        key="horizontal-guide"
        style={{
          position: 'absolute',
          left: '0',
          top: `${snappedY}px`,
          width: '100%',
          height: '1px',
          backgroundColor: 'var(--ui-color-primary-500)',
          pointerEvents: 'none',
          zIndex: 'var(--ui-z-index-tooltip)'
        }}
      />
    );
    
    // 垂直辅助线
    guides.push(
      <div
        key="vertical-guide"
        style={{
          position: 'absolute',
          left: `${snappedX}px`,
          top: '0',
          width: '1px',
          height: '100%',
          backgroundColor: 'var(--ui-color-primary-500)',
          pointerEvents: 'none',
          zIndex: 'var(--ui-z-index-tooltip)'
        }}
      />
    );
  }

  // 元素对齐辅助线
  elements.forEach(element => {
    if (dragState.selectedElements.some(sel => sel.id === element.id)) return;
    
    const elementEdges = {
      left: element.x,
      right: element.x + element.width,
      top: element.y,
      bottom: element.y + element.height,
      centerX: element.x + element.width / 2,
      centerY: element.y + element.height / 2
    };
    
    // 检查是否需要对其他元素对齐
    dragState.selectedElements.forEach(selectedElement => {
      const selectedEdges = {
        left: selectedElement.x + dragState.delta.x,
        right: selectedElement.x + selectedElement.width + dragState.delta.x,
        top: selectedElement.y + dragState.delta.y,
        bottom: selectedElement.y + selectedElement.height + dragState.delta.y,
        centerX: selectedElement.x + selectedElement.width / 2 + dragState.delta.x,
        centerY: selectedElement.y + selectedElement.height / 2 + dragState.delta.y
      };
      
      // 检查各种对齐情况
      const alignments = [
        { type: 'left', condition: Math.abs(selectedEdges.left - elementEdges.left) < 5 },
        { type: 'right', condition: Math.abs(selectedEdges.right - elementEdges.right) < 5 },
        { type: 'top', condition: Math.abs(selectedEdges.top - elementEdges.top) < 5 },
        { type: 'bottom', condition: Math.abs(selectedEdges.bottom - elementEdges.bottom) < 5 },
        { type: 'centerX', condition: Math.abs(selectedEdges.centerX - elementEdges.centerX) < 5 },
        { type: 'centerY', condition: Math.abs(selectedEdges.centerY - elementEdges.centerY) < 5 }
      ];
      
      alignments.forEach(alignment => {
        if (alignment.condition) {
          guides.push(
            <div
              key={`${element.id}-${alignment.type}`}
              style={{
                position: 'absolute',
                left: alignment.type.includes('left') ? `${elementEdges.left}px` : 
                      alignment.type.includes('right') ? `${elementEdges.right}px` :
                      alignment.type.includes('centerX') ? `${elementEdges.centerX}px` : '0',
                top: alignment.type.includes('top') ? `${elementEdges.top}px` :
                     alignment.type.includes('bottom') ? `${elementEdges.bottom}px` :
                     alignment.type.includes('centerY') ? `${elementEdges.centerY}px` : '0',
                width: alignment.type.includes('X') ? '1px' : '100%',
                height: alignment.type.includes('Y') ? '1px' : '100%',
                backgroundColor: 'var(--ui-color-success-500)',
                pointerEvents: 'none',
                zIndex: 'var(--ui-z-index-tooltip)'
              }}
            />
          );
        }
      });
    });
  });

  return <>{guides}</>;
};

export default DragManagerProvider;