// 画布工具函数

/**
 * 计算两点之间的距离
 */
export const distance = (x1, y1, x2, y2) => {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
};

/**
 * 计算两点之间的角度
 */
export const angle = (x1, y1, x2, y2) => {
  return Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
};

/**
 * 将坐标对齐到网格
 */
export const snapToGrid = (x, y, gridSize = 20) => {
  return {
    x: Math.round(x / gridSize) * gridSize,
    y: Math.round(y / gridSize) * gridSize
  };
};

/**
 * 检查点是否在矩形内
 */
export const isPointInRect = (point, rect) => {
  return point.x >= rect.x && 
         point.x <= rect.x + rect.width && 
         point.y >= rect.y && 
         point.y <= rect.y + rect.height;
};

/**
 * 检查两个矩形是否相交
 */
export const rectsIntersect = (rect1, rect2) => {
  return rect1.x < rect2.x + rect2.width &&
         rect1.x + rect1.width > rect2.x &&
         rect1.y < rect2.y + rect2.height &&
         rect1.y + rect1.height > rect2.y;
};

/**
 * 计算矩形的中心点
 */
export const rectCenter = (rect) => {
  return {
    x: rect.x + rect.width / 2,
    y: rect.y + rect.height / 2
  };
};

/**
 * 计算贝塞尔曲线控制点
 */
export const calculateBezierControlPoints = (start, end, curvature = 0.5) => {
  const distanceX = end.x - start.x;
  const distanceY = end.y - start.y;
  
  return {
    control1: {
      x: start.x + distanceX * curvature,
      y: start.y
    },
    control2: {
      x: start.x + distanceX * (1 - curvature),
      y: end.y
    }
  };
};

/**
 * 生成唯一ID
 */
export const generateId = (prefix = 'element') => {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * 深度克隆对象
 */
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (obj instanceof Object) {
    const clonedObj = {};
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
};

/**
 * 防抖函数
 */
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

/**
 * 节流函数
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

/**
 * 计算元素在画布上的绝对位置
 */
export const getAbsolutePosition = (element, canvasState) => {
  return {
    x: element.x * canvasState.scale + canvasState.position.x,
    y: element.y * canvasState.scale + canvasState.position.y,
    width: element.width * canvasState.scale,
    height: element.height * canvasState.scale
  };
};

/**
 * 将屏幕坐标转换为画布坐标
 */
export const screenToCanvas = (screenX, screenY, canvasState) => {
  return {
    x: (screenX - canvasState.position.x) / canvasState.scale,
    y: (screenY - canvasState.position.y) / canvasState.scale
  };
};

/**
 * 将画布坐标转换为屏幕坐标
 */
export const canvasToScreen = (canvasX, canvasY, canvasState) => {
  return {
    x: canvasX * canvasState.scale + canvasState.position.x,
    y: canvasY * canvasState.scale + canvasState.position.y
  };
};

/**
 * 计算元素边界框
 */
export const getElementBounds = (elements) => {
  if (!elements.length) return { x: 0, y: 0, width: 0, height: 0 };
  
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  
  elements.forEach(element => {
    minX = Math.min(minX, element.x);
    minY = Math.min(minY, element.y);
    maxX = Math.max(maxX, element.x + element.width);
    maxY = Math.max(maxY, element.y + element.height);
  });
  
  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY
  };
};

/**
 * 计算适合视图的缩放比例
 */
export const calculateFitScale = (bounds, containerWidth, containerHeight, padding = 0.1) => {
  const scaleX = (containerWidth * (1 - padding)) / bounds.width;
  const scaleY = (containerHeight * (1 - padding)) / bounds.height;
  return Math.min(scaleX, scaleY, 3); // 限制最大缩放为3倍
};

/**
 * 计算适合视图的位置
 */
export const calculateFitPosition = (bounds, containerWidth, containerHeight, scale) => {
  return {
    x: (containerWidth - bounds.width * scale) / (2 * scale),
    y: (containerHeight - bounds.height * scale) / (2 * scale)
  };
};

/**
 * 检查元素是否在视口内
 */
export const isElementInViewport = (element, canvasState, containerRect) => {
  const absPos = getAbsolutePosition(element, canvasState);
  
  return absPos.x + absPos.width >= 0 &&
         absPos.x <= containerRect.width &&
         absPos.y + absPos.height >= 0 &&
         absPos.y <= containerRect.height;
};

