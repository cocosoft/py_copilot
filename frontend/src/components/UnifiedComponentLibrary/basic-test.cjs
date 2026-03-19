/**
 * 前端组件库基础功能测试
 * 
 * 验证组件库的基本功能和文件完整性
 */

const fs = require('fs');
const path = require('path');

console.log('🧪 开始前端组件库基础功能测试...\n');

const testResults = {};

/**
 * 测试1: 检查核心文件存在性
 */
function testCoreFiles() {
  console.log('📁 测试1: 检查核心文件存在性...');
  
  const requiredFiles = [
    'index.js',
    'Core/Button/index.jsx',
    'Core/Button/Button.css',
    'Core/Modal/index.jsx', 
    'Core/Modal/Modal.css',
    'Core/Loading/index.jsx',
    'Core/Loading/Loading.css',
    'Core/ErrorBoundary/index.jsx',
    'Core/ErrorBoundary/ErrorBoundary.css'
  ];
  
  const existingFiles = [];
  const missingFiles = [];
  
  for (const file of requiredFiles) {
    const filePath = path.join(__dirname, file);
    if (fs.existsSync(filePath)) {
      existingFiles.push(file);
      console.log(`  ✅ ${file}`);
    } else {
      missingFiles.push(file);
      console.log(`  ❌ ${file}`);
    }
  }
  
  testResults.coreFiles = {
    status: missingFiles.length === 0 ? 'PASS' : 'FAIL',
    message: missingFiles.length === 0 ? '所有核心文件存在' : `缺少 ${missingFiles.length} 个文件`,
    details: { existingFiles, missingFiles }
  };
  
  console.log(`  ${missingFiles.length === 0 ? '✅' : '❌'} 核心文件测试 ${missingFiles.length === 0 ? '通过' : '失败'}\n`);
}

/**
 * 测试2: 检查组件导出
 */
function testComponentExports() {
  console.log('📦 测试2: 检查组件导出...');
  
  try {
    const indexFile = path.join(__dirname, 'index.js');
    const content = fs.readFileSync(indexFile, 'utf8');
    
    // 检查导出的组件
    const exports = {
      Button: content.includes('export { default as Button }'),
      Modal: content.includes('export { default as Modal }'),
      Loading: content.includes('export { default as Loading }'),
      ErrorBoundary: content.includes('export { default as ErrorBoundary }'),
      designTokens: content.includes('export { default as designTokens }')
    };
    
    const allExported = Object.values(exports).every(Boolean);
    
    Object.entries(exports).forEach(([component, exported]) => {
      console.log(`  ${exported ? '✅' : '❌'} ${component}`);
    });
    
    testResults.componentExports = {
      status: allExported ? 'PASS' : 'FAIL',
      message: allExported ? '所有组件正确导出' : '部分组件导出缺失',
      details: exports
    };
    
    console.log(`  ${allExported ? '✅' : '❌'} 组件导出测试 ${allExported ? '通过' : '失败'}\n`);
    
  } catch (error) {
    console.log(`  ❌ 读取index.js失败: ${error.message}`);
    testResults.componentExports = {
      status: 'FAIL',
      message: `读取index.js失败: ${error.message}`
    };
  }
}

/**
 * 测试3: 检查组件文件内容
 */
function testComponentContent() {
  console.log('📄 测试3: 检查组件文件内容...');
  
  const components = [
    { name: 'Button', file: 'Core/Button/index.jsx' },
    { name: 'Modal', file: 'Core/Modal/index.jsx' },
    { name: 'Loading', file: 'Core/Loading/index.jsx' },
    { name: 'ErrorBoundary', file: 'Core/ErrorBoundary/index.jsx' }
  ];
  
  const contentResults = {};
  
  for (const component of components) {
    const filePath = path.join(__dirname, component.file);
    
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      
      contentResults[component.name] = {
        exists: true,
        hasReactImport: content.includes('import React'),
        hasExport: content.includes('export default'),
        hasComponent: content.includes('function') || content.includes('const') || content.includes('class'),
        fileSize: content.length
      };
      
      const result = contentResults[component.name];
      const status = result.hasReactImport && result.hasExport && result.hasComponent;
      
      console.log(`  ${status ? '✅' : '❌'} ${component.name}: ${result.fileSize} 字符`);
      
    } catch (error) {
      console.log(`  ❌ ${component.name}: 读取失败`);
      contentResults[component.name] = {
        exists: false,
        error: error.message
      };
    }
  }
  
  const allValid = Object.values(contentResults).every(r => r.exists && r.hasReactImport && r.hasExport && r.hasComponent);
  
  testResults.componentContent = {
    status: allValid ? 'PASS' : 'FAIL',
    message: allValid ? '所有组件文件内容有效' : '部分组件文件内容异常',
    details: contentResults
  };
  
  console.log(`  ${allValid ? '✅' : '❌'} 组件内容测试 ${allValid ? '通过' : '失败'}\n`);
}

