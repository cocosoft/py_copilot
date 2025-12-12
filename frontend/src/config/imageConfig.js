// 图片路径配置文件
// 用户可以在这里修改图片的存储路径配置

// 图片根目录
const IMAGE_ROOT = '/logos';

// 各个分类的图片目录
const IMAGE_DIRS = {
  // 供应商/提供商图片目录
  providers: `${IMAGE_ROOT}/providers`,
  // 模型类别图片目录
  categories: `${IMAGE_ROOT}/categories`,
  // 模型图片目录
  models: `${IMAGE_ROOT}/models`,
  // 智能体图片目录
  agents: `${IMAGE_ROOT}/agents`,
  // 能力图片目录
  capabilities: `${IMAGE_ROOT}/capabilities`
};

// 默认图片路径
const DEFAULT_IMAGES = {
  // 默认供应商图片
  provider: `${IMAGE_DIRS.providers}/default.png`,
  // 默认模型图片
  model: `${IMAGE_DIRS.models}/default.png`,
  // 默认类别图片
  category: `${IMAGE_DIRS.categories}/default.png`,
  // 默认智能体图片
  agent: `${IMAGE_DIRS.agents}/default.png`,
  // 默认能力图片
  capability: `${IMAGE_DIRS.capabilities}/default.png`
};

// 图片路径生成工具函数
const getImageUrl = (type, filename) => {
  // 如果已经是完整的URL或绝对路径，直接返回
  if (filename && (filename.startsWith('http') || filename.startsWith('/'))) {
    return filename;
  }
  
  // 根据类型返回对应的图片路径
  const baseDir = IMAGE_DIRS[type];
  if (!baseDir) {
    console.warn(`未知的图片类型: ${type}`);
    return DEFAULT_IMAGES.provider;
  }
  
  return filename ? `${baseDir}/${filename}` : DEFAULT_IMAGES[type] || DEFAULT_IMAGES.provider;
};

export {
  IMAGE_ROOT,
  IMAGE_DIRS,
  DEFAULT_IMAGES,
  getImageUrl
};