/**
 * 计算连接线路径
 */
export const calculateConnectionPath = (from, to, type = 'bezier') => {
  const fromCenter = rectCenter(from);
  const toCenter = rectCenter(to);
  
  switch (type) {
    case 'straight':
      return `M ${fromCenter.x} ${fromCenter.y} L ${toCenter.x} ${toCenter.y}`;
    
    case 'bezier':
      const controlPoints = calculateBezierControlPoints(fromCenter, toCenter);
      return `M ${fromCenter.x} ${fromCenter.y} 
              C ${controlPoints.control1.x} ${controlPoints.control1.y}, 
                ${controlPoints.control2.x} ${controlPoints.control2.y}, 
                ${toCenter.x} ${toCenter.y}`;
    
    case 'stepped':
      const midX = (fromCenter.x + toCenter.x) / 2;
      return `M ${fromCenter.x} ${fromCenter.y} 
              L ${midX} ${fromCenter.y} 
              L ${midX} ${toCenter.y} 
              L ${toCenter.x} ${toCenter.y}`;
    
    default:
      return `M ${fromCenter.x} ${fromCenter.y} L ${toCenter.x} ${toCenter.y}`;
  }
};

/**
 * 计算元素之间的最短连接路径
 */
export const findShortestPath = (elements, startId, endId) => {
  // 简化的最短路径算法实现
  const graph = {};
  
  // 构建图
  elements.forEach(element => {
    graph[element.id] = element.connections || [];
  });
  
  // BFS搜索最短路径
  const queue = [[startId]];
  const visited = new Set([startId]);
  
  while (queue.length > 0) {
    const path = queue.shift();
    const node = path[path.length - 1];
    
    if (node === endId) {
      return path;
    }
    
    for (const neighbor of graph[node] || []) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push([...path, neighbor]);
      }
    }
  }
  
  return null; // 没有找到路径
};

/**
 * 序列化画布状态
 */
export const serializeCanvas = (elements, connections, canvasState) => {
  return {
    version: '1.0.0',
    timestamp: new Date().toISOString(),
    canvasState: deepClone(canvasState),
    elements: elements.map(el => ({
      id: el.id,
      type: el.type,
      x: el.x,
      y: el.y,
      width: el.width,
      height: el.height,
      data: el.data || {}
    })),
    connections: connections.map(conn => ({
      id: conn.id,
      from: conn.from,
      to: conn.to,
      type: conn.type,
      data: conn.data || {}
    }))
  };
};

/**
 * 反序列化画布状态
 */
export const deserializeCanvas = (data) => {
  if (!data || data.version !== '1.0.0') {
    throw new Error('不支持的画布数据格式');
  }
  
  return {
    canvasState: data.canvasState,
    elements: data.elements,
    connections: data.connections
  };
};

/**
 * 导出画布为图片
 */
export const exportToImage = (canvasElement, format = 'png', quality = 1) => {
  return new Promise((resolve, reject) => {
    try {
      const dataUrl = canvasElement.toDataURL(`image/${format}`, quality);
      resolve(dataUrl);
    } catch (error) {
      reject(error);
    }
  });
};

/**
 * 导出画布为SVG
 */
export const exportToSVG = (elements, connections, canvasState) => {
  const bounds = getElementBounds(elements);
  
  const svgContent = `
    <svg width="${bounds.width}" height="${bounds.height}" xmlns="http://www.w3.org/2000/svg">
      ${connections.map(conn => {
        const fromEl = elements.find(el => el.id === conn.from);
        const toEl = elements.find(el => el.id === conn.to);
        if (!fromEl || !toEl) return '';
        
        const path = calculateConnectionPath(fromEl, toEl, conn.type);
        return `<path d="${path}" fill="none" stroke="#666" stroke-width="2"/>`;
      }).join('')}
      
      ${elements.map(el => {
        return `<rect x="${el.x}" y="${el.y}" width="${el.width}" height="${el.height}" 
                fill="white" stroke="#333" stroke-width="2"/>
                <text x="${el.x + el.width / 2}" y="${el.y + el.height / 2}" 
                text-anchor="middle" dominant-baseline="middle" font-size="12">
                ${el.data?.title || el.id}
                </text>`;
      }).join('')}
    </svg>
  `;
  
  return svgContent;
};