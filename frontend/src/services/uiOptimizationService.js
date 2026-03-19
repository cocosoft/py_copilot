/**
 * 界面优化服务
 *
 * 提供用户体验优化功能，包括界面配置、交互优化、反馈收集
 *
 * 任务编号: Phase2-Week5
 * 阶段: 第二阶段 - 功能简陋问题优化
 */

import { create } from 'zustand';

/**
 * 界面优化状态管理
 */
export const useUIOptimizationStore = create((set, get) => ({
  // 界面配置
  uiConfig: {
    theme: 'light',
    fontSize: 'medium',
    compactMode: false,
    animations: true,
    sidebarCollapsed: false,
  },

  // 用户偏好
  userPreferences: {
    defaultView: 'list',
    itemsPerPage: 20,
    autoSave: true,
    notifications: true,
  },

  // 交互状态
  interactionState: {
    activeModal: null,
    selectedItems: [],
    expandedPanels: [],
    loadingStates: {},
  },

  // 反馈数据
  feedbackData: [],

  // 更新界面配置
  updateUIConfig: (config) => {
    set((state) => ({
      uiConfig: { ...state.uiConfig, ...config },
    }));
    get().savePreferences();
  },

  // 更新用户偏好
  updateUserPreferences: (preferences) => {
    set((state) => ({
      userPreferences: { ...state.userPreferences, ...preferences },
    }));
    get().savePreferences();
  },

  // 设置交互状态
  setInteractionState: (state) => {
    set((prev) => ({
      interactionState: { ...prev.interactionState, ...state },
    }));
  },

  // 添加反馈
  addFeedback: (feedback) => {
    set((state) => ({
      feedbackData: [
        ...state.feedbackData,
        {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          ...feedback,
        },
      ],
    }));
  },

  // 保存偏好到本地存储
  savePreferences: () => {
    const { uiConfig, userPreferences } = get();
    localStorage.setItem('uiConfig', JSON.stringify(uiConfig));
    localStorage.setItem('userPreferences', JSON.stringify(userPreferences));
  },

  // 加载偏好
  loadPreferences: () => {
    try {
      const uiConfig = JSON.parse(localStorage.getItem('uiConfig'));
      const userPreferences = JSON.parse(localStorage.getItem('userPreferences'));

      if (uiConfig) {
        set((state) => ({ uiConfig: { ...state.uiConfig, ...uiConfig } }));
      }
      if (userPreferences) {
        set((state) => ({ userPreferences: { ...state.userPreferences, ...userPreferences } }));
      }
    } catch (error) {
      console.error('加载用户偏好失败:', error);
    }
  },

  // 重置配置
  resetConfig: () => {
    set({
      uiConfig: {
        theme: 'light',
        fontSize: 'medium',
        compactMode: false,
        animations: true,
        sidebarCollapsed: false,
      },
      userPreferences: {
        defaultView: 'list',
        itemsPerPage: 20,
        autoSave: true,
        notifications: true,
      },
    });
    get().savePreferences();
  },
}));

/**
 * 界面优化服务类
 */
class UIOptimizationService {
  constructor() {
    this.store = useUIOptimizationStore;
    this.initialized = false;
  }

  /**
   * 初始化服务
   */
  initialize() {
    if (this.initialized) return;

    this.store.getState().loadPreferences();
    this.initialized = true;

    console.log('界面优化服务已初始化');
  }

  /**
   * 获取界面配置
   * @returns {Object} 界面配置
   */
  getUIConfig() {
    return this.store.getState().uiConfig;
  }

  /**
   * 获取用户偏好
   * @returns {Object} 用户偏好
   */
  getUserPreferences() {
    return this.store.getState().userPreferences;
  }

  /**
   * 更新界面配置
   * @param {Object} config - 配置对象
   */
  updateUIConfig(config) {
    this.store.getState().updateUIConfig(config);
  }

  /**
   * 更新用户偏好
   * @param {Object} preferences - 偏好对象
   */
  updateUserPreferences(preferences) {
    this.store.getState().updateUserPreferences(preferences);
  }

  /**
   * 获取交互状态
   * @returns {Object} 交互状态
   */
  getInteractionState() {
    return this.store.getState().interactionState;
  }

  /**
   * 设置交互状态
   * @param {Object} state - 状态对象
   */
  setInteractionState(state) {
    this.store.getState().setInteractionState(state);
  }

  /**
   * 提交用户反馈
   * @param {Object} feedback - 反馈对象
   * @param {string} feedback.type - 反馈类型
   * @param {string} feedback.content - 反馈内容
   * @param {number} feedback.rating - 评分
   */
  submitFeedback(feedback) {
    this.store.getState().addFeedback(feedback);

    // 可以发送到后端
    console.log('用户反馈已提交:', feedback);
  }

  /**
   * 获取所有反馈
   * @returns {Array} 反馈列表
   */
  getAllFeedback() {
    return this.store.getState().feedbackData;
  }

  /**
   * 生成反馈报告
   * @returns {Object} 反馈报告
   */
  generateFeedbackReport() {
    const feedback = this.getAllFeedback();

    const typeCount = feedback.reduce((acc, item) => {
      acc[item.type] = (acc[item.type] || 0) + 1;
      return acc;
    }, {});

    const avgRating = feedback.length > 0
      ? feedback.reduce((sum, item) => sum + (item.rating || 0), 0) / feedback.length
      : 0;

    return {
      totalFeedback: feedback.length,
      typeDistribution: typeCount,
      averageRating: avgRating.toFixed(2),
      recentFeedback: feedback.slice(-10),
    };
  }

  /**
   * 获取优化建议
   * @returns {Array} 优化建议列表
   */
  getOptimizationSuggestions() {
    const config = this.getUIConfig();
    const preferences = this.getUserPreferences();
    const suggestions = [];

    // 基于配置生成建议
    if (config.compactMode && config.fontSize === 'large') {
      suggestions.push({
        type: 'conflict',
        message: '紧凑模式与大字体可能存在冲突，建议调整',
        priority: 'medium',
      });
    }

    if (!config.animations && preferences.notifications) {
      suggestions.push({
        type: 'enhancement',
        message: '开启动画可以提升通知体验',
        priority: 'low',
      });
    }

    // 基于反馈生成建议
    const report = this.generateFeedbackReport();
    if (report.averageRating < 3) {
      suggestions.push({
        type: 'improvement',
        message: '用户满意度较低，建议进行界面优化',
        priority: 'high',
      });
    }

    return suggestions;
  }

  /**
   * 重置所有配置
   */
  resetAll() {
    this.store.getState().resetConfig();
  }
}

// 导出单例
export const uiOptimizationService = new UIOptimizationService();

export default UIOptimizationService;
