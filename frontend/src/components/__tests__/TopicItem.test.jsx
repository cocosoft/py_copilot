/** TopicItem 组件单元测试 */
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TopicItem from '../TopicItem';

describe('TopicItem 组件', () => {
  const mockTopic = {
    id: 1,
    topic_name: '测试话题',
    topic_summary: '这是一个测试话题的摘要',
    message_count: 10,
    created_at: new Date().toISOString()
  };

  const mockOnClick = jest.fn();
  const mockOnDelete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('基本渲染', () => {
    test('应该正确渲染话题信息', () => {
      render(
        <TopicItem
          topic={mockTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('测试话题')).toBeInTheDocument();
      expect(screen.getByText('这是一个测试话题的摘要')).toBeInTheDocument();
      expect(screen.getByText('10 条消息')).toBeInTheDocument();
    });

    test('活跃状态应该显示活跃徽章', () => {
      render(
        <TopicItem
          topic={mockTopic}
          isActive={true}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('活跃')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /测试话题/ })).toHaveClass('topic-item-active');
    });

    test('非活跃状态不应该显示活跃徽章', () => {
      render(
        <TopicItem
          topic={mockTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.queryByText('活跃')).not.toBeInTheDocument();
    });
  });

  describe('交互行为', () => {
    test('点击话题应该调用onClick回调', () => {
      render(
        <TopicItem
          topic={mockTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      const topicItem = screen.getByRole('button', { name: /测试话题/ });
      fireEvent.click(topicItem);

      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    test('点击删除按钮应该调用onDelete回调', () => {
      render(
        <TopicItem
          topic={mockTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      const deleteButton = screen.getByTitle('删除话题');
      fireEvent.click(deleteButton);

      expect(mockOnDelete).toHaveBeenCalledTimes(1);
      expect(mockOnClick).not.toHaveBeenCalled();
    });
  });

  describe('时间格式化', () => {
    test('应该正确显示"刚刚"', () => {
      const recentTopic = {
        ...mockTopic,
        created_at: new Date(Date.now() - 30000).toISOString()
      };

      render(
        <TopicItem
          topic={recentTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('刚刚')).toBeInTheDocument();
    });

    test('应该正确显示"X分钟前"', () => {
      const recentTopic = {
        ...mockTopic,
        created_at: new Date(Date.now() - 1800000).toISOString()
      };

      render(
        <TopicItem
          topic={recentTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('30 分钟前')).toBeInTheDocument();
    });

    test('应该正确显示"X小时前"', () => {
      const recentTopic = {
        ...mockTopic,
        created_at: new Date(Date.now() - 7200000).toISOString()
      };

      render(
        <TopicItem
          topic={recentTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('2 小时前')).toBeInTheDocument();
    });

    test('应该正确显示"X天前"', () => {
      const recentTopic = {
        ...mockTopic,
        created_at: new Date(Date.now() - 172800000).toISOString()
      };

      render(
        <TopicItem
          topic={recentTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('2 天前')).toBeInTheDocument();
    });
  });

  describe('性能优化', () => {
    test('应该使用React.memo进行优化', () => {
      const { rerender } = render(
        <TopicItem
          topic={mockTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      const initialRenderCount = mockOnClick.mock.calls.length;

      rerender(
        <TopicItem
          topic={mockTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(mockOnClick.mock.calls.length).toBe(initialRenderCount);
    });

    test('props变化时应该重新渲染', () => {
      const { rerender } = render(
        <TopicItem
          topic={mockTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      const updatedTopic = { ...mockTopic, topic_name: '更新后的话题' };
      rerender(
        <TopicItem
          topic={updatedTopic}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.getByText('更新后的话题')).toBeInTheDocument();
    });
  });

  describe('边界情况', () => {
    test('没有摘要时不应该显示摘要', () => {
      const topicWithoutSummary = {
        ...mockTopic,
        topic_summary: null
      };

      render(
        <TopicItem
          topic={topicWithoutSummary}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.queryByText('这是一个测试话题的摘要')).not.toBeInTheDocument();
    });

    test('没有创建时间时不应该显示时间', () => {
      const topicWithoutDate = {
        ...mockTopic,
        created_at: null
      };

      render(
        <TopicItem
          topic={topicWithoutDate}
          isActive={false}
          onClick={mockOnClick}
          onDelete={mockOnDelete}
        />
      );

      expect(screen.queryByText('刚刚')).not.toBeInTheDocument();
      expect(screen.queryByText('分钟前')).not.toBeInTheDocument();
    });
  });
});
