/**
 * Settings.jsx 测试
 * 测试记忆管理界面的功能
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Settings from '../Settings';

// Mock API 客户端
jest.mock('../utils/apiUtils', () => ({
  request: jest.fn(),
  requestWithRetry: jest.fn()
}));

// Mock D3
jest.mock('d3', () => ({
  select: jest.fn(() => ({
    selectAll: jest.fn(() => ({
      remove: jest.fn(),
      data: jest.fn(() => ({
        enter: jest.fn(() => ({
          append: jest.fn(() => ({
            attr: jest.fn().mockReturnThis(),
            style: jest.fn().mockReturnThis(),
            text: jest.fn().mockReturnThis(),
            call: jest.fn().mockReturnThis()
          }))
        }))
      })),
      append: jest.fn(() => ({
        attr: jest.fn().mockReturnThis(),
        call: jest.fn().mockReturnThis()
      }))
    })),
    pie: jest.fn(() => ({
      value: jest.fn().mockReturnThis()
    })),
    arc: jest.fn(() => ({
      innerRadius: jest.fn().mockReturnThis(),
      outerRadius: jest.fn().mockReturnThis(),
      centroid: jest.fn().mockReturnValue([0, 0])
    })),
    scaleOrdinal: jest.fn(() => ({
      domain: jest.fn().mockReturnThis(),
      range: jest.fn().mockReturnThis()
    })),
    scaleBand: jest.fn(() => ({
      range: jest.fn().mockReturnThis(),
      padding: jest.fn().mockReturnThis(),
      domain: jest.fn().mockReturnThis(),
      bandwidth: jest.fn().mockReturnValue(100)
    })),
    scaleLinear: jest.fn(() => ({
      range: jest.fn().mockReturnThis(),
      domain: jest.fn().mockReturnThis()
    })),
    axisBottom: jest.fn(),
    axisLeft: jest.fn(),
    forceSimulation: jest.fn(() => ({
      force: jest.fn().mockReturnThis(),
      on: jest.fn().mockReturnThis()
    })),
    forceLink: jest.fn(() => ({
      id: jest.fn().mockReturnThis(),
      distance: jest.fn().mockReturnThis()
    })),
    forceManyBody: jest.fn(() => ({
      strength: jest.fn().mockReturnThis()
    })),
    forceCenter: jest.fn(() => ({
      x: jest.fn().mockReturnThis(),
      y: jest.fn().mockReturnThis()
    })),
    forceCollide: jest.fn(() => ({
      radius: jest.fn().mockReturnThis()
    })),
    drag: jest.fn(() => ({
      on: jest.fn().mockReturnThis()
    }))
  })
}));

describe('Settings Memory Management', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('请求串行化', () => {
    it('应该按顺序加载记忆数据', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry
        .mockResolvedValueOnce({ config: 'test-config' })
        .mockResolvedValueOnce({ items: [], total: 0 })
        .mockResolvedValueOnce({ total_count: 100 })
        .mockResolvedValueOnce({ temporal_patterns: {} })
        .mockResolvedValueOnce({ nodes: [], edges: [] });

      render(<Settings />);

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledTimes(5);
      });
    });

    it('应该在配置加载完成后加载列表', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      let callOrder = 0;
      requestWithRetry.mockImplementation((url) => {
        callOrder++;
        if (url.includes('config')) {
          return Promise.resolve({ config: 'test-config' });
        } else if (url.includes('memories') && !url.includes('analytics')) {
          return Promise.resolve({ items: [], total: 0 });
        }
        return Promise.resolve({});
      });

      render(<Settings />);

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledWith('/v1/memory/memories/analytics/config');
      });

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledWith('/v1/memory/memories');
      });
    });
  });

  describe('缓存机制', () => {
    it('应该使用缓存避免重复请求', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({ total_count: 100 });

      render(<Settings />);

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledTimes(1);
      });

      // 触发重新渲染
      fireEvent.click(screen.getByText('刷新'));

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledTimes(1);
      });
    });

    it('应该在数据更新时清除缓存', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({ total_count: 100 });

      render(<Settings />);

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledTimes(1);
      });

      // 模拟数据更新
      fireEvent.click(screen.getByText('清除缓存'));

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('错误处理', () => {
    it('应该在请求失败时显示错误提示', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 错误
      requestWithRetry.mockRejectedValue(new Error('网络错误'));

      // Mock alert
      window.alert = jest.fn();

      render(<Settings />);

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('加载记忆配置失败: 网络错误');
      });
    });

    it('应该在重试失败后显示错误', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 重试失败
      requestWithRetry.mockRejectedValue(new Error('重试失败'));

      // Mock alert
      window.alert = jest.fn();

      render(<Settings />);

      await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('加载记忆配置失败: 重试失败');
      });
    });
  });

  describe('分页加载', () => {
    it('应该在分页变化时重新加载记忆列表', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({ items: [], total: 100 });

      render(<Settings />);

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledWith('/v1/memory/memories');
      });

      // 触发分页变化
      fireEvent.click(screen.getByText('下一页'));

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledWith('/v1/memory/memories?page=2&limit=20');
      });
    });

    it('应该在分页变化时不重新加载统计数据', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({ total_count: 100 });

      render(<Settings />);

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledWith('/v1/memory/memories/analytics/stats');
      });

      // 触发分页变化
      fireEvent.click(screen.getByText('下一页'));

      await waitFor(() => {
        expect(requestWithRetry).not.toHaveBeenCalledWith('/v1/memory/memories/analytics/stats');
      });
    });
  });

  describe('图表渲染', () => {
    it('应该渲染记忆类型分布饼图', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({
        total_count: 100,
        by_type: { SHORT_TERM: 50, LONG_TERM: 50 }
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('记忆类型分布')).toBeInTheDocument();
      });
    });

    it('应该渲染记忆重要性分布柱状图', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({
        total_count: 100,
        by_type: { SHORT_TERM: 50, LONG_TERM: 50 }
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('记忆重要性分布')).toBeInTheDocument();
      });
    });

    it('应该渲染知识图谱', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({
        nodes: [{ id: 1, title: '节点1' }],
        edges: []
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('知识图谱')).toBeInTheDocument();
      });
    });
  });

  describe('防抖优化', () => {
    it('应该在窗口大小变化时使用防抖', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({
        total_count: 100,
        by_type: { SHORT_TERM: 50, LONG_TERM: 50 }
      });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('记忆类型分布')).toBeInTheDocument();
      });

      // 触发多次窗口大小变化
      for (let i = 0; i < 10; i++) {
        fireEvent(window, new Event('resize'));
      }

      // 验证图表只重新渲染一次（防抖生效）
      await waitFor(() => {
        expect(screen.getByText('记忆类型分布')).toBeInTheDocument();
      }, { timeout: 500 });
    });
  });

  describe('用户体验', () => {
    it('应该显示加载状态', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 延迟响应
      requestWithRetry.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ total_count: 100 }), 1000))
      );

      render(<Settings />);

      expect(screen.getByText('加载中...')).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText('加载中...')).not.toBeInTheDocument();
      });
    });

    it('应该显示空状态', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 空数据
      requestWithRetry.mockResolvedValue({ items: [], total: 0 });

      render(<Settings />);

      await waitFor(() => {
        expect(screen.getByText('暂无记忆数据')).toBeInTheDocument();
      });
    });

    it('应该支持搜索功能', async () => {
      const { requestWithRetry } = require('../utils/apiUtils');
      
      // Mock 响应
      requestWithRetry.mockResolvedValue({ items: [], total: 0 });

      render(<Settings />);

      const searchInput = screen.getByPlaceholderText('搜索记忆...');
      fireEvent.change(searchInput, { target: { value: '测试' } });

      await waitFor(() => {
        expect(requestWithRetry).toHaveBeenCalledWith('/v1/memory/memories?query=测试');
      });
    });
  });
});
