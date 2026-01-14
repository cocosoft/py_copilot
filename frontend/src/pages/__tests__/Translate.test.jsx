import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import Translate from '../Translate';
import { useTranslateText, useSupportedLanguages, useTranslationHistory, useSaveTranslationHistory, useClearTranslationHistory } from '../../hooks/useTranslation';
import { showSuccess, showError } from '../../components/UI';

// Mock the translation hooks and UI components
jest.mock('../../hooks/useTranslation', () => ({
  useTranslateText: jest.fn(),
  useSupportedLanguages: jest.fn(),
  useTranslationHistory: jest.fn(),
  useSaveTranslationHistory: jest.fn(),
  useClearTranslationHistory: jest.fn()
}));

jest.mock('../../components/UI', () => ({
  showSuccess: jest.fn(),
  showError: jest.fn()
}));

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
    readText: jest.fn()
  }
});

describe('Translate Component', () => {
  let queryClient;
  let wrapper;

  const mockLanguages = {
    languages: [
      { code: 'en', name: 'English' },
      { code: 'zh', name: 'Chinese' },
      { code: 'ja', name: 'Japanese' },
      { code: 'ko', name: 'Korean' }
    ]
  };

  const mockHistory = {
    history: [
      {
        id: 1,
        source_text: 'Hello',
        translated_text: '你好',
        source_language: 'en',
        target_language: 'zh',
        created_at: '2024-01-01T00:00:00Z'
      }
    ]
  };

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

    wrapper = ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );

    // Mock hooks
    useSupportedLanguages.mockReturnValue({
      data: mockLanguages,
      isLoading: false,
      error: null
    });

    useTranslationHistory.mockReturnValue({
      data: mockHistory,
      isLoading: false,
      error: null
    });

    useTranslateText.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      error: null
    });

    useSaveTranslationHistory.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      error: null
    });

    useClearTranslationHistory.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: false,
      error: null
    });

    jest.clearAllMocks();
  });

  it('should render the translation page with all elements', () => {
    render(<Translate />, { wrapper });

    expect(screen.getByText('翻译')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('请输入要翻译的文本...')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('翻译结果将显示在这里...')).toBeInTheDocument();
    expect(screen.getByText('翻译')).toBeInTheDocument();
    expect(screen.getByText('复制结果')).toBeInTheDocument();
    expect(screen.getByText('清空')).toBeInTheDocument();
    expect(screen.getByText('翻译历史')).toBeInTheDocument();
  });

  it('should handle text input and translation', async () => {
    const user = userEvent.setup();
    const mockTranslate = jest.fn().mockResolvedValue({
      translated_text: '你好世界',
      source_language: 'en',
      target_language: 'zh'
    });

    useTranslateText.mockReturnValue({
      mutateAsync: mockTranslate,
      isPending: false,
      error: null
    });

    render(<Translate />, { wrapper });

    const sourceTextarea = screen.getByPlaceholderText('请输入要翻译的文本...');
    const translateButton = screen.getByText('立即翻译 (Ctrl+Enter)');

    // Enter text
    await user.type(sourceTextarea, 'Hello world');
    expect(sourceTextarea.value).toBe('Hello world');

    // Click translate button
    await user.click(translateButton);

    expect(mockTranslate).toHaveBeenCalledWith({
      text: 'Hello world',
      source_language: 'en',
      target_language: 'zh'
    });

    // Wait for translation to complete
    await waitFor(() => {
      expect(showSuccess).toHaveBeenCalledWith('翻译成功');
    });
  });

  it('should handle copy to clipboard', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    // Mock translated text
    const translatedTextarea = screen.getByPlaceholderText('翻译结果将显示在这里...');
    Object.defineProperty(translatedTextarea, 'value', {
      value: '你好世界',
      writable: true
    });

    const copyButton = screen.getByText('复制结果');
    await user.click(copyButton);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('你好世界');
    expect(showSuccess).toHaveBeenCalledWith('已复制到剪贴板');
  });

  it('should handle clear functionality', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    const sourceTextarea = screen.getByPlaceholderText('请输入要翻译的文本...');
    const clearButton = screen.getByTitle('清空 (Ctrl+Backspace)');

    // Enter some text
    await user.type(sourceTextarea, 'Test text');
    expect(sourceTextarea.value).toBe('Test text');

    // Clear the text
    await user.click(clearButton);

    expect(sourceTextarea.value).toBe('');
    expect(showSuccess).toHaveBeenCalledWith('已清空输入');
  });

  it('should handle language selection', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    const sourceLanguageSelect = screen.getByDisplayValue('English');
    const targetLanguageSelect = screen.getByDisplayValue('Chinese');

    // Change source language
    await user.selectOptions(sourceLanguageSelect, 'ja');
    expect(sourceLanguageSelect.value).toBe('ja');

    // Change target language
    await user.selectOptions(targetLanguageSelect, 'ko');
    expect(targetLanguageSelect.value).toBe('ko');
  });

  it('should handle keyboard shortcuts', async () => {
    const user = userEvent.setup();
    const mockTranslate = jest.fn().mockResolvedValue({
      translated_text: '测试',
      source_language: 'en',
      target_language: 'zh'
    });

    useTranslateText.mockReturnValue({
      mutateAsync: mockTranslate,
      isPending: false,
      error: null
    });

    render(<Translate />, { wrapper });

    const sourceTextarea = screen.getByPlaceholderText('请输入要翻译的文本...');
    
    // Focus the textarea
    await user.click(sourceTextarea);
    await user.type(sourceTextarea, 'Test');

    // Test Ctrl+Enter shortcut
    await user.keyboard('{Control>}{Enter}{/Control}');

    expect(mockTranslate).toHaveBeenCalledWith({
      text: 'Test',
      source_language: 'en',
      target_language: 'zh'
    });
  });

  it('should display loading state during translation', () => {
    useTranslateText.mockReturnValue({
      mutateAsync: jest.fn(),
      isPending: true,
      error: null
    });

    render(<Translate />, { wrapper });

    expect(screen.getByText('翻译中...')).toBeInTheDocument();
  });

  it('should handle translation errors', async () => {
    const user = userEvent.setup();
    const mockError = new Error('Translation failed');
    
    useTranslateText.mockReturnValue({
      mutateAsync: jest.fn().mockRejectedValue(mockError),
      isPending: false,
      error: mockError
    });

    render(<Translate />, { wrapper });

    const sourceTextarea = screen.getByPlaceholderText('请输入要翻译的文本...');
    const translateButton = screen.getByText('翻译');

    await user.type(sourceTextarea, 'Hello');
    await user.click(translateButton);

    await waitFor(() => {
      expect(showError).toHaveBeenCalledWith('翻译失败，请稍后重试');
    });
  });

  it('should display translation history', () => {
    render(<Translate />, { wrapper });

    expect(screen.getByText('翻译历史')).toBeInTheDocument();
    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText('你好')).toBeInTheDocument();
  });

  it('should handle voice input placeholder', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    const voiceButton = screen.getByTitle('语音输入');
    await user.click(voiceButton);

    await waitFor(() => {
      expect(showSuccess).toHaveBeenCalledWith('开始语音输入...');
    });
  });

  it('should handle text-to-speech placeholder', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    // Mock translated text
    const translatedTextarea = screen.getByPlaceholderText('翻译结果将显示在这里...');
    Object.defineProperty(translatedTextarea, 'value', {
      value: '你好世界',
      writable: true
    });

    const ttsButton = screen.getByTitle('语音播放');
    await user.click(ttsButton);

    expect(showError).toHaveBeenCalledWith('语音播放功能暂未实现');
  });

  it('should handle search functionality', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    // Click filter toggle button
    const filterButton = screen.getByRole('button', { name: /筛选选项/ });
    await user.click(filterButton);

    // Enter search keyword
    const searchInput = screen.getByPlaceholderText('搜索源文本或翻译结果...');
    await user.type(searchInput, 'Hello');

    // Verify search parameter is passed to hook
    expect(useTranslationHistory).toHaveBeenCalledWith({
      search: 'Hello',
      source_language: '',
      target_language: '',
      date_range: ''
    });
  });

  it('should handle language filtering', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    // Click filter toggle button
    const filterButton = screen.getByRole('button', { name: /筛选选项/ });
    await user.click(filterButton);

    // Select source language filter
    const sourceLanguageSelect = screen.getByDisplayValue('所有源语言');
    await user.selectOptions(sourceLanguageSelect, 'en');

    // Verify filter parameters are passed to hook
    expect(useTranslationHistory).toHaveBeenCalledWith({
      search: '',
      source_language: 'en',
      target_language: '',
      date_range: ''
    });
  });

  it('should handle date range filtering', async () => {
    const user = userEvent.setup();
    
    render(<Translate />, { wrapper });

    // Click filter toggle button
    const filterButton = screen.getByRole('button', { name: /筛选选项/ });
    await user.click(filterButton);

    // Select date range filter
    const dateRangeSelect = screen.getByDisplayValue('所有时间');
    await user.selectOptions(dateRangeSelect, 'today');

    // Verify filter parameters are passed to hook
    expect(useTranslationHistory).toHaveBeenCalledWith({
      search: '',
      source_language: '',
      target_language: '',
      date_range: 'today'
    });
  });

  it('should handle clear filters functionality', async () => {
    const user = userEvent.setup();
    
    // Mock history with search parameters
    useTranslationHistory.mockReturnValue({
      data: { history: [] },
      isLoading: false,
      error: null
    });

    render(<Translate />, { wrapper });

    // Click filter toggle button
    const filterButton = screen.getByRole('button', { name: /筛选选项/ });
    await user.click(filterButton);

    // Enter search keyword and select filters
    const searchInput = screen.getByPlaceholderText('搜索源文本或翻译结果...');
    await user.type(searchInput, 'Hello');

    const sourceLanguageSelect = screen.getByDisplayValue('所有源语言');
    await user.selectOptions(sourceLanguageSelect, 'en');

    // Click clear filters button
    const clearFiltersButton = screen.getByRole('button', { name: /重置/ });
    await user.click(clearFiltersButton);

    // Verify all filters are cleared
    expect(useTranslationHistory).toHaveBeenCalledWith({
      search: '',
      source_language: '',
      target_language: '',
      date_range: ''
    });
  });

  it('should display filter stats when filters are active', async () => {
    const user = userEvent.setup();
    
    // Mock history with search parameters
    useTranslationHistory.mockReturnValue({
      data: { 
        history: [
          {
            id: 1,
            source_text: 'Hello',
            translated_text: '你好',
            source_language: 'en',
            target_language: 'zh',
            created_at: '2024-01-01T00:00:00Z'
          }
        ]
      },
      isLoading: false,
      error: null
    });

    render(<Translate />, { wrapper });

    // Click filter toggle button
    const filterButton = screen.getByRole('button', { name: /筛选选项/ });
    await user.click(filterButton);

    // Enter search keyword
    const searchInput = screen.getByPlaceholderText('搜索源文本或翻译结果...');
    await user.type(searchInput, 'Hello');

    // Verify filter stats are displayed
    expect(screen.getByText('找到 1 条记录')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /清除筛选/ })).toBeInTheDocument();
  });

  it('should display no results message when no matches found', () => {
    // Mock empty history with search parameters
    useTranslationHistory.mockReturnValue({
      data: { history: [] },
      isLoading: false,
      error: null
    });

    render(<Translate />, { wrapper });

    // Check for either "没有找到匹配的记录" or "暂无翻译历史"
    const noResultsMessage = screen.getByText(/没有找到匹配的记录|暂无翻译历史/);
    expect(noResultsMessage).toBeInTheDocument();
  });
});