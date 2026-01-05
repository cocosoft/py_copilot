// CSS 文件模拟
module.exports = {
  process() {
    return {
      code: 'module.exports = {};',
    };
  },
  getCacheKey() {
    return 'css-transform';
  },
};