import React from 'react';
import EnhancedMarkdownRenderer from './EnhancedMarkdownRenderer';

const FormulaTest = () => {
  // 测试内容
  const testContent = `
# 数学公式测试

## 行内公式
这是一个行内公式：$E = mc^2$

这是另一个行内公式：$\sum_{i=1}^n i = \\frac{n(n+1)}{2}$

## 块级公式
$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

$$f(x) = \\frac{1}{\sqrt{2\pi\sigma^2}} e^{-\\frac{(x-\mu)^2}{2\sigma^2}}$$

## 简单数学
$$a^2 + b^2 = c^2$$

$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

## 代码块
\`\`\`javascript
const math = "数学公式";
console.log(math);
\`\`\`
  `;

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      <h1>公式渲染测试页面</h1>
      <div style={{ border: '1px solid #ccc', padding: '20px', borderRadius: '8px', background: '#f9f9f9' }}>
        <EnhancedMarkdownRenderer content={testContent} />
      </div>
      
      <div style={{ marginTop: '30px', padding: '15px', background: '#e8f4fd', borderRadius: '8px' }}>
        <h3>测试说明：</h3>
        <ul>
          <li>行内公式应该显示为：$E = mc^2$</li>
          <li>块级公式应该居中显示</li>
          <li>代码块应该有语法高亮</li>
        </ul>
      </div>
    </div>
  );
};

export default FormulaTest;