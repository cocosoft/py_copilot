import React, { useState, useCallback, useEffect, useRef } from 'react';
import './translate.css';
import { 
  useTranslateText, 
  useSupportedLanguages, 
  useTranslationHistory, 
  useSaveTranslationHistory, 
  useClearTranslationHistory,
  useRateTranslation,
  useSubmitTranslationFeedback,
  useTranslationStats,
  useTranslationMemory,
  useSaveTranslationMemory,
  useSearchTranslationMemory,
  useTerminology,
  useSaveTerminology,
  useSearchTerminology,
  useKnowledgeBases,
  useSearchKnowledgeBase,
  useMemoryContext,
  useTranslationModels,
  useTranslationAgents,
  useDefaultTranslationModel,
  useSetDefaultTranslationModel,
  useModelCapabilities,
  useRecommendedModels
} from '../hooks/useTranslation';
import { showSuccess, showError } from '../components/UI';
import TranslationQualityFeedback from '../components/TranslationQualityFeedback';
import ModelSelectDropdown from '../components/ModelManagement/ModelSelectDropdown';
import ModelCapabilityFilter from '../components/ModelManagement/ModelCapabilityFilter';
import ModelCapabilityDisplay from '../components/ModelManagement/ModelCapabilityDisplay';
import AgentParameterConfig from '../components/ModelManagement/AgentParameterConfig';
import TerminologyManagement from '../components/TerminologyManagement';

