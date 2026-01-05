// 静态文件模拟（图片、字体等）
module.exports = {
  process() {
    return {
      code: 'module.exports = "test-file-stub";',
    };
  },
  getCacheKey() {
    return 'file-transform';
  },
};