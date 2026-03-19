import React from 'react';
import Button from './Core/Button/index.jsx';

const TestButton = () => {
  return (
    <div>
      <h3>测试Button组件</h3>
      <Button variant="primary" onClick={() => console.log('Button clicked')}>
        测试按钮
      </Button>
    </div>
  );
};

export default TestButton;