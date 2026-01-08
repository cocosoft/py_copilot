// 测试图表数据
export const testChartData = {
  bar: [
    { label: '一月', value: 120 },
    { label: '二月', value: 200 },
    { label: '三月', value: 150 },
    { label: '四月', value: 180 },
    { label: '五月', value: 220 }
  ],
  
  line: [
    { x: 1, y: 30 },
    { x: 2, y: 45 },
    { x: 3, y: 25 },
    { x: 4, y: 60 },
    { x: 5, y: 40 }
  ],
  
  pie: [
    { label: '产品A', value: 35 },
    { label: '产品B', value: 25 },
    { label: '产品C', value: 20 },
    { label: '产品D', value: 20 }
  ],
  
  scatter: [
    { x: 1, y: 10, size: 5 },
    { x: 2, y: 25, size: 8 },
    { x: 3, y: 15, size: 6 },
    { x: 4, y: 35, size: 10 },
    { x: 5, y: 20, size: 7 }
  ],
  
  complex: {
    type: 'chart',
    data: [
      { category: 'Q1', sales: 100, profit: 30 },
      { category: 'Q2', sales: 150, profit: 45 },
      { category: 'Q3', sales: 120, profit: 36 },
      { category: 'Q4', sales: 200, profit: 60 }
    ],
    metadata: {
      chartType: 'bar',
      title: '季度销售数据',
      xAxis: '季度',
      yAxis: '金额（万元）'
    }
  }
};

// 生成随机测试数据
export const generateRandomData = (type, count = 10) => {
  const data = [];
  
  switch (type) {
    case 'bar':
      for (let i = 0; i < count; i++) {
        data.push({
          label: `项目${i + 1}`,
          value: Math.floor(Math.random() * 100) + 50
        });
      }
      break;
      
    case 'line':
      for (let i = 0; i < count; i++) {
        data.push({
          x: i + 1,
          y: Math.floor(Math.random() * 100) + 20
        });
      }
      break;
      
    case 'pie':
      const categories = ['A', 'B', 'C', 'D', 'E', 'F'];
      for (let i = 0; i < Math.min(count, categories.length); i++) {
        data.push({
          label: categories[i],
          value: Math.floor(Math.random() * 50) + 10
        });
      }
      break;
      
    case 'scatter':
      for (let i = 0; i < count; i++) {
        data.push({
          x: Math.random() * 100,
          y: Math.random() * 100,
          size: Math.random() * 10 + 2
        });
      }
      break;
  }
  
  return data;
};

// 验证数据格式
export const validateChartData = (data, type) => {
  if (!data || !Array.isArray(data)) {
    return { valid: false, error: '数据必须为数组' };
  }
  
  if (data.length === 0) {
    return { valid: false, error: '数据不能为空' };
  }
  
  switch (type) {
    case 'bar':
      for (const item of data) {
        if (!item.label && !item.category && !item.name) {
          return { valid: false, error: '柱状图数据必须包含标签字段' };
        }
        if (typeof item.value !== 'number' && typeof item.y !== 'number') {
          return { valid: false, error: '柱状图数据必须包含数值字段' };
        }
      }
      break;
      
    case 'line':
      for (const item of data) {
        if (typeof item.x !== 'number') {
          return { valid: false, error: '折线图数据必须包含x坐标' };
        }
        if (typeof item.y !== 'number') {
          return { valid: false, error: '折线图数据必须包含y坐标' };
        }
      }
      break;
      
    case 'pie':
      for (const item of data) {
        if (!item.label) {
          return { valid: false, error: '饼图数据必须包含标签字段' };
        }
        if (typeof item.value !== 'number') {
          return { valid: false, error: '饼图数据必须包含数值字段' };
        }
      }
      break;
      
    case 'scatter':
      for (const item of data) {
        if (typeof item.x !== 'number') {
          return { valid: false, error: '散点图数据必须包含x坐标' };
        }
        if (typeof item.y !== 'number') {
          return { valid: false, error: '散点图数据必须包含y坐标' };
        }
      }
      break;
  }
  
  return { valid: true };
};