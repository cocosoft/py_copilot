import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import ModelSelector from '../ModelSelector';

describe('ModelSelector Component', () => {
  const mockModels = [
    {
      id: '1',
      name: 'GPT-4',
      provider: 'OpenAI',
      description: 'Most capable model',
      category: 'text',
      parameters: 1750000000000,
      contextLength: 8192,
      pricing: { input: 0.03, output: 0.06 }
    },
    {
      id: '2',
      name: 'Claude-3',
      provider: 'Anthropic',
      description: 'Advanced reasoning model',
      category: 'text',
      parameters: null,
      contextLength: 200000,
      pricing: { input: 0.015, output: 0.075 }
    },
    {
      id: '3',
      name: 'DALL-E 3',
      provider: 'OpenAI',
      description: 'Image generation model',
      category: 'image',
      parameters: null,
      contextLength: null,
      pricing: { input: 0.04, output: null }
    }
  ];

  const defaultProps = {
    models: mockModels,
    selectedModelId: null,
    onModelSelect: jest.fn(),
    onModelPreview: jest.fn(),
    loading: false,
    error: null
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders model selector with all models', () => {
      render(<ModelSelector {...defaultProps} />);
      
      expect(screen.getByText('GPT-4')).toBeInTheDocument();
      expect(screen.getByText('Claude-3')).toBeInTheDocument();
      expect(screen.getByText('DALL-E 3')).toBeInTheDocument();
    });

    it('displays model provider and description', () => {
      render(<ModelSelector {...defaultProps} />);
      
      expect(screen.getByText('OpenAI')).toBeInTheDocument();
      expect(screen.getByText('Anthropic')).toBeInTheDocument();
      expect(screen.getByText('Most capable model')).toBeInTheDocument();
      expect(screen.getByText('Advanced reasoning model')).toBeInTheDocument();
    });

    it('shows loading state when loading is true', () => {
      render(<ModelSelector {...defaultProps} loading={true} />);
      
      expect(screen.getByText(/加载中/)).toBeInTheDocument();
    });

    it('shows error state when error is provided', () => {
      const errorMessage = 'Failed to load models';
      render(<ModelSelector {...defaultProps} error={errorMessage} />);
      
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    it('displays empty state when no models are available', () => {
      render(<ModelSelector {...defaultProps} models={[]} />);
      
      expect(screen.getByText(/暂无可用模型/)).toBeInTheDocument();
    });
  });

  describe('Search and Filter', () => {
    it('filters models by search term', async () => {
      const user = userEvent.setup();
      render(<ModelSelector {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/搜索模型/);
      await user.type(searchInput, 'GPT');
      
      await waitFor(() => {
        expect(screen.getByText('GPT-4')).toBeInTheDocument();
        expect(screen.queryByText('Claude-3')).not.toBeInTheDocument();
        expect(screen.queryByText('DALL-E 3')).not.toBeInTheDocument();
      });
    });

    it('filters models by provider', async () => {
      const user = userEvent.setup();
      render(<ModelSelector {...defaultProps} />);
      
      const providerFilter = screen.getByText('所有提供商');
      await user.click(providerFilter);
      
      const openaiOption = screen.getByText('OpenAI');
      await user.click(openaiOption);
      
      await waitFor(() => {
        expect(screen.getByText('GPT-4')).toBeInTheDocument();
        expect(screen.getByText('DALL-E 3')).toBeInTheDocument();
        expect(screen.queryByText('Claude-3')).not.toBeInTheDocument();
      });
    });

    it('filters models by category', async () => {
      const user = userEvent.setup();
      render(<ModelSelector {...defaultProps} />);
      
      const categoryFilter = screen.getByText('所有类型');
      await user.click(categoryFilter);
      
      const textOption = screen.getByText('文本生成');
      await user.click(textOption);
      
      await waitFor(() => {
        expect(screen.getByText('GPT-4')).toBeInTheDocument();
        expect(screen.getByText('Claude-3')).toBeInTheDocument();
        expect(screen.queryByText('DALL-E 3')).not.toBeInTheDocument();
      });
    });
  });

  describe('Model Selection', () => {
    it('calls onModelSelect when a model is selected', async () => {
      const user = userEvent.setup();
      const { onModelSelect } = defaultProps;
      
      render(<ModelSelector {...defaultProps} />);
      
      const gpt4Card = screen.getByText('GPT-4').closest('[data-testid="model-card"]');
      await user.click(gpt4Card);
      
      expect(onModelSelect).toHaveBeenCalledWith(mockModels[0]);
    });

    it('highlights selected model', () => {
      render(<ModelSelector {...defaultProps} selectedModelId="1" />);
      
      const gpt4Card = screen.getByText('GPT-4').closest('[data-testid="model-card"]');
      expect(gpt4Card).toHaveClass('border-blue-500', 'bg-blue-50');
    });

    it('shows selected model badge', () => {
      render(<ModelSelector {...defaultProps} selectedModelId="1" />);
      
      expect(screen.getByText('已选择')).toBeInTheDocument();
    });
  });

  describe('Model Preview', () => {
    it('calls onModelPreview when preview button is clicked', async () => {
      const user = userEvent.setup();
      const { onModelPreview } = defaultProps;
      
      render(<ModelSelector {...defaultProps} />);
      
      const previewButton = screen.getAllByText('预览')[0];
      await user.click(previewButton);
      
      expect(onModelPreview).toHaveBeenCalledWith(mockModels[0]);
    });

    it('opens preview modal with model details', async () => {
      const user = userEvent.setup();
      render(<ModelSelector {...defaultProps} />);
      
      const previewButton = screen.getAllByText('预览')[0];
      await user.click(previewButton);
      
      await waitFor(() => {
        expect(screen.getByText('模型详情')).toBeInTheDocument();
        expect(screen.getByText('GPT-4')).toBeInTheDocument();
        expect(screen.getByText('OpenAI')).toBeInTheDocument();
        expect(screen.getByText('Most capable model')).toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('navigates models with arrow keys', async () => {
      const user = userEvent.setup();
      render(<ModelSelector {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/搜索模型/);
      searchInput.focus();
      
      await user.keyboard('{ArrowDown}');
      
      await waitFor(() => {
        const focusedCard = document.activeElement.closest('[data-testid="model-card"]');
        expect(focusedCard).toBeTruthy();
      });
    });

    it('selects model with Enter key', async () => {
      const user = userEvent.setup();
      const { onModelSelect } = defaultProps;
      
      render(<ModelSelector {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/搜索模型/);
      searchInput.focus();
      
      await user.keyboard('{ArrowDown}{Enter}');
      
      expect(onModelSelect).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA labels', () => {
      render(<ModelSelector {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/搜索模型/);
      expect(searchInput).toHaveAttribute('aria-label', '搜索模型');
      
      const modelCards = screen.getAllByTestId('model-card');
      modelCards.forEach(card => {
        expect(card).toHaveAttribute('role', 'button');
      });
    });

    it('supports keyboard navigation', () => {
      render(<ModelSelector {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText(/搜索模型/);
      searchInput.focus();
      
      expect(searchInput).toHaveFocus();
    });
  });
});