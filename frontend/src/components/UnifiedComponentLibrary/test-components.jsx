/**
 * 统一前端组件库测试脚本
 * 
 * 测试新创建的统一组件库的基本功能，确保组件正常工作
 */

import React from 'react';
import { Button, Modal, Loading, ErrorBoundary, designTokens } from './index';

/**
 * 测试组件功能
 */
const TestComponents = () => {
  const [modalOpen, setModalOpen] = React.useState(false);
  const [loadingType, setLoadingType] = React.useState('spinner');

  return (
    <div style={{ padding: '20px', fontFamily: designTokens.typography.fontFamily.sans }}>
      <h1>统一前端组件库测试</h1>
      
      {/* 按钮组件测试 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>按钮组件测试</h2>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' }}>
          <Button variant="primary">主要按钮</Button>
          <Button variant="secondary">次要按钮</Button>
          <Button variant="success">成功按钮</Button>
          <Button variant="warning">警告按钮</Button>
          <Button variant="danger">危险按钮</Button>
          <Button variant="outline">轮廓按钮</Button>
          <Button variant="ghost">幽灵按钮</Button>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' }}>
          <Button size="small">小按钮</Button>
          <Button size="medium">中按钮</Button>
          <Button size="large">大按钮</Button>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <Button loading={true}>加载中</Button>
          <Button disabled={true}>禁用按钮</Button>
          <Button onClick={() => setModalOpen(true)}>
            打开模态框
          </Button>
        </div>
      </section>

      {/* 模态框组件测试 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>模态框组件测试</h2>
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="测试模态框"
          size="medium"
          footer={
            <>
              <Button variant="outline" onClick={() => setModalOpen(false)}>
                取消
              </Button>
              <Button variant="primary" onClick={() => setModalOpen(false)}>
                确认
              </Button>
            </>
          }
        >
          <p>这是一个测试模态框的内容。</p>
          <p>你可以在这里放置任何内容。</p>
        </Modal>
        
        <Button onClick={() => setModalOpen(true)}>
          打开模态框
        </Button>
      </section>

      {/* 加载组件测试 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>加载组件测试</h2>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ marginRight: '12px' }}>选择加载类型:</label>
          <select 
            value={loadingType} 
            onChange={(e) => setLoadingType(e.target.value)}
            style={{ padding: '6px 12px', borderRadius: '4px', border: '1px solid #ccc' }}
          >
            <option value="spinner">旋转加载器</option>
            <option value="dots">点状加载器</option>
            <option value="progress">进度条</option>
            <option value="skeleton">骨架屏</option>
          </select>
        </div>
        
        <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
          <Loading type={loadingType} size="small" text="小加载" />
          <Loading type={loadingType} size="medium" text="中加载" />
          <Loading type={loadingType} size="large" text="大加载" />
          
          {loadingType === 'progress' && (
            <Loading type="progress" progress={65} text="进度加载" />
          )}
        </div>
      </section>

      {/* 错误边界组件测试 */}
      <section style={{ marginBottom: '40px' }}>
        <h2>错误边界组件测试</h2>
        
        <ErrorBoundary
          showDetails={true}
          onError={(error, errorInfo) => {
            console.log('错误边界捕获到错误:', error, errorInfo);
          }}
        >
          <div style={{ 
            padding: '20px', 
            border: '1px solid #e0e0e0', 
            borderRadius: '8px',
            backgroundColor: '#f9f9f9'
          }}>
            <h3>正常组件内容</h3>
            <p>这个组件在错误边界保护下运行。</p>
            <Button variant="primary" onClick={() => {
              // 模拟一个错误
              throw new Error('这是一个测试错误！');
            }}>
              触发错误
            </Button>
          </div>
        </ErrorBoundary>
      </section>

      {/* 设计令牌测试 */}
      <section>
        <h2>设计令牌测试</h2>
        
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '20px' }}>
          {Object.entries(designTokens.colors.primary).map(([key, value]) => (
            <div
              key={key}
              style={{
                width: '60px',
                height: '60px',
                backgroundColor: value,
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: parseInt(key) >= 500 ? 'white' : 'black',
                fontSize: '12px',
                fontWeight: 'bold'
              }}
            >
              {key}
            </div>
          ))}
        </div>
        
        <div style={{ 
          padding: '16px', 
          backgroundColor: designTokens.colors.gray[50],
          borderRadius: '8px',
          border: `1px solid ${designTokens.colors.gray[200]}`
        }}>
          <h3 style={{ color: designTokens.colors.gray[900] }}>设计系统示例</h3>
          <p style={{ color: designTokens.colors.gray[600] }}>
            这是一个使用设计令牌的示例文本。
          </p>
        </div>
      </section>
    </div>
  );
};

/**
 * 组件导入测试
 */
const testComponentImports = () => {
  try {
    console.log('🧪 开始测试组件导入...');
    
    // 测试组件是否存在
    const components = {
      Button: typeof Button,
      Modal: typeof Modal,
      Loading: typeof Loading,
      ErrorBoundary: typeof ErrorBoundary,
      designTokens: typeof designTokens
    };
    
    console.log('✅ 组件导入状态:', components);
    
    // 测试设计令牌
    if (designTokens && designTokens.colors && designTokens.colors.primary) {
      console.log('✅ 设计令牌导入正常');
    } else {
      console.log('❌ 设计令牌导入异常');
    }
    
    return true;
  } catch (error) {
    console.error('❌ 组件导入测试失败:', error);
    return false;
  }
};

// 运行导入测试
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    setTimeout(() => {
      testComponentImports();
    }, 1000);
  });
}

export default TestComponents;
export { testComponentImports };