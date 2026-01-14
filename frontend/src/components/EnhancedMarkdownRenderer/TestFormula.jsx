import React from 'react';
import EnhancedMarkdownRenderer from './EnhancedMarkdownRenderer';

const TestFormula = () => {
  const testContent = `
# 数学公式测试

## 行内公式
这是一个行内公式：$E = mc^2$，这是另一个行内公式：$\sum_{i=1}^n i = \\frac{n(n+1)}{2}$

## 块级公式
$$\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}$$

$$f(x) = \\frac{1}{\sqrt{2\pi\sigma^2}} e^{-\\frac{(x-\mu)^2}{2\sigma^2}}$$

## 化学公式
化学方程式：$\\ce{2H2 + O2 -> 2H2O}$

## 代码块
\`\`\`javascript
const math = "数学公式";
console.log(math);
\`\`\`
  `;

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>公式渲染测试</h1>
      <EnhancedMarkdownRenderer content={testContent} />
    </div>
  );
};

export default TestFormula;