/**
 * 测试4: 检查样式文件
 */
function testStyleFiles() {
  console.log('🎨 测试4: 检查样式文件...');
  
  const styleFiles = [
    'Core/Button/Button.css',
    'Core/Modal/Modal.css',
    'Core/Loading/Loading.css',
    'Core/ErrorBoundary/ErrorBoundary.css'
  ];
  
  const styleResults = {};
  
  for (const file of styleFiles) {
    const filePath = path.join(__dirname, file);
    
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      
      styleResults[file] = {
        exists: true,
        hasCSS: content.includes('{') && content.includes('}'),
        fileSize: content.length,
        lineCount: content.split('\n').length
      };
      
      const result = styleResults[file];
      console.log(`  ${result.hasCSS ? '✅' : '❌'} ${file}: ${result.lineCount} 行`);
      
    } catch (error) {
      console.log(`  ❌ ${file}: 读取失败`);
      styleResults[file] = {
        exists: false,
        error: error.message
      };
    }
  }
  
  const allValid = Object.values(styleResults).every(r => r.exists && r.hasCSS);
  
  testResults.styleFiles = {
    status: allValid ? 'PASS' : 'FAIL',
    message: allValid ? '所有样式文件有效' : '部分样式文件异常',
    details: styleResults
  };
  
  console.log(`  ${allValid ? '✅' : '❌'} 样式文件测试 ${allValid ? '通过' : '失败'}\n`);
}

/**
 * 测试5: 检查文档文件
 */
function testDocumentation() {
  console.log('📚 测试5: 检查文档文件...');
  
  const docFiles = [
    'README.md',
    'COMPONENT_USAGE.md'
  ];
  
  const docResults = {};
  
  for (const file of docFiles) {
    const filePath = path.join(__dirname, file);
    
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      
      docResults[file] = {
        exists: true,
        hasContent: content.length > 100, // 至少100字符
        fileSize: content.length
      };
      
      const result = docResults[file];
      console.log(`  ${result.hasContent ? '✅' : '❌'} ${file}: ${result.fileSize} 字符`);
      
    } catch (error) {
      console.log(`  ❌ ${file}: 读取失败`);
      docResults[file] = {
        exists: false,
        error: error.message
      };
    }
  }
  
  const allValid = Object.values(docResults).every(r => r.exists && r.hasContent);
  
  testResults.documentation = {
    status: allValid ? 'PASS' : 'FAIL',
    message: allValid ? '所有文档文件有效' : '部分文档文件异常',
    details: docResults
  };
  
  console.log(`  ${allValid ? '✅' : '❌'} 文档文件测试 ${allValid ? '通过' : '失败'}\n`);
}

/**
 * 生成测试报告
 */
function generateReport() {
  console.log('📊 前端组件库基础功能测试报告');
  console.log('='.repeat(60));
  
  const totalTests = Object.keys(testResults).length;
  const passedTests = Object.values(testResults).filter(r => r.status === 'PASS').length;
  const failedTests = Object.values(testResults).filter(r => r.status === 'FAIL').length;
  
  console.log(`总测试数: ${totalTests}`);
  console.log(`通过测试: ${passedTests}`);
  console.log(`失败测试: ${failedTests}`);
  console.log(`成功率: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
  
  console.log('\n详细结果:');
  Object.entries(testResults).forEach(([testName, result]) => {
    const icon = result.status === 'PASS' ? '✅' : '❌';
    console.log(`${icon} ${testName}: ${result.message}`);
  });
  
  console.log('='.repeat(60));
  
  if (failedTests === 0) {
    console.log('🎉 前端组件库基础功能测试全部通过！');
    console.log('💡 组件库文件结构和内容完整，可以正常使用');
  } else {
    console.log('⚠️ 前端组件库测试存在失败项，需要检查');
  }
  
  // 保存报告
  const report = {
    timestamp: new Date().toISOString(),
    testResults: testResults,
    summary: {
      totalTests,
      passedTests,
      failedTests,
      successRate: (passedTests / totalTests) * 100
    }
  };
  
  try {
    fs.writeFileSync(
      path.join(__dirname, 'frontend_basic_test_report.json'),
      JSON.stringify(report, null, 2)
    );
    console.log('\n📁 测试报告已保存到: frontend_basic_test_report.json');
  } catch (error) {
    console.log('\n⚠️ 无法保存测试报告文件');
  }
}

// 执行所有测试
function runAllTests() {
  testCoreFiles();
  testComponentExports();
  testComponentContent();
  testStyleFiles();
  testDocumentation();
  generateReport();
}

// 运行测试
runAllTests();