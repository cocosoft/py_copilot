module.exports = {
  // 测试环境
  testEnvironment: 'jest-environment-jsdom',
  
  // 测试文件匹配模式
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx}',
    '<rootDir>/tests/**/*.{test,spec}.{js,jsx}'
  ],
  
  // 模块文件扩展名
  moduleFileExtensions: ['js', 'jsx', 'json', 'node'],
  
  // 转换配置
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest'
  },
  
  // 转换忽略模式
  transformIgnorePatterns: [
    'node_modules/(?!(react-router-dom)/)'
  ],
  
  // 模块路径解析
  moduleDirectories: ['node_modules', 'src'],
  
  // 设置文件
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  
  // 模拟文件
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': '<rootDir>/tests/__mocks__/styleMock.js',
    '\\.(gif|ttf|eot|svg)$': '<rootDir>/tests/__mocks__/fileMock.js'
  },
  
  // 覆盖率配置
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/main.jsx',
    '!src/vite-env.d.js',
    '!src/**/*.d.ts',
    '!src/**/__tests__/**',
    '!src/tests/**'
  ],
  
  // 覆盖率阈值
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  
  // 覆盖率报告格式
  coverageReporters: ['text', 'lcov', 'html'],
  
  // 覆盖率输出目录
  coverageDirectory: 'coverage',
  
  // 覆盖率汇总
  collectCoverage: false,
  
  // 详细输出
  verbose: true,
  
  // 测试超时时间
  testTimeout: 10000
};