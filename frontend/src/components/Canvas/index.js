// 画布组件库入口文件

// 基础组件
export { default as Canvas } from './Canvas';
export { default as CanvasElement } from './CanvasElement';

// 工具函数和类型定义
export * from './utils';

// 画布组件使用示例
export const usageExamples = {
  Canvas: `
import { Canvas } from './components/Canvas';

// 基础画布使用
<Canvas 
  width={2000} 
  height={2000}
  scale={1}
  panEnabled={true}
  zoomEnabled={true}
>
  {/* 画布内容 */}
  <CanvasElement.Node
    id="node-1"
    x={100}
    y={100}
    title="开始节点"
    type="start"
  />
  
  <CanvasElement.Node
    id="node-2"
    x={300}
    y={100}
    title="处理节点"
    type="task"
  />
  
  <CanvasElement.Connection
    id="conn-1"
    from={{ x: 120, y: 140 }}
    to={{ x: 300, y: 140 }}
  />
</Canvas>
  `,
  
  CanvasElement: `
import { CanvasElement } from './components/Canvas';

// 节点元素
<CanvasElement.Node
  id="node-1"
  x={100}
  y={100}
  title="数据输入"
  type="data"
  status="success"
  inputs={[1]}
  outputs={[1, 2]}
  onSelect={(id) => console.log('选中节点:', id)}
  onMove={(id, delta) => console.log('移动节点:', id, delta)}
/>

// 文本元素
<CanvasElement.Text
  id="text-1"
  x={200}
  y={200}
  text="这是一个文本注释"
  fontSize={16}
  fontWeight="bold"
  resizable={true}
/>

// 连接线
<CanvasElement.Connection
  id="conn-1"
  from={{ x: 120, y: 140 }}
  to={{ x: 300, y: 140 }}
  type="bezier"
  selected={false}
  onSelect={(id) => console.log('选中连接:', id)}
/>
  `,
  
  AdvancedUsage: `
import { Canvas, CanvasElement } from './components/Canvas';
import { useCanvas } from './components/Canvas/hooks';

// 高级用法：自定义画布逻辑
const WorkflowCanvas = () => {
  const { elements, connections, selectedIds, onElementMove, onConnectionCreate } = useCanvas();
  
  return (
    <Canvas
      width={3000}
      height={2000}
      onScaleChange={(scale) => console.log('缩放:', scale)}
      onPositionChange={(position) => console.log('位置:', position)}
    >
      {/* 渲染元素 */}
      {elements.map(element => (
        <CanvasElement.Node
          key={element.id}
          {...element}
          selected={selectedIds.includes(element.id)}
          onMove={(id, delta) => onElementMove(id, delta)}
        />
      ))}
      
      {/* 渲染连接线 */}
      {connections.map(connection => (
        <CanvasElement.Connection
          key={connection.id}
          {...connection}
          selected={selectedIds.includes(connection.id)}
        />
      ))}
    </Canvas>
  );
};
  `
};

// 画布配置常量
export const CANVAS_CONFIG = {
  // 默认画布尺寸
  DEFAULT_WIDTH: 2000,
  DEFAULT_HEIGHT: 2000,
  
  // 缩放限制
  MIN_SCALE: 0.1,
  MAX_SCALE: 3,
  DEFAULT_SCALE: 1,
  
  // 网格配置
  GRID_SIZE: 20,
  GRID_COLOR: 'rgba(0, 0, 0, 0.1)',
  
  // 元素默认尺寸
  NODE_WIDTH: 120,
  NODE_HEIGHT: 80,
  TEXT_MIN_WIDTH: 60,
  TEXT_MIN_HEIGHT: 40,
  
  // 交互配置
  SNAP_TO_GRID: true,
  SHOW_GRID: true,
  ENABLE_PAN: true,
  ENABLE_ZOOM: true,
  
  // 性能配置
  DEBOUNCE_DELAY: 16, // ms
  THROTTLE_DELAY: 16, // ms
  MAX_ELEMENTS: 1000
};

// 节点类型定义
export const NODE_TYPES = {
  START: 'start',
  END: 'end',
  TASK: 'task',
  DECISION: 'decision',
  DATA: 'data',
  API: 'api',
  CUSTOM: 'custom'
};

// 连接线类型定义
export const CONNECTION_TYPES = {
  STRAIGHT: 'straight',
  BEZIER: 'bezier',
  STEPPED: 'stepped',
  SMOOTH: 'smooth'
};

// 元素状态定义
export const ELEMENT_STATUS = {
  IDLE: 'idle',
  RUNNING: 'running',
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  DISABLED: 'disabled'
};