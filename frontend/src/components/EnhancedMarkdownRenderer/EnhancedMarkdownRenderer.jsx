import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import 'katex/dist/katex.min.css';
import './EnhancedMarkdownRenderer.css';

// 配置KaTeX以支持数学公式渲染
const katexOptions = {
  throwOnError: false,
  displayMode: false, // 设置为false，让KaTeX自动处理行内和块级公式
  fleqn: false,
  leqno: false,
  output: 'html',
  strict: 'warn',
  trust: true, // 信任输入内容，允许更复杂的公式
  macros: {
    "\\RR": "\\mathbb{R}",
    "\\CC": "\\mathbb{C}",
    "\\NN": "\\mathbb{N}",
    "\\ZZ": "\\mathbb{Z}",
    "\\QQ": "\\mathbb{Q}",
    "\\vec": "\\boldsymbol{#1}",
    "\\partial": "\\partial",
    "\\nabla": "\\nabla",
    "\\times": "\\times",
    "\\cdot": "\\cdot",
    "\\mu": "\\mu",
    "\\varepsilon": "\\varepsilon",
    "\\rho": "\\rho",
    "\\sigma": "\\sigma",
    "\\mathbf": "\\boldsymbol{#1}",
    "\\^": "^{#1}",
    "\\_": "_{#1}"
  }
};

const EnhancedMarkdownRenderer = ({ content, className = '' }) => {
  const components = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      const language = match ? match[1] : '';
      
      if (!inline && language) {
        return (
          <SyntaxHighlighter
            style={vscDarkPlus}
            language={language}
            PreTag="div"
            className="code-block"
            {...props}
          >
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        );
      }
      
      return (
        <code className={`inline-code ${className || ''}`} {...props}>
          {children}
        </code>
      );
    },
    
    table({ children }) {
      return (
        <div className="table-container">
          <table className="markdown-table">{children}</table>
        </div>
      );
    },
    
    blockquote({ children }) {
      return <blockquote className="markdown-blockquote">{children}</blockquote>;
    },
    
    img({ src, alt, title }) {
      return (
        <div className="image-container">
          <img src={src} alt={alt} title={title} className="markdown-image" />
          {alt && <div className="image-caption">{alt}</div>}
        </div>
      );
    }
  };

  // 直接使用原始内容，让 remarkMath 插件来处理公式
  const processedContent = content;

  return (
    <div className={`enhanced-markdown ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, katexOptions]]}
        components={components}
        skipHtml={false}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};

export default EnhancedMarkdownRenderer;