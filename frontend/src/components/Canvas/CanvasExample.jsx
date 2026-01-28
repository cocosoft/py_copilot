import React, { useState, useCallback } from 'react';
import Canvas from './Canvas';
import CanvasElement from './CanvasElement';
import DragManagerProvider, { useDragManager, SelectionBox, DragGuides } from './DragManager';
import { generateId } from './utils';
import './CanvasExample.css';

/**
 * 画布使用示例组件
 * 演示完整的画布功能
 */
const CanvasExample = () => {
  const [elements, setElements] = useState([
    {
      id: generateId('node'),
      type: 'start',
      x: 100,
      y: 100,
      width: 120,
      height: 80,
      title: '开始节点',
      status: 'idle'
    },
    {
      id: generateId('node'),
      type: 'task',
      x: 300,
      y: 100,
      width: 120,
      height: 80,
      title: '数据处理',
      status: 'running'
    },
    {
      id: generateId('node'),
      type: 'decision',
      x: 500,
      y: 100,
      width: 120,
      height: 80,
      title: '条件判断',
      status: 'idle'
    },
    {
      id: generateId('node'),
      type: 'end',
      x: 700,
      y: 100,
      width: 120,
      height: 80,
      title: '结束节点',
      status: 'idle'
    },
    {
      id: generateId('text'),
      type: 'text',
      x: 200,
      y: 250,
      width: 200,
      height: 40,
      text: '这是一个文本注释'
    }
  ]);

  const [connections, setConnections] = useState([
    {
      id: generateId('conn'),
      from: { x: 120, y: 140 },
      to: { x: 300, y: 140 },
      type: 'bezier'
    },
    {
      id: generateId('conn'),
      from: { x: 420, y: 140 },
      to: { x: 500, y: 140 },
      type: 'bezier'
    },
    {
      id: generateId('conn'),
      from: { x: 620, y: 140 },
      to: { x: 700, y: 140 },
      type: 'bezier'
    }
  ]);

  const [selectedIds, setSelectedIds] = useState([]);
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  // 处理元素选择
  const handleElementSelect = useCallback((id, event) => {
    if (event.ctrlKey || event.metaKey) {
      // 多选
      setSelectedIds(prev => 
        prev.includes(id) 
          ? prev.filter(selectedId => selectedId !== id)
          : [...prev, id]
      );
    } else {
      // 单选
      setSelectedIds([id]);
    }
  }, []);

  // 处理元素移动
  const handleElementMove = useCallback((id, delta) => {
    setElements(prev => 
      prev.map(element => 
        element.id === id 
          ? { ...element, x: element.x + delta[0], y: element.y + delta[1] }
          : element
      )
    );

    // 更新相关的连接线
    setConnections(prev => 
      prev.map(connection => {
        // 这里简化处理，实际应用中需要更复杂的逻辑
        return connection;
      })
    );
  }, []);

  // 处理缩放变化
  const handleScaleChange = useCallback((newScale) => {
    setScale(newScale);
    console.log('画布缩放:', newScale);
  }, []);

  // 处理位置变化
  const handlePositionChange = useCallback((newPosition) => {
    setPosition(newPosition);
    console.log('画布位置:', newPosition);
  }, []);

  // 添加新节点
  const addNode = useCallback((type, x, y) => {
    const newNode = {
      id: generateId('node'),
      type,
      x: x || 100,
      y: y || 100,
      width: 120,
      height: 80,
      title: `${type}节点`,
      status: 'idle'
    };
    
    setElements(prev => [...prev, newNode]);
    setSelectedIds([newNode.id]);
  }, []);

  // 删除选中元素
  const deleteSelected = useCallback(() => {
    setElements(prev => prev.filter(element => !selectedIds.includes(element.id)));
    setConnections(prev => prev.filter(connection => !selectedIds.includes(connection.id)));
    setSelectedIds([]);
  }, [selectedIds]);

  // 复制选中元素
  const copySelected = useCallback(() => {
    const selectedElements = elements.filter(element => selectedIds.includes(element.id));
    const newElements = selectedElements.map(element => ({
      ...element,
      id: generateId('node'),
      x: element.x + 20,
      y: element.y + 20
    }));
    
    setElements(prev => [...prev, ...newElements]);
    setSelectedIds(newElements.map(el => el.id));
  }, [elements, selectedIds]);

  return (
    <DragManagerProvider>
      <div className="canvas-example">
        {/* 画布工具栏 */}
        <div className="canvas-toolbar">
          <div className="toolbar-group">
            <button 
              className="toolbar-button"
              onClick={() => addNode('start')}
              title="添加开始节点"
            >
              ▶️ 开始
            </button>
            <button 
              className="toolbar-button"
              onClick={() => addNode('task')}
              title="添加任务节点"
            >
              ⚙️ 任务
            </button>
            <button 
              className="toolbar-button"
              onClick={() => addNode('decision')}
              title="添加判断节点"
            >
              ❓ 判断
            </button>
            <button 
              className="toolbar-button"
              onClick={() => addNode('end')}
              title="添加结束节点"
            >
              ⏹️ 结束
            </button>
          </div>
          
          <div className="toolbar-group">
            <button 
              className="toolbar-button"
              onClick={copySelected}
              disabled={selectedIds.length === 0}
              title="复制选中元素"
            >
              📋 复制
            </button>
            <button 
              className="toolbar-button toolbar-button--danger"
              onClick={deleteSelected}
              disabled={selectedIds.length === 0}
              title="删除选中元素"
            >
              🗑️ 删除
            </button>
          </div>
          
          <div className="toolbar-group">
            <span className="toolbar-info">
              选中: {selectedIds.length} 个元素
            </span>
            <span className="toolbar-info">
              缩放: {Math.round(scale * 100)}%
            </span>
          </div>
        </div>

        {/* 画布区域 */}
        <div className="canvas-area">
          <Canvas
            width={2000}
            height={2000}
            scale={scale}
            onScaleChange={handleScaleChange}
            onPositionChange={handlePositionChange}
            gridEnabled={true}
            panEnabled={true}
            zoomEnabled={true}
            className="canvas-example__canvas"
          >
            {/* 渲染连接线 */}
            {connections.map(connection => (
              <CanvasElement.Connection
                key={connection.id}
                id={connection.id}
                from={connection.from}
                to={connection.to}
                type={connection.type}
                selected={selectedIds.includes(connection.id)}
                onSelect={handleElementSelect}
              />
            ))}

            {/* 渲染节点元素 */}
            {elements.map(element => (
              <CanvasElement.Node
                key={element.id}
                id={element.id}
                x={element.x}
                y={element.y}
                width={element.width}
                height={element.height}
                type={element.type}
                title={element.title}
                status={element.status}
                selected={selectedIds.includes(element.id)}
                onSelect={handleElementSelect}
                onMove={handleElementMove}
                inputs={[1]}
                outputs={[1]}
              />
            ))}

            {/* 渲染文本元素 */}
            {elements
              .filter(element => element.type === 'text')
              .map(element => (
                <CanvasElement.Text
                  key={element.id}
                  id={element.id}
                  x={element.x}
                  y={element.y}
                  width={element.width}
                  height={element.height}
                  text={element.text}
                  selected={selectedIds.includes(element.id)}
                  onSelect={handleElementSelect}
                  onMove={handleElementMove}
                  resizable={true}
                />
              ))}
          </Canvas>
        </div>

        {/* 画布状态栏 */}
        <div className="canvas-statusbar">
          <span>位置: X={Math.round(position.x)}, Y={Math.round(position.y)}</span>
          <span>缩放: {Math.round(scale * 100)}%</span>
          <span>元素数量: {elements.length}</span>
          <span>连接线: {connections.length}</span>
        </div>
      </div>
    </DragManagerProvider>
  );
};

/**
 * 工作流画布示例
 */
const WorkflowCanvasExample = () => {
  const [workflow, setWorkflow] = useState({
    name: '示例工作流',
    description: '这是一个演示工作流',
    nodes: [],
    connections: []
  });

  const [isRunning, setIsRunning] = useState(false);

  // 模拟工作流执行
  const runWorkflow = useCallback(async () => {
    setIsRunning(true);
    
    // 模拟执行过程
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setIsRunning(false);
    console.log('工作流执行完成');
  }, []);

  return (
    <div className="workflow-canvas-example">
      <div className="workflow-header">
        <h2>{workflow.name}</h2>
        <p>{workflow.description}</p>
        
        <div className="workflow-controls">
          <button 
            className="workflow-button workflow-button--primary"
            onClick={runWorkflow}
            disabled={isRunning}
          >
            {isRunning ? '🔄 执行中...' : '▶️ 执行工作流'}
          </button>
          
          <button className="workflow-button">
            💾 保存
          </button>
          
          <button className="workflow-button">
            📤 导出
          </button>
        </div>
      </div>

      <CanvasExample />
    </div>
  );
};

export { CanvasExample, WorkflowCanvasExample };
export default CanvasExample;