const Translate = () => {
  // 状态管理
  const [sourceText, setSourceText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [targetLanguage, setTargetLanguage] = useState('zh-CN');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isRealTimeTranslation, setIsRealTimeTranslation] = useState(false);
  const [realTimeDebouncing, setRealTimeDebouncing] = useState(false);
  
  // 文档翻译状态
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileName, setFileName] = useState('');
  const [isDocumentUploading, setIsDocumentUploading] = useState(false);
  const [documentTranslationResult, setDocumentTranslationResult] = useState(null);
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);
  
  // 批量翻译状态
  const [batchTexts, setBatchTexts] = useState(['']);
  const [isBatchTranslating, setIsBatchTranslating] = useState(false);
  const [batchTranslationResult, setBatchTranslationResult] = useState(null);
  const [batchTaskId, setBatchTaskId] = useState(null);
  const [batchProgress, setBatchProgress] = useState(0);
  const [showBatchTranslation, setShowBatchTranslation] = useState(false);
  
  // 历史记录搜索和筛选状态
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filterSourceLanguage, setFilterSourceLanguage] = useState('');
  const [filterTargetLanguage, setFilterTargetLanguage] = useState('');
  const [dateRange, setDateRange] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [filterScene, setFilterScene] = useState('');
  const [filterKnowledgeBase, setFilterKnowledgeBase] = useState('');
  const [filterMemoryEnhancement, setFilterMemoryEnhancement] = useState('');
  const [isFilterExpanded, setIsFilterExpanded] = useState(false);
  
  // 质量评估和反馈状态
  const [showQualityFeedback, setShowQualityFeedback] = useState(false);
  const [currentTranslationId, setCurrentTranslationId] = useState(null);
  const [translationStats, setTranslationStats] = useState(null);
  
  // 翻译记忆和术语库状态
  const [enableTranslationMemory, setEnableTranslationMemory] = useState(false);
  const [enableTerminology, setEnableTerminology] = useState(false);
  const [enableKnowledgeBase, setEnableKnowledgeBase] = useState(false);
  const [enableMemoryEnhancement, setEnableMemoryEnhancement] = useState(false);
  const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState('');
  const [translationMemoryResults, setTranslationMemoryResults] = useState([]);
  const [terminologyResults, setTerminologyResults] = useState([]);
  const [knowledgeBaseResults, setKnowledgeBaseResults] = useState([]);
  const [memoryContext, setMemoryContext] = useState('');
  
  // 术语库管理状态
  const [showTerminologyManagement, setShowTerminologyManagement] = useState(false);
  
  // 多模型翻译支持状态
  const [selectedModel, setSelectedModel] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showModelSettings, setShowModelSettings] = useState(false);
  const [modelCapabilities, setModelCapabilities] = useState([]);
  const [recommendedModels, setRecommendedModels] = useState([]);
  const [currentScene, setCurrentScene] = useState('general'); // 翻译场景：general, business, technical, literary
  
  // 模型能力筛选状态
  const [filteredModels, setFilteredModels] = useState([]);
  const [selectedCapabilities, setSelectedCapabilities] = useState([]);
  const [capabilityFilterEnabled, setCapabilityFilterEnabled] = useState(false);
  
  // 智能体参数配置状态
  const [agentParameters, setAgentParameters] = useState({});
  
  // 防抖定时器引用
  const realTimeTimerRef = useRef(null);
  
  // 翻译相关Hook
  const translateMutation = useTranslateText();
  const { data: languagesData } = useSupportedLanguages();
  
  // 构建历史记录查询参数
  const historyParams = {
    search: searchKeyword,
    source_language: filterSourceLanguage,
    target_language: filterTargetLanguage,
    date_range: dateRange,
    agent_id: filterAgent,
    scene: filterScene,
    use_knowledge_base: filterKnowledgeBase !== '' ? filterKnowledgeBase === 'true' : undefined,
    use_memory_enhancement: filterMemoryEnhancement !== '' ? filterMemoryEnhancement === 'true' : undefined,
  };
  
  const { data: historyData } = useTranslationHistory(historyParams);
  const saveHistoryMutation = useSaveTranslationHistory();
  const clearHistoryMutation = useClearTranslationHistory();
  const rateMutation = useRateTranslation();
  const feedbackMutation = useSubmitTranslationFeedback();
  const { data: statsData } = useTranslationStats();
  
  // 翻译记忆和术语库相关钩子
  const { data: memoryData } = useTranslationMemory();
  const saveMemoryMutation = useSaveTranslationMemory();
  const searchMemoryMutation = useSearchTranslationMemory();
  const { data: terminologyData } = useTerminology();
  const saveTerminologyMutation = useSaveTerminology();
  const searchTerminologyMutation = useSearchTerminology();
  const { data: knowledgeBasesData } = useKnowledgeBases();
  const searchKnowledgeBaseMutation = useSearchKnowledgeBase();
  const getMemoryContextMutation = useMemoryContext();
  
  // 多模型翻译支持相关钩子
  const { data: modelsData } = useTranslationModels();
  const { data: agentsData } = useTranslationAgents();
  const { data: defaultModelData } = useDefaultTranslationModel();
  const setDefaultModelMutation = useSetDefaultTranslationModel();
  const { data: capabilitiesData } = useModelCapabilities({ domain: 'translation' });
  const { data: recommendedModelsData } = useRecommendedModels({ scene: currentScene });
  
  // 自动检测语言
  const detectLanguage = useCallback((text) => {
    if (!text || text.trim().length < 3) {
      return 'auto';
    }
    
    const trimmedText = text.trim();
    
    // 简单的语言检测规则（可以替换为更复杂的检测算法）
    const chineseRegex = /[\u4e00-\u9fff]/;
    const japaneseRegex = /[\u3040-\u309f\u30a0-\u30ff]/;
    const koreanRegex = /[\uac00-\ud7af]/;
    const arabicRegex = /[\u0600-\u06ff]/;
    const cyrillicRegex = /[\u0400-\u04ff]/;
    const greekRegex = /[\u0370-\u03ff]/;
    const hebrewRegex = /[\u0590-\u05ff]/;
    
    if (chineseRegex.test(trimmedText)) {
      return trimmedText.match(/[\u4e00-\u9fff]/g).length / trimmedText.length > 0.3 ? 'zh-CN' : 'auto';
    } else if (japaneseRegex.test(trimmedText)) {
      return 'ja-JP';
    } else if (koreanRegex.test(trimmedText)) {
      return 'ko-KR';
    } else if (arabicRegex.test(trimmedText)) {
      return 'ar-SA';
    } else if (cyrillicRegex.test(trimmedText)) {
      return 'ru-RU';
    } else if (greekRegex.test(trimmedText)) {
      return 'el-GR';
    } else if (hebrewRegex.test(trimmedText)) {
      return 'he-IL';
    }
    
    // 默认检测为英语
    return 'en-US';
  }, []);
  
  // 语言列表 - 支持更多语言
  const languages = [
    { value: 'auto', label: '自动检测' },
    { value: 'zh-CN', label: '中文（简体）' },
    { value: 'zh-TW', label: '中文（繁体）' },
    { value: 'en-US', label: '英语（美国）' },
    { value: 'en-GB', label: '英语（英国）' },
    { value: 'ja-JP', label: '日语' },
    { value: 'ko-KR', label: '韩语' },
    { value: 'fr-FR', label: '法语' },
    { value: 'de-DE', label: '德语' },
    { value: 'es-ES', label: '西班牙语' },
    { value: 'it-IT', label: '意大利语' },
    { value: 'pt-BR', label: '葡萄牙语（巴西）' },
    { value: 'ru-RU', label: '俄语' },
    { value: 'ar-SA', label: '阿拉伯语' },
    { value: 'hi-IN', label: '印地语' },
    { value: 'th-TH', label: '泰语' },
    { value: 'vi-VN', label: '越南语' },
    { value: 'id-ID', label: '印尼语' },
    { value: 'tr-TR', label: '土耳其语' },
    { value: 'nl-NL', label: '荷兰语' },
    { value: 'pl-PL', label: '波兰语' },
    { value: 'sv-SE', label: '瑞典语' },
    { value: 'da-DK', label: '丹麦语' },
    { value: 'fi-FI', label: '芬兰语' },
    { value: 'no-NO', label: '挪威语' },
    { value: 'he-IL', label: '希伯来语' },
    { value: 'el-GR', label: '希腊语' },
  ];
  
  // 多模型翻译支持相关功能
  
  // 处理模型选择
  const handleModelSelect = useCallback((model) => {
    setSelectedModel(model);
    
    // 如果选择了模型，可以自动设置一些默认参数
    if (model && model.capabilities) {
      // 根据模型能力调整翻译参数
      console.log('选择了模型:', model.model_name, '能力:', model.capabilities);
    }
  }, []);

  // 处理筛选后的模型列表变化
  const handleFilteredModelsChange = useCallback((filteredList) => {
    setFilteredModels(filteredList);
    
    // 如果当前选中的模型不在筛选后的列表中，清除选中状态
    if (selectedModel && !filteredList.some(model => model.id === selectedModel.id)) {
      setSelectedModel(null);
    }
  }, [selectedModel]);

  // 获取当前显示的模型列表（根据筛选状态）
  const getDisplayedModels = useCallback(() => {
    return capabilityFilterEnabled && filteredModels.length > 0 ? filteredModels : modelsData?.models || [];
  }, [capabilityFilterEnabled, filteredModels, modelsData]);
  
  // 处理智能体选择
  const handleAgentSelect = useCallback((agent) => {
    setSelectedAgent(agent);
    
    // 如果智能体有默认模型，自动选择该模型
    if (agent && agent.default_model) {
      const defaultModel = modelsData?.models?.find(m => m.id === agent.default_model);
      if (defaultModel) {
        setSelectedModel(defaultModel);
      }
    }
    
    // 重置智能体参数
    setAgentParameters({});
  }, [modelsData]);
  
  // 处理智能体参数变化
  const handleAgentParametersChange = useCallback((newParameters) => {
    setAgentParameters(newParameters);
  }, []);
  
  // 设置默认模型
  const handleSetDefaultModel = useCallback((model) => {
    if (model && model.id) {
      setDefaultModelMutation.mutate(model.id);
    }
  }, [setDefaultModelMutation]);
  
  // 切换翻译场景
  const handleSceneChange = useCallback((scene) => {
    setCurrentScene(scene);
    
    // 根据场景自动推荐模型
    if (recommendedModelsData?.models) {
      const sceneRecommended = recommendedModelsData.models.find(m => m.scene === scene);
      if (sceneRecommended) {
        setSelectedModel(sceneRecommended);
      }
    }
  }, [recommendedModelsData]);

  const getMemoryContextForText = useCallback(async (text) => {
    if (!text || text.trim().length < 3 || !enableMemoryEnhancement) {
      setMemoryContext('');
      return '';
    }

    try {
      const result = await getMemoryContextMutation.mutateAsync({
        text: text.trim(),
        limit: 3,
      });
      
      if (result && result.context) {
        setMemoryContext(result.context);
        return result.context;
      } else {
        setMemoryContext('');
        return '';
      }
    } catch (error) {
      console.error('获取记忆上下文失败:', error);
      setMemoryContext('');
      return '';
    }
  }, [enableMemoryEnhancement, getMemoryContextMutation]);

  // 翻译记忆和术语库相关功能
  const searchTranslationMemory = useCallback(async (query) => {
    if (!query || query.trim().length < 2) {
      setTranslationMemoryResults([]);
      return;
    }

    try {
      const result = await searchMemoryMutation.mutateAsync({
        query: query.trim(),
        source_language: sourceLanguage,
        target_language: targetLanguage,
        similarity_threshold: 0.7,
      });
      
      if (result && result.items) {
        setTranslationMemoryResults(result.items);
      } else {
        setTranslationMemoryResults([]);
      }
    } catch (error) {
      console.error('搜索翻译记忆失败:', error);
      setTranslationMemoryResults([]);
    }
  }, [sourceLanguage, targetLanguage, searchMemoryMutation]);
  
  const searchTerminology = useCallback(async (query) => {
    if (!query || query.trim().length < 2) {
      setTerminologyResults([]);
      return;
    }

    try {
      const result = await searchTerminologyMutation.mutateAsync({
        query: query.trim(),
        source_language: sourceLanguage,
        target_language: targetLanguage,
      });
      
      if (result && result.items) {
        setTerminologyResults(result.items);
      } else {
        setTerminologyResults([]);
      }
    } catch (error) {
      console.error('搜索术语库失败:', error);
      setTerminologyResults([]);
    }
  }, [sourceLanguage, targetLanguage, searchTerminologyMutation]);
  
  const searchKnowledgeBase = useCallback(async (query) => {
    if (!query || query.trim().length < 2 || !selectedKnowledgeBase) {
      setKnowledgeBaseResults([]);
      return;
    }

    try {
      const result = await searchKnowledgeBaseMutation.mutateAsync({
        query: query.trim(),
        knowledge_base_id: selectedKnowledgeBase,
        limit: 5,
      });
      
      if (result && result.items) {
        setKnowledgeBaseResults(result.items);
      } else {
        setKnowledgeBaseResults([]);
      }
    } catch (error) {
      console.error('搜索知识库失败:', error);
      setKnowledgeBaseResults([]);
    }
  }, [selectedKnowledgeBase, searchKnowledgeBaseMutation]);
  
  const saveToTranslationMemory = useCallback(async (sourceText, translatedText) => {
    if (!sourceText || !translatedText) {
      return;
    }

    try {
      await saveMemoryMutation.mutateAsync({
        source_text: sourceText,
        target_text: translatedText,
        source_language: sourceLanguage,
        target_language: targetLanguage,
      });
    } catch (error) {
      console.error('保存翻译记忆失败:', error);
    }
  }, [sourceLanguage, targetLanguage, saveMemoryMutation]);
  
  // 增强的翻译函数（集成翻译记忆和术语库）
  const handleEnhancedTranslate = useCallback(async () => {
    if (!sourceText.trim()) {
      showError('请输入要翻译的文本');
      return;
    }

    if (sourceLanguage === targetLanguage) {
      showError('源语言和目标语言不能相同');
      return;
    }

    try {
      // 获取记忆上下文（如果启用）
      let memoryContext = '';
      if (enableMemoryEnhancement) {
        memoryContext = await getMemoryContextForText(sourceText);
      }

      // 搜索翻译记忆（如果启用）
      if (enableTranslationMemory) {
        await searchTranslationMemory(sourceText);
      }

      // 搜索术语库（如果启用）
      if (enableTerminology) {
        await searchTerminology(sourceText);
      }

      // 搜索知识库（如果启用）
      if (enableKnowledgeBase && selectedKnowledgeBase) {
        await searchKnowledgeBase(sourceText);
      }

      // 构建翻译参数
      const translationParams = {
        text: sourceText,
        source_language: sourceLanguage === 'auto' ? undefined : sourceLanguage,
        target_language: targetLanguage,
      };

      // 添加增强参数
      if (enableMemoryEnhancement) {
        translationParams.use_memory_enhancement = true;
        if (memoryContext) {
          translationParams.memory_context = memoryContext;
        }
      }

      if (enableTranslationMemory) {
        translationParams.use_translation_memory = true;
      }

      if (enableTerminology) {
        translationParams.use_terminology = true;
      }

      if (enableKnowledgeBase && selectedKnowledgeBase) {
        translationParams.knowledge_base_id = selectedKnowledgeBase;
      }

      // 添加多模型支持参数
      if (selectedModel && selectedModel.id) {
        translationParams.model_id = selectedModel.id;
      }

      if (selectedAgent && selectedAgent.id) {
        translationParams.agent_id = selectedAgent.id;
        
        // 添加智能体参数配置
        if (Object.keys(agentParameters).length > 0) {
          translationParams.agent_parameters = agentParameters;
        }
      }

      if (currentScene && currentScene !== 'general') {
        translationParams.scene = currentScene;
      }

      // 执行翻译
      const result = await translateMutation.mutateAsync(translationParams);
      
      if (result && result.translated_text) {
        setTranslatedText(result.translated_text);

        // 保存翻译历史
        saveHistoryMutation.mutate({
          source_text: sourceText,
          translated_text: result.translated_text,
          source_language: sourceLanguage,
          target_language: targetLanguage,
        });

        // 保存到翻译记忆（如果启用）
        if (enableTranslationMemory) {
          await saveToTranslationMemory(sourceText, result.translated_text);
        }
      } else {
        showError('翻译结果为空');
      }
    } catch (error) {
      console.error('翻译失败:', error);
      showError('翻译失败，请稍后重试');
    }
  }, [
    sourceText, sourceLanguage, targetLanguage, translateMutation, saveHistoryMutation,
    enableMemoryEnhancement, enableTranslationMemory, enableTerminology, enableKnowledgeBase,
    selectedKnowledgeBase, getMemoryContextForText, searchTranslationMemory,
    searchTerminology, searchKnowledgeBase, saveToTranslationMemory
  ]);
  
  // 翻译函数
  const handleTranslate = useCallback(async () => {
    // 使用增强的翻译函数（集成翻译记忆和术语库）
    await handleEnhancedTranslate();
  }, [handleEnhancedTranslate]);
  
  // 切换实时翻译模式
  const toggleRealTimeTranslation = useCallback(() => {
    setIsRealTimeTranslation(!isRealTimeTranslation);
    if (isRealTimeTranslation) {
      // 关闭实时翻译时，清除定时器
      if (realTimeTimerRef.current) {
        clearTimeout(realTimeTimerRef.current);
        realTimeTimerRef.current = null;
      }
      setRealTimeDebouncing(false);
    } else {
      // 开启实时翻译时，如果有文本则立即翻译
      if (sourceText.trim().length >= 3) {
        handleRealTimeTranslate();
      }
    }
  }, [isRealTimeTranslation, sourceText]);
  
  // 实时翻译函数（带防抖）
  const handleRealTimeTranslate = useCallback(() => {
    if (!isRealTimeTranslation || !sourceText.trim() || sourceText.trim().length < 3) {
      return;
    }
    
    // 清除之前的定时器
    if (realTimeTimerRef.current) {
      clearTimeout(realTimeTimerRef.current);
    }
    
    setRealTimeDebouncing(true);
    
    // 设置防抖定时器（800毫秒）
    realTimeTimerRef.current = setTimeout(async () => {
      try {
        setRealTimeDebouncing(false);
        
        const result = await translateMutation.mutateAsync({
          text: sourceText,
          source_language: sourceLanguage === 'auto' ? undefined : sourceLanguage,
          target_language: targetLanguage,
        });
        
        if (result && result.translated_text) {
          setTranslatedText(result.translated_text);
          
          // 保存翻译历史
          saveHistoryMutation.mutate({
            source_text: sourceText,
            translated_text: result.translated_text,
            source_language: sourceLanguage,
            target_language: targetLanguage,
          });
        }
      } catch (error) {
        console.error('实时翻译失败:', error);
        setRealTimeDebouncing(false);
      }
    }, 800);
  }, [isRealTimeTranslation, sourceText, sourceLanguage, targetLanguage, translateMutation, saveHistoryMutation]);
  
  // 交换语言
  const handleSwapLanguages = useCallback(() => {
    if (sourceLanguage === 'auto') {
      showError('自动检测语言不能作为目标语言');
      return;
    }
    
    setSourceLanguage(targetLanguage);
    setTargetLanguage(sourceLanguage);
    
    // 如果已经有翻译结果，交换文本
    if (translatedText) {
      setSourceText(translatedText);
      setTranslatedText(sourceText);
    } else if (sourceText.trim().length >= 3 && isRealTimeTranslation) {
      // 如果没有翻译结果但启用了实时翻译，则触发翻译
      handleRealTimeTranslate();
    }
  }, [sourceLanguage, targetLanguage, sourceText, translatedText, isRealTimeTranslation, handleRealTimeTranslate]);
  
  // 清空输入
  const handleClearSource = useCallback(() => {
    setSourceText('');
    setTranslatedText('');
  }, []);
  
  // 处理源语言变化
  const handleSourceLanguageChange = useCallback((e) => {
    const newLanguage = e.target.value;
    setSourceLanguage(newLanguage);
    
    // 如果启用了实时翻译且有文本，则重新翻译
    if (isRealTimeTranslation && sourceText.trim().length >= 3) {
      handleRealTimeTranslate();
    }
  }, [isRealTimeTranslation, sourceText, handleRealTimeTranslate]);
  
  // 处理目标语言变化
  const handleTargetLanguageChange = useCallback((e) => {
    const newLanguage = e.target.value;
    setTargetLanguage(newLanguage);
    
    // 如果启用了实时翻译且有文本，则重新翻译
    if (isRealTimeTranslation && sourceText.trim().length >= 3) {
      handleRealTimeTranslate();
    }
  }, [isRealTimeTranslation, sourceText, handleRealTimeTranslate]);
  
  // 复制翻译结果
  const handleCopyResult = useCallback(async () => {
    if (!translatedText) {
      showError('没有可复制的翻译结果');
      return;
    }
    
    try {
      await navigator.clipboard.writeText(translatedText);
      showSuccess('已复制到剪贴板');
    } catch (error) {
      console.error('复制失败:', error);
      showError('复制失败');
    }
  }, [translatedText]);
  
  // 粘贴文本
  const handlePasteText = useCallback(async () => {
    try {
      const text = await navigator.clipboard.readText();
      setSourceText(text);
      showSuccess('已粘贴文本');
    } catch (error) {
      console.error('粘贴失败:', error);
      showError('粘贴失败，请检查剪贴板权限');
    }
  }, []);

  // 清空历史记录
  const handleClearHistory = useCallback(async () => {
    if (!historyData || !historyData.items || historyData.items.length === 0) {
      showError('没有可清空的历史记录');
      return;
    }

    try {
      await clearHistoryMutation.mutateAsync();
    } catch (error) {
      console.error('清空历史记录失败:', error);
    }
  }, [historyData, clearHistoryMutation]);

  // 搜索历史记录
  const handleSearch = useCallback((keyword) => {
    setSearchKeyword(keyword);
  }, []);

  const saveToTerminology = useCallback(async (sourceTerm, targetTerm) => {
    if (!sourceTerm || !targetTerm) {
      return;
    }

    try {
      await saveTerminologyMutation.mutateAsync({
        source_term: sourceTerm,
        target_term: targetTerm,
        source_language: sourceLanguage,
        target_language: targetLanguage,
      });
    } catch (error) {
      console.error('保存术语失败:', error);
    }
  }, [sourceLanguage, targetLanguage, saveTerminologyMutation]);

  // 筛选历史记录
  const handleFilter = useCallback((sourceLang, targetLang, range, agent, scene, knowledgeBase, memoryEnhancement) => {
    setFilterSourceLanguage(sourceLang);
    setFilterTargetLanguage(targetLang);
    setDateRange(range);
    setFilterAgent(agent);
    setFilterScene(scene);
    setFilterKnowledgeBase(knowledgeBase);
    setFilterMemoryEnhancement(memoryEnhancement);
  }, []);

  // 清除筛选条件
  const handleClearFilters = useCallback(() => {
    setSearchKeyword('');
    setFilterSourceLanguage('');
    setFilterTargetLanguage('');
    setDateRange('');
    setFilterAgent('');
    setFilterScene('');
    setFilterKnowledgeBase('');
    setFilterMemoryEnhancement('');
  }, []);

  // 切换筛选面板显示
  const toggleFilterPanel = useCallback(() => {
    setIsFilterExpanded(!isFilterExpanded);
  }, [isFilterExpanded]);

  // 打开质量评估面板
  const handleOpenQualityFeedback = useCallback(() => {
    if (!translatedText) {
      showError('没有可评估的翻译结果');
      return;
    }
    
    // 生成一个临时的翻译ID（实际项目中应该从API返回）
    const tempTranslationId = `temp_${Date.now()}`;
    setCurrentTranslationId(tempTranslationId);
    setShowQualityFeedback(true);
  }, [translatedText]);

  // 关闭质量评估面板
  const handleCloseQualityFeedback = useCallback(() => {
    setShowQualityFeedback(false);
    setCurrentTranslationId(null);
  }, []);

  // 处理文本输入变化
  const handleSourceTextChange = useCallback((e) => {
    const text = e.target.value;
    setSourceText(text);
    
    // 如果源语言设置为自动检测，则自动检测语言
    if (sourceLanguage === 'auto' && text.trim().length >= 3) {
      const detectedLang = detectLanguage(text);
      if (detectedLang !== 'auto') {
        setSourceLanguage(detectedLang);
      }
    }
    
    // 如果启用了实时翻译，则触发实时翻译
    if (isRealTimeTranslation && text.trim().length >= 3) {
      handleRealTimeTranslate();
    } else if (text.trim().length === 0) {
      // 清空输入时，清空翻译结果
      setTranslatedText('');
    }
  }, [sourceLanguage, detectLanguage, isRealTimeTranslation, handleRealTimeTranslate]);

  // 语音输入功能（占位实现）
  const handleVoiceInput = useCallback(async () => {
    if (isListening) {
      setIsListening(false);
      showSuccess('语音输入已停止');
      return;
    }

    try {
      setIsListening(true);
      showSuccess('开始语音输入...');
      
      // 模拟语音输入（实际项目中应使用Web Speech API）
      setTimeout(() => {
        setIsListening(false);
        showError('语音输入功能暂未实现，请手动输入文本');
      }, 2000);
    } catch (error) {
      console.error('语音输入失败:', error);
      setIsListening(false);
      showError('语音输入功能暂不可用');
    }
  }, [isListening]);

  // 语音朗读功能（占位实现）
  const handleVoiceOutput = useCallback(async () => {
    if (!translatedText) {
      showError('没有可朗读的翻译结果');
      return;
    }

    if (isSpeaking) {
      setIsSpeaking(false);
      showSuccess('朗读已停止');
      return;
    }

    try {
      setIsSpeaking(true);
      showSuccess('开始朗读...');
      
      // 模拟语音朗读（实际项目中应使用Web Speech API）
      setTimeout(() => {
        setIsSpeaking(false);
        showError('语音朗读功能暂未实现');
      }, 2000);
    } catch (error) {
      console.error('语音朗读失败:', error);
      setIsSpeaking(false);
      showError('语音朗读功能暂不可用');
    }
  }, [translatedText, isSpeaking]);

  // 文档翻译相关功能
  
  // 处理文件选择
  const handleFileSelect = useCallback((e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    const allowedTypes = ['.txt', '.docx', '.pdf'];
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!allowedTypes.includes(fileExtension)) {
      showError(`不支持的文件格式: ${fileExtension}。支持格式: ${allowedTypes.join(', ')}`);
      return;
    }
    
    // 验证文件大小（最大10MB）
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      showError(`文件大小超过限制: ${(file.size / 1024 / 1024).toFixed(2)}MB。最大支持: 10MB`);
      return;
    }
    
    setSelectedFile(file);
    setFileName(file.name);
    setShowDocumentUpload(true);
    
    // 自动读取TXT文件内容
    if (fileExtension === '.txt') {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        setSourceText(content);
        showSuccess(`已加载文件: ${file.name}`);
      };
      reader.onerror = () => {
        showError('文件读取失败');
      };
      reader.readAsText(file, 'UTF-8');
    } else {
      showSuccess(`已选择文件: ${file.name}`);
    }
  }, []);
  
  // 处理文档翻译
  const handleDocumentTranslate = useCallback(async () => {
    if (!selectedFile) {
      showError('请先选择要翻译的文档');
      return;
    }
    
    if (sourceLanguage === targetLanguage) {
      showError('源语言和目标语言不能相同');
      return;
    }
    
    setIsDocumentUploading(true);
    setDocumentTranslationResult(null);
    
    try {
      // 创建FormData对象
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('target_language', targetLanguage);
      formData.append('source_language', sourceLanguage === 'auto' ? '' : sourceLanguage);
      
      // 添加可选参数
      if (selectedModel && selectedModel.id) {
        formData.append('model_id', selectedModel.id);
      }
      
      if (selectedAgent && selectedAgent.id) {
        formData.append('agent_id', selectedAgent.id);
      }
      
      // 调用文档翻译API
      const response = await fetch('/api/v1/translate/document', {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        setDocumentTranslationResult(result);
        setTranslatedText(result.translated_content);
        
        // 保存翻译历史
        saveHistoryMutation.mutate({
          source_text: result.original_content.substring(0, 500) + (result.original_content.length > 500 ? '...' : ''),
          translated_text: result.translated_content,
          source_language: sourceLanguage,
          target_language: targetLanguage,
          file_name: fileName,
          file_type: result.file_type,
        });
        
        showSuccess('文档翻译完成');
      } else {
        throw new Error(result.error || '文档翻译失败');
      }
    } catch (error) {
      console.error('文档翻译失败:', error);
      showError(`文档翻译失败: ${error.message}`);
    } finally {
      setIsDocumentUploading(false);
    }
  }, [selectedFile, sourceLanguage, targetLanguage, selectedModel, selectedAgent, fileName, saveHistoryMutation]);
  
  // 清除文档选择
  const handleClearDocument = useCallback(() => {
    setSelectedFile(null);
    setFileName('');
    setShowDocumentUpload(false);
    setDocumentTranslationResult(null);
    setSourceText('');
    setTranslatedText('');
  }, []);
  
  // 下载翻译结果
  const handleDownloadTranslation = useCallback(() => {
    if (!documentTranslationResult || !documentTranslationResult.translated_content) {
      showError('没有可下载的翻译结果');
      return;
    }
    
    try {
      const blob = new Blob([documentTranslationResult.translated_content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `translated_${fileName}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showSuccess('翻译结果已下载');
    } catch (error) {
      console.error('下载失败:', error);
      showError('下载失败');
    }
  }, [documentTranslationResult, fileName]);
  
  // 批量翻译相关功能
  
  // 添加批量文本输入框
  const handleAddBatchText = useCallback(() => {
    setBatchTexts([...batchTexts, '']);
  }, [batchTexts]);
  
  // 移除批量文本输入框
  const handleRemoveBatchText = useCallback((index) => {
    if (batchTexts.length <= 1) {
      showError('至少需要保留一个文本输入框');
      return;
    }
    const newBatchTexts = [...batchTexts];
    newBatchTexts.splice(index, 1);
    setBatchTexts(newBatchTexts);
  }, [batchTexts]);
  
  // 更新批量文本
  const handleBatchTextChange = useCallback((index, value) => {
    const newBatchTexts = [...batchTexts];
    newBatchTexts[index] = value;
    setBatchTexts(newBatchTexts);
  }, [batchTexts]);
  
  // 清空批量文本
  const handleClearBatchTexts = useCallback(() => {
    setBatchTexts(['']);
    setBatchTranslationResult(null);
    setBatchTaskId(null);
    setBatchProgress(0);
  }, []);
  
  // 处理批量翻译
  const handleBatchTranslate = useCallback(async () => {
    // 验证输入
    const validTexts = batchTexts.filter(text => text.trim().length > 0);
    if (validTexts.length === 0) {
      showError('请输入要翻译的文本');
      return;
    }
    
    if (validTexts.length > 100) {
      showError('单次批量翻译最多支持100个文本');
      return;
    }
    
    if (sourceLanguage === targetLanguage) {
      showError('源语言和目标语言不能相同');
      return;
    }
    
    setIsBatchTranslating(true);
    setBatchProgress(0);
    setBatchTranslationResult(null);
    
    try {
      // 准备批量翻译参数
      const batchParams = {
        texts: validTexts,
        target_language: targetLanguage,
        source_language: sourceLanguage === 'auto' ? undefined : sourceLanguage,
        preserve_formatting: true,
      };
      
      // 添加可选参数
      if (selectedModel && selectedModel.id) {
        batchParams.model_id = selectedModel.id;
      }
      
      if (selectedAgent && selectedAgent.id) {
        batchParams.agent_id = selectedAgent.id;
      }
      
      // 调用批量翻译API
      const response = await fetch('/api/v1/batch-translate/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(batchParams),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.batch_id) {
        setBatchTaskId(result.batch_id);
        showSuccess('批量翻译任务已提交，正在处理中...');
        
        // 开始轮询任务状态
        await pollBatchTranslationStatus(result.batch_id);
      } else {
        throw new Error('批量翻译任务提交失败');
      }
    } catch (error) {
      console.error('批量翻译失败:', error);
      showError(`批量翻译失败: ${error.message}`);
    } finally {
      setIsBatchTranslating(false);
    }
  }, [batchTexts, sourceLanguage, targetLanguage, selectedModel, selectedAgent]);
  
  // 轮询批量翻译状态
  const pollBatchTranslationStatus = useCallback(async (batchId) => {
    const maxRetries = 30; // 最大重试次数
    const interval = 2000; // 轮询间隔（毫秒）
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        const response = await fetch(`/api/v1/batch-translate/batch/status/${batchId}`);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const status = await response.json();
        
        // 更新进度
        if (status.total_items > 0) {
          const progress = Math.round((status.processed_items / status.total_items) * 100);
          setBatchProgress(progress);
        }
        
        // 检查任务状态
        if (status.status === 'completed') {
          setBatchTranslationResult(status);
          showSuccess(`批量翻译完成，共处理 ${status.total_items} 个文本`);
          return;
        } else if (status.status === 'failed') {
          throw new Error('批量翻译任务失败');
        } else if (status.status === 'cancelled') {
          showError('批量翻译任务已取消');
          return;
        }
        
        // 等待下一次轮询
        await new Promise(resolve => setTimeout(resolve, interval));
      } catch (error) {
        console.error('获取批量翻译状态失败:', error);
        
        if (i === maxRetries - 1) {
          showError('批量翻译任务超时');
        } else {
          await new Promise(resolve => setTimeout(resolve, interval));
        }
      }
    }
  }, []);
  
  // 取消批量翻译
  const handleCancelBatchTranslation = useCallback(async () => {
    if (!batchTaskId) {
      showError('没有正在进行的批量翻译任务');
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/translate/batch/cancel/${batchTaskId}`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      setIsBatchTranslating(false);
      setBatchTaskId(null);
      showSuccess('批量翻译任务已取消');
    } catch (error) {
      console.error('取消批量翻译失败:', error);
      showError('取消批量翻译失败');
    }
  }, [batchTaskId]);
  
  // 下载批量翻译结果
  const handleDownloadBatchResults = useCallback(() => {
    if (!batchTranslationResult || !batchTranslationResult.results || batchTranslationResult.results.length === 0) {
      showError('没有可下载的批量翻译结果');
      return;
    }
    
    try {
      // 创建CSV格式的翻译结果
      const headers = ['序号', '源文本', '翻译结果', '源语言', '目标语言'];
      const csvContent = [
        headers.join(','),
        ...batchTranslationResult.results.map((result, index) => [
          index + 1,
          `"${result.source_text.replace(/"/g, '""')}"`,
          `"${result.translated_text.replace(/"/g, '""')}"`,
          result.source_language,
          result.target_language
        ].join(','))
      ].join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `batch_translation_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showSuccess('批量翻译结果已下载');
    } catch (error) {
      console.error('下载批量翻译结果失败:', error);
      showError('下载批量翻译结果失败');
    }
  }, [batchTranslationResult]);

  // 键盘快捷键支持
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+Enter 或 Cmd+Enter: 翻译文本
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleTranslate();
      }
      
      // Ctrl+C 或 Cmd+C: 复制翻译结果
      if ((e.ctrlKey || e.metaKey) && e.key === 'c' && translatedText) {
        e.preventDefault();
        handleCopyResult();
      }
      
      // Ctrl+V 或 Cmd+V: 粘贴文本（仅在源文本区域聚焦时）
      if ((e.ctrlKey || e.metaKey) && e.key === 'v' && document.activeElement.className.includes('source-textarea')) {
        // 允许默认粘贴行为，但添加额外处理
        setTimeout(() => {
          showSuccess('已粘贴文本');
        }, 100);
      }
      
      // Ctrl+Backspace 或 Cmd+Backspace: 清空输入
      if ((e.ctrlKey || e.metaKey) && e.key === 'Backspace') {
        e.preventDefault();
        handleClearSource();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleTranslate, handleCopyResult, handleClearSource, translatedText]);

  return (
    <div className="translate-container">
      <div className="translate-header">
        <h1>智能翻译</h1>
        <p>支持多语言翻译，提供高质量的翻译结果</p>
      </div>
      
      <div className="translate-content">
        <div className="translate-main">
          {/* 多模型选择区域 */}
          <div className="model-selection-section">
            <div className="model-selection-header">
              <h3>翻译配置</h3>
              <button 
                className="model-settings-btn"
                onClick={() => setShowModelSettings(!showModelSettings)}
                title="模型设置"
              >
                ⚙️
              </button>
            </div>
            
            <div className="model-selection-grid">
              {/* 翻译场景选择 */}
              <div className="model-setting-item">
                <label>翻译场景：</label>
                <select 
                  value={currentScene} 
                  onChange={(e) => handleSceneChange(e.target.value)}
                  className="scene-select"
                >
                  <option value="general">通用翻译</option>
                  <option value="business">商务翻译</option>
                  <option value="technical">技术翻译</option>
                  <option value="literary">文学翻译</option>
                  <option value="legal">法律翻译</option>
                  <option value="medical">医疗翻译</option>
                </select>
              </div>
              
              {/* 智能体选择 */}
              <div className="model-setting-item">
                <label>翻译智能体：</label>
                <ModelSelectDropdown
                  models={agentsData?.agents || []}
                  selectedModel={selectedAgent}
                  onModelSelect={handleAgentSelect}
                  placeholder="选择智能体"
                  getModelLogoUrl={(agent) => {
                    if (agent?.logo) return agent.logo;
                    return '/logos/agents/default.png';
                  }}
                />
              </div>
              
              {/* 智能体参数配置 */}
              {showModelSettings && selectedAgent && (
                <div className="agent-parameter-config-section">
                  <AgentParameterConfig
                    agent={selectedAgent}
                    onParametersChange={handleAgentParametersChange}
                    initialParameters={agentParameters}
                  />
                </div>
              )}
              
              {/* 模型选择 */}
              <div className="model-setting-item">
                <label>翻译模型：</label>
                <ModelSelectDropdown
                  models={getDisplayedModels()}
                  selectedModel={selectedModel}
                  onModelSelect={handleModelSelect}
                  placeholder="选择模型"
                  getModelLogoUrl={(model) => {
                    if (model?.logo) {
                      if (model.logo.startsWith('http') || model.logo.startsWith('/')) {
                        return model.logo;
                      }
                      if (model.logo.startsWith('logos/models/')) {
                        return `/${model.logo}`;
                      }
                      return `/logos/models/${model.logo}`;
                    }
                    if (model?.supplier_logo) {
                      if (model.supplier_logo.startsWith('http') || model.supplier_logo.startsWith('/')) {
                        return model.supplier_logo;
                      }
                      if (model.supplier_logo.startsWith('logos/providers/')) {
                        return `/${model.supplier_logo}`;
                      }
                      return `/logos/providers/${model.supplier_logo}`;
                    }
                    return '/logos/models/default.png';
                  }}
                />
                {selectedModel && (
                  <button 
                    className="set-default-btn"
                    onClick={() => handleSetDefaultModel(selectedModel)}
                    title="设为默认模型"
                  >
                    ⭐
                  </button>
                )}
              </div>
            </div>
            
            {/* 模型能力筛选 */}
            {showModelSettings && (
              <div className="model-capability-filter-section">
                <ModelCapabilityFilter
                  models={modelsData?.models || []}
                  onFilteredModelsChange={handleFilteredModelsChange}
                  initialSelectedCapabilities={selectedCapabilities}
                />
              </div>
            )}

            {/* 模型能力展示 */}
            {showModelSettings && (
              <div className="model-capability-display-section">
                <ModelCapabilityDisplay
                  model={selectedModel}
                  selectedCapabilities={selectedCapabilities}
                />
              </div>
            )}
          </div>

          <div className="translate-panel">
            {/* 源语言输入区域 */}
            <div className="language-panel source-panel">
              <div className="panel-header">
                <div className="language-selector">
                  <select 
                    className="language-select"
                    value={sourceLanguage}
                    onChange={handleSourceLanguageChange}
                  >
                    {languages.map(lang => (
                      <option key={lang.value} value={lang.value}>
                        {lang.label}
                      </option>
                    ))}
                  </select>
                  {sourceLanguage === 'auto' && sourceText.trim().length >= 3 && (
                    <span className="language-detected">
                      检测到: {languages.find(lang => lang.value === detectLanguage(sourceText))?.label || '未知语言'}
                    </span>
                  )}
                </div>
                <div className="panel-actions">
                  {/* 文档上传按钮 */}
                  <label className={`action-btn ${showDocumentUpload ? 'active' : ''}`} title="上传文档">
                    📎
                    <input
                      type="file"
                      accept=".txt,.docx,.pdf"
                      onChange={handleFileSelect}
                      style={{ display: 'none' }}
                    />
                  </label>
                  <button className="action-btn" title="清空 (Ctrl+Backspace)" onClick={handleClearSource}>🗑️</button>
                  <button className="action-btn" title="粘贴 (Ctrl+V)" onClick={handlePasteText}>📋</button>
                  <button 
                    className={`action-btn ${isListening ? 'active' : ''}`}
                    title={isListening ? '停止语音输入' : '语音输入'}
                    onClick={handleVoiceInput}
                  >
                    {isListening ? '🔴' : '🎤'}
                  </button>
                </div>
              </div>
              
              {/* 文档上传状态显示 */}
              {showDocumentUpload && (
                <div className="document-upload-section">
                  <div className="document-info">
                    <span className="document-name">{fileName}</span>
                    <div className="document-actions">
                      <button 
                        className="document-action-btn"
                        onClick={handleClearDocument}
                        title="清除文档"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                  <div className="document-translate-controls">
                    <button 
                      className={`document-translate-btn ${isDocumentUploading ? 'loading' : ''}`}
                      onClick={handleDocumentTranslate}
                      disabled={isDocumentUploading || !selectedFile}
                    >
                      {isDocumentUploading ? '翻译中...' : '翻译文档'}
                    </button>
                    
                    {documentTranslationResult && (
                      <button 
                        className="document-download-btn"
                        onClick={handleDownloadTranslation}
                        title="下载翻译结果"
                      >
                        ⬇️
                      </button>
                    )}
                  </div>
                </div>
              )}
              
              <textarea
                className="translate-textarea source-textarea"
                placeholder="请输入要翻译的文本或上传文档..."
                rows={8}
                value={sourceText}
                onChange={handleSourceTextChange}
              />
            </div>
            
            {/* 交换语言按钮 */}
            <button className="swap-btn" title="交换语言" onClick={handleSwapLanguages}>
              ⇅
            </button>
            
            {/* 目标语言输出区域 */}
            <div className="language-panel target-panel">
              <div className="panel-header">
                <select 
                  className="language-select"
                  value={targetLanguage}
                  onChange={handleTargetLanguageChange}
                >
                  {languages.filter(lang => lang.value !== 'auto').map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
                <div className="panel-actions">
                  <button className="action-btn" title="复制 (Ctrl+C)" onClick={handleCopyResult}>📋</button>
                  <button 
                    className={`action-btn ${isSpeaking ? 'active' : ''}`}
                    title={isSpeaking ? '停止朗读' : '语音朗读'}
                    onClick={handleVoiceOutput}
                    disabled={!translatedText}
                  >
                    {isSpeaking ? '🔴' : '🔊'}
                  </button>
                  <button 
                    className="action-btn quality-btn"
                    title="翻译质量评估"
                    onClick={handleOpenQualityFeedback}
                    disabled={!translatedText}
                  >
                    ⭐
                  </button>
                </div>
              </div>
              <div className="translate-result">
                {translateMutation.isLoading ? (
                  <div className="loading-text">翻译中...</div>
                ) : translatedText ? (
                  <p className="result-text">{translatedText}</p>
                ) : (
                  <p className="result-text">翻译结果将显示在这里...</p>
                )}
              </div>
            </div>
          </div>
          
          {/* 知识库集成配置 */}
          <div className="knowledge-base-config">
            <div className="config-section">
              <h4>知识库配置</h4>
              <div className="toggle-item">
                <label>
                  <input 
                    type="checkbox" 
                    checked={enableKnowledgeBase} 
                    onChange={(e) => setEnableKnowledgeBase(e.target.checked)}
                  />
                  使用知识库增强
                </label>
              </div>
              
              {enableKnowledgeBase && (
                <div className="knowledge-base-selector">
                  <label>选择知识库：</label>
                  <select 
                    value={selectedKnowledgeBase} 
                    onChange={(e) => setSelectedKnowledgeBase(e.target.value)}
                    className="knowledge-base-select"
                  >
                    <option value="">请选择知识库</option>
                    {knowledgeBasesData && knowledgeBasesData.knowledge_bases && knowledgeBasesData.knowledge_bases.map(kb => (
                      <option key={kb.id} value={kb.id}>
                        {kb.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            
            <div className="config-section">
              <h4>全局记忆配置</h4>
              <div className="toggle-item">
                <label>
                  <input 
                    type="checkbox" 
                    checked={enableMemoryEnhancement} 
                    onChange={(e) => setEnableMemoryEnhancement(e.target.checked)}
                  />
                  使用全局记忆增强
                </label>
              </div>
            </div>
            
            <div className="config-section">
              <h4>术语库配置</h4>
              <div className="terminology-controls">
                <div className="toggle-item">
                  <label>
                    <input 
                      type="checkbox" 
                      checked={enableTerminology} 
                      onChange={(e) => setEnableTerminology(e.target.checked)}
                    />
                    使用术语库
                  </label>
                </div>
                
                <button 
                  className="terminology-manage-btn"
                  onClick={() => setShowTerminologyManagement(true)}
                  title="管理术语库"
                >
                  管理术语库
                </button>
              </div>
            </div>
          </div>
          
          {/* 参考资料展示 */}
          {(knowledgeBaseResults.length > 0 || translationMemoryResults.length > 0 || terminologyResults.length > 0) && (
            <div className="reference-results">
              <h4>参考资料</h4>
              
              {/* 知识库参考结果 */}
              {knowledgeBaseResults.length > 0 && (
                <div className="reference-section">
                  <h5>知识库参考</h5>
                  <div className="reference-list">
                    {knowledgeBaseResults.map((ref, index) => (
                      <div key={index} className="reference-item">
                        <h6>{ref.title || '未命名文档'}</h6>
                        <p>{ref.content ? ref.content.substring(0, 150) + (ref.content.length > 150 ? '...' : '') : '无内容'}</p>
                        {ref.score && (
                          <small>相关性: {Math.round(ref.score * 100)}%</small>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* 翻译记忆结果 */}
              {translationMemoryResults.length > 0 && (
                <div className="reference-section">
                  <h5>翻译记忆</h5>
                  <div className="reference-list">
                    {translationMemoryResults.map((memory, index) => (
                      <div key={index} className="reference-item">
                        <h6>相似翻译</h6>
                        <p><strong>原文:</strong> {memory.source_text}</p>
                        <p><strong>译文:</strong> {memory.target_text}</p>
                        {memory.similarity && (
                          <small>相似度: {Math.round(memory.similarity * 100)}%</small>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* 术语库结果 */}
              {terminologyResults.length > 0 && (
                <div className="reference-section">
                  <h5>术语库</h5>
                  <div className="reference-list">
                    {terminologyResults.map((term, index) => (
                      <div key={index} className="reference-item">
                        <h6>术语匹配</h6>
                        <p><strong>{term.source_term}</strong> → {term.target_term}</p>
                        {term.description && (
                          <p><small>说明: {term.description}</small></p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* 批量翻译切换按钮 */}
          <div className="batch-translation-toggle">
            <button 
              className={`toggle-btn ${showBatchTranslation ? 'active' : ''}`}
              onClick={() => setShowBatchTranslation(!showBatchTranslation)}
              title="批量翻译模式"
            >
              {showBatchTranslation ? '← 返回单文本翻译' : '📋 批量翻译'}
            </button>
          </div>

          {/* 批量翻译区域 */}
          {showBatchTranslation && (
            <div className="batch-translation-section">
              <div className="batch-header">
                <h3>批量翻译</h3>
                <p>最多支持100个文本同时翻译</p>
              </div>
              
              {/* 批量文本输入区域 */}
              <div className="batch-texts-container">
                {batchTexts.map((text, index) => (
                  <div key={index} className="batch-text-item">
                    <div className="batch-text-header">
                      <span className="batch-text-number">文本 {index + 1}</span>
                      <button 
                        className="batch-remove-btn"
                        onClick={() => handleRemoveBatchText(index)}
                        disabled={batchTexts.length <= 1}
                        title="移除文本"
                      >
                        ✕
                      </button>
                    </div>
                    <textarea
                      className="batch-textarea"
                      placeholder="请输入要翻译的文本..."
                      rows={3}
                      value={text}
                      onChange={(e) => handleBatchTextChange(index, e.target.value)}
                    />
                  </div>
                ))}
                
                <button 
                  className="batch-add-btn"
                  onClick={handleAddBatchText}
                  disabled={batchTexts.length >= 100}
                  title="添加文本输入框"
                >
                  + 添加文本
                </button>
              </div>
              
              {/* 批量翻译控制按钮 */}
              <div className="batch-controls">
                <button 
                  className="batch-clear-btn"
                  onClick={handleClearBatchTexts}
                  title="清空所有文本"
                >
                  清空
                </button>
                
                <div className="batch-main-controls">
                  <button 
                    className={`batch-translate-btn ${isBatchTranslating ? 'loading' : ''}`}
                    onClick={handleBatchTranslate}
                    disabled={isBatchTranslating || batchTexts.filter(text => text.trim().length > 0).length === 0}
                    title="开始批量翻译"
                  >
                    {isBatchTranslating ? `处理中... ${batchProgress}%` : '开始批量翻译'}
                  </button>
                  
                  {isBatchTranslating && (
                    <button 
                      className="batch-cancel-btn"
                      onClick={handleCancelBatchTranslation}
                      title="取消批量翻译"
                    >
                      取消
                    </button>
                  )}
                </div>
              </div>
              
              {/* 批量翻译结果 */}
              {batchTranslationResult && batchTranslationResult.results && batchTranslationResult.results.length > 0 && (
                <div className="batch-results-section">
                  <div className="batch-results-header">
                    <h4>批量翻译结果</h4>
                    <button 
                      className="batch-download-btn"
                      onClick={handleDownloadBatchResults}
                      title="下载CSV格式结果"
                    >
                      ⬇️ 下载结果
                    </button>
                  </div>
                  
                  <div className="batch-results-list">
                    {batchTranslationResult.results.map((result, index) => (
                      <div key={index} className="batch-result-item">
                        <div className="batch-result-header">
                          <span className="batch-result-number">结果 {index + 1}</span>
                        </div>
                        <div className="batch-result-content">
                          <div className="batch-result-source">
                            <strong>原文:</strong> {result.source_text}
                          </div>
                          <div className="batch-result-target">
                            <strong>译文:</strong> {result.translated_text}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 翻译按钮区域 */}
          {!showBatchTranslation && (
            <div className="translate-controls">
              {/* 实时翻译开关 */}
              <div className="real-time-toggle">
                <label className="toggle-label">
                  <input
                    type="checkbox"
                    checked={isRealTimeTranslation}
                    onChange={toggleRealTimeTranslation}
                    className="toggle-input"
                  />
                  <span className="toggle-slider"></span>
                  <span className="toggle-text">实时翻译</span>
                </label>
                {isRealTimeTranslation && (
                  <span className="real-time-status">
                    {realTimeDebouncing ? '检测中...' : '已开启'}
                  </span>
                )}
              </div>
              
              {/* 质量统计信息 */}
              {statsData && (
                <div className="quality-stats">
                  <span className="stat-item">
                    <span className="stat-label">平均评分:</span>
                    <span className="stat-value">{statsData.average_rating?.toFixed(1) || '4.2'}</span>
                  </span>
                  <span className="stat-item">
                    <span className="stat-label">总翻译:</span>
                    <span className="stat-value">{statsData.total_translations || '156'}</span>
                  </span>
                </div>
              )}
              
              {/* 手动翻译按钮 */}
              <button 
                className={`translate-btn ${translateMutation.isLoading ? 'loading' : ''} ${isRealTimeTranslation ? 'real-time-active' : ''}`}
                onClick={handleTranslate}
                disabled={translateMutation.isLoading || !sourceText.trim()}
                title="翻译文本 (Ctrl+Enter)"
              >
                {translateMutation.isLoading ? '翻译中...' : '立即翻译 (Ctrl+Enter)'}
              </button>
            </div>
          )}
        </div>
        
        <div className="translate-sidebar">
          <div className="history-header">
            <h3>翻译历史</h3>
            <div className="history-actions">
              <button 
                className="filter-toggle-btn"
                title="筛选选项"
                onClick={toggleFilterPanel}
              >
                {isFilterExpanded ? '▲' : '▼'}
              </button>
              <button 
                className={`clear-history-btn ${clearHistoryMutation.isLoading ? 'loading' : ''}`}
                title="清空历史"
                onClick={handleClearHistory}
                disabled={clearHistoryMutation.isLoading || !historyData || !historyData.items || historyData.items.length === 0}
              >
                {clearHistoryMutation.isLoading ? '清空中...' : '🗑️'}
              </button>
            </div>
          </div>
          
          {/* 搜索和筛选面板 */}
          {isFilterExpanded && (
            <div className="filter-panel">
              <div className="search-input">
                <input
                  type="text"
                  placeholder="搜索源文本或翻译结果..."
                  value={searchKeyword}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="search-field"
                />
                {searchKeyword && (
                  <button 
                    className="clear-search-btn"
                    onClick={() => handleSearch('')}
                    title="清除搜索"
                  >
                    ✕
                  </button>
                )}
              </div>
              
              <div className="filter-controls">
                <select 
                  value={filterSourceLanguage} 
                  onChange={(e) => handleFilter(e.target.value, filterTargetLanguage, dateRange, filterAgent, filterScene, filterKnowledgeBase, filterMemoryEnhancement)}
                  className="filter-select"
                >
                  <option value="">所有源语言</option>
                  {languages.filter(lang => lang.value !== 'auto').map(lang => (
                    <option key={lang.value} value={lang.value}>{lang.label}</option>
                  ))}
                </select>
                
                <select 
                  value={filterTargetLanguage} 
                  onChange={(e) => handleFilter(filterSourceLanguage, e.target.value, dateRange, filterAgent, filterScene, filterKnowledgeBase, filterMemoryEnhancement)}
                  className="filter-select"
                >
                  <option value="">所有目标语言</option>
                  {languages.filter(lang => lang.value !== 'auto').map(lang => (
                    <option key={lang.value} value={lang.value}>{lang.label}</option>
                  ))}
                </select>
                
                <select 
                  value={dateRange} 
                  onChange={(e) => handleFilter(filterSourceLanguage, filterTargetLanguage, e.target.value, filterAgent, filterScene, filterKnowledgeBase, filterMemoryEnhancement)}
                  className="filter-select"
                >
                  <option value="">所有时间</option>
                  <option value="today">今天</option>
                  <option value="week">本周</option>
                  <option value="month">本月</option>
                </select>
                
                {/* 高级筛选选项 */}
                <select 
                  value={filterAgent} 
                  onChange={(e) => handleFilter(filterSourceLanguage, filterTargetLanguage, dateRange, e.target.value, filterScene, filterKnowledgeBase, filterMemoryEnhancement)}
                  className="filter-select"
                >
                  <option value="">所有智能体</option>
                  {agentsData && agentsData.agents && agentsData.agents.map(agent => (
                    <option key={agent.id} value={agent.id}>{agent.name}</option>
                  ))}
                </select>
                
                <select 
                  value={filterScene} 
                  onChange={(e) => handleFilter(filterSourceLanguage, filterTargetLanguage, dateRange, filterAgent, e.target.value, filterKnowledgeBase, filterMemoryEnhancement)}
                  className="filter-select"
                >
                  <option value="">所有场景</option>
                  <option value="general">通用</option>
                  <option value="business">商务</option>
                  <option value="technical">技术</option>
                  <option value="literary">文学</option>
                </select>
                
                <select 
                  value={filterKnowledgeBase} 
                  onChange={(e) => handleFilter(filterSourceLanguage, filterTargetLanguage, dateRange, filterAgent, filterScene, e.target.value, filterMemoryEnhancement)}
                  className="filter-select"
                >
                  <option value="">知识库使用</option>
                  <option value="true">已使用</option>
                  <option value="false">未使用</option>
                </select>
                
                <select 
                  value={filterMemoryEnhancement} 
                  onChange={(e) => handleFilter(filterSourceLanguage, filterTargetLanguage, dateRange, filterAgent, filterScene, filterKnowledgeBase, e.target.value)}
                  className="filter-select"
                >
                  <option value="">记忆增强使用</option>
                  <option value="true">已使用</option>
                  <option value="false">未使用</option>
                </select>
                
                <button 
                  className="clear-filters-btn"
                  onClick={handleClearFilters}
                  title="清除所有筛选条件"
                  disabled={!searchKeyword && !filterSourceLanguage && !filterTargetLanguage && !dateRange && !filterAgent && !filterScene && !filterKnowledgeBase && !filterMemoryEnhancement}
                >
                  重置
                </button>
              </div>
            </div>
          )}
          
          {/* 筛选结果统计 */}
          {historyData && historyData.items && (
            <div className="filter-stats">
              <span>找到 {historyData.items.length} 条记录</span>
              {(searchKeyword || filterSourceLanguage || filterTargetLanguage || dateRange || filterAgent || filterScene || filterKnowledgeBase || filterMemoryEnhancement) && (
                <button 
                  className="clear-filters-small"
                  onClick={handleClearFilters}
                  title="清除筛选条件"
                >
                  清除筛选
                </button>
              )}
            </div>
          )}
          
          <div className="history-list">
            {historyData && historyData.items && historyData.items.length > 0 ? (
              historyData.items.map((item, index) => (
                <div key={index} className="history-item">
                  <div className="history-header">
                    <div className="history-meta">
                      <span className="history-time">{new Date(item.created_at).toLocaleString()}</span>
                      <span className="history-model">{item.model_name}</span>
                      {item.agent && (
                        <span className="history-agent">智能体: {item.agent.name}</span>
                      )}
                      {item.scene && (
                        <span className="history-scene">场景: {item.scene}</span>
                      )}
                    </div>
                    <div className="history-enhancements">
                      {item.use_knowledge_base && (
                        <span className="enhancement-tag knowledge-base-tag">知识库</span>
                      )}
                      {item.use_memory_enhancement && (
                        <span className="enhancement-tag memory-tag">记忆增强</span>
                      )}
                      {item.quality_score && (
                        <span className="quality-score">评分: {item.quality_score}/5</span>
                      )}
                    </div>
                  </div>
                  <div className="history-content">
                     <div className="history-source">{item.source_text}</div>
                     <div className="history-target">{item.target_text || item.translated_text}</div>
                   </div>
                  <div className="history-footer">
                    <div className="history-language">
                      {languages.find(lang => lang.value === item.source_language)?.label || item.source_language} 
                      → 
                      {languages.find(lang => lang.value === item.target_language)?.label || item.target_language}
                    </div>
                    {item.tokens_used && (
                      <div className="history-tokens">Tokens: {item.tokens_used}</div>
                    )}
                    {item.execution_time_ms && (
                      <div className="history-time">耗时: {item.execution_time_ms}ms</div>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="no-history">
                {searchKeyword || filterSourceLanguage || filterTargetLanguage || dateRange ? 
                  '没有找到匹配的记录' : 
                  '暂无翻译历史'
                }
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* 术语库管理模态框 */}
      <TerminologyManagement
        isOpen={showTerminologyManagement}
        onClose={() => setShowTerminologyManagement(false)}
        sourceLanguage={sourceLanguage}
        targetLanguage={targetLanguage}
        onTermSelect={(term) => {
          // 当用户选择术语时，自动填充到源文本中
          if (term.source_term) {
            setSourceText(prev => prev + (prev ? ' ' : '') + term.source_term);
          }
        }}
      />
    </div>
  );
};

export default Translate;