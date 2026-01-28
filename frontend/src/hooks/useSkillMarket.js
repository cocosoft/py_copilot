import { useState, useEffect, useCallback, useMemo } from 'react';

/**
 * 技能市场Hook
 * 提供技能数据的获取、筛选、搜索和安装功能
 */
const useSkillMarket = () => {
  // 状态管理
  const [skills, setSkills] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({});
  const [sortBy, setSortBy] = useState('popularity');

  // 模拟技能数据（实际项目中应该从API获取）
  const mockSkills = [
    {
      id: 'data-analysis',
      name: '数据分析助手',
      description: '强大的数据分析工具，支持多种数据格式和可视化',
      longDescription: '这是一个功能强大的数据分析技能，支持Excel、CSV、JSON等多种数据格式。可以自动识别数据模式，生成统计报告和可视化图表。',
      category: '数据分析',
      tags: ['数据分析', '可视化', '统计', 'Excel', 'CSV'],
      rating: 4.8,
      reviewCount: 124,
      downloads: 2560,
      version: '1.2.3',
      size: '2.3 MB',
      lastUpdated: '2024-01-15',
      author: 'Py Copilot团队',
      official: true,
      popular: true,
      installed: false,
      icon: '/logos/skills/data-analysis.png',
      dependencies: [
        { name: 'pandas', version: '>=1.5.0' },
        { name: 'matplotlib', version: '>=3.6.0' }
      ],
      examples: [
        {
          title: '基本数据分析',
          description: '快速分析数据集的统计信息',
          code: 'await skill.analyze(data, { method: "descriptive" })'
        }
      ],
      reviews: [
        {
          author: '数据分析师',
          rating: 5,
          date: '2024-01-20',
          content: '非常实用的工具，大大提高了我的工作效率！'
        }
      ],
      compatibility: 'Py Copilot 1.0+',
      license: 'MIT'
    },
    {
      id: 'web-scraping',
      name: '网页爬虫',
      description: '自动化网页数据采集工具，支持多种网站和反爬机制',
      category: '数据采集',
      tags: ['爬虫', '数据采集', '自动化', '网页'],
      rating: 4.5,
      reviewCount: 89,
      downloads: 1870,
      version: '2.1.0',
      size: '1.8 MB',
      lastUpdated: '2024-01-10',
      author: 'WebTools Inc.',
      official: false,
      popular: true,
      installed: true,
      icon: '/logos/skills/web-scraping.png',
      dependencies: [
        { name: 'requests', version: '>=2.28.0' },
        { name: 'beautifulsoup4', version: '>=4.11.0' }
      ]
    },
    {
      id: 'image-processing',
      name: '图像处理',
      description: '专业的图像处理和分析工具',
      category: '多媒体',
      tags: ['图像处理', '计算机视觉', 'AI', '图片'],
      rating: 4.3,
      reviewCount: 67,
      downloads: 920,
      version: '1.0.5',
      size: '3.1 MB',
      lastUpdated: '2024-01-08',
      author: 'VisionAI',
      official: false,
      popular: false,
      installed: false,
      icon: '/logos/skills/image-processing.png'
    },
    {
      id: 'document-ai',
      name: '文档智能处理',
      description: 'AI驱动的文档分析和处理工具',
      category: '文档处理',
      tags: ['文档', 'AI', 'OCR', 'PDF'],
      rating: 4.7,
      reviewCount: 156,
      downloads: 2100,
      version: '1.3.2',
      size: '4.2 MB',
      lastUpdated: '2024-01-18',
      author: 'DocAI Labs',
      official: true,
      popular: true,
      installed: false,
      icon: '/logos/skills/document-ai.png'
    },
    {
      id: 'automation',
      name: '工作流自动化',
      description: '自动化重复性工作任务',
      category: '自动化',
      tags: ['自动化', '工作流', '效率', 'RPA'],
      rating: 4.4,
      reviewCount: 93,
      downloads: 1450,
      version: '1.1.0',
      size: '2.7 MB',
      lastUpdated: '2024-01-12',
      author: 'AutoFlow',
      official: false,
      popular: false,
      installed: true,
      icon: '/logos/skills/automation.png'
    },
    {
      id: 'api-integration',
      name: 'API集成工具',
      description: '简化API集成和数据处理',
      category: '开发工具',
      tags: ['API', '集成', '开发', 'REST'],
      rating: 4.6,
      reviewCount: 78,
      downloads: 1100,
      version: '1.2.1',
      size: '1.5 MB',
      lastUpdated: '2024-01-14',
      author: 'DevTools',
      official: true,
      popular: false,
      installed: false,
      icon: '/logos/skills/api-integration.png'
    }
  ];

  // 获取技能数据
  const fetchSkills = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // 从真实API获取数据
      const response = await fetch('/api/v1/skill-management/market');
      
      if (!response.ok) {
        throw new Error(`API调用失败: ${response.status}`);
      }
      
      const data = await response.json();
      
      // 转换API响应格式以匹配前端期望的格式
      const formattedSkills = data.skills.map(skill => ({
        id: skill.id,
        name: skill.name,
        description: skill.description,
        category: skill.category,
        tags: skill.tags || [],
        rating: skill.rating,
        reviewCount: Math.floor(skill.downloads * 0.1), // 模拟评论数
        downloads: skill.downloads,
        version: skill.version,
        size: `${Math.floor(Math.random() * 5) + 1}.${Math.floor(Math.random() * 10)} MB`, // 模拟大小
        lastUpdated: skill.last_updated,
        author: skill.author,
        official: skill.official,
        popular: skill.popular,
        installed: skill.installed,
        icon: skill.icon
      }));
      
      setSkills(formattedSkills);
    } catch (err) {
      setError(err);
      console.error('获取技能数据失败:', err);
      
      // 错误时使用模拟数据作为后备
      setSkills(mockSkills);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 安装技能
  const installSkill = useCallback(async (skillId) => {
    try {
      // 调用真实API
      const response = await fetch('/api/v1/skill-management/install', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ skill_id: skillId, source: 'market' })
      });
      
      if (!response.ok) {
        throw new Error(`安装技能失败: ${response.status}`);
      }
      
      const result = await response.json();
      
      // 更新本地状态
      setSkills(prevSkills => 
        prevSkills.map(skill => 
          skill.id === skillId ? { ...skill, installed: true } : skill
        )
      );
      
      console.log(`技能 ${skillId} 安装成功`, result);
      return result;
    } catch (err) {
      console.error(`安装技能 ${skillId} 失败:`, err);
      throw err;
    }
  }, []);

  // 卸载技能
  const uninstallSkill = useCallback(async (skillId) => {
    try {
      // 调用真实API
      const response = await fetch('/api/v1/skill-management/uninstall', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ skill_id: skillId })
      });
      
      if (!response.ok) {
        throw new Error(`卸载技能失败: ${response.status}`);
      }
      
      const result = await response.json();
      
      // 更新本地状态
      setSkills(prevSkills => 
        prevSkills.map(skill => 
          skill.id === skillId ? { ...skill, installed: false } : skill
        )
      );
      
      console.log(`技能 ${skillId} 卸载成功`, result);
      return result;
    } catch (err) {
      console.error(`卸载技能 ${skillId} 失败:`, err);
      throw err;
    }
  }, []);

  // 刷新技能数据
  const refreshSkills = useCallback(() => {
    return fetchSkills();
  }, [fetchSkills]);

  // 获取分类列表
  const categories = useMemo(() => {
    const allCategories = skills.map(skill => skill.category);
    return [...new Set(allCategories)].filter(Boolean);
  }, [skills]);

  // 筛选和搜索技能
  const filteredSkills = useMemo(() => {
    let filtered = [...skills];

    // 搜索筛选
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(skill => 
        skill.name.toLowerCase().includes(query) ||
        skill.description.toLowerCase().includes(query) ||
        skill.tags?.some(tag => tag.toLowerCase().includes(query)) ||
        skill.category?.toLowerCase().includes(query)
      );
    }

    // 分类筛选
    if (filters.categories?.length > 0) {
      filtered = filtered.filter(skill => 
        filters.categories.includes(skill.category)
      );
    }

    // 安装状态筛选
    if (filters.installed !== undefined) {
      filtered = filtered.filter(skill => skill.installed === filters.installed);
    }

    // 评分筛选
    if (filters.minRating) {
      filtered = filtered.filter(skill => skill.rating >= filters.minRating);
    }

    // 官方技能筛选
    if (filters.official) {
      filtered = filtered.filter(skill => skill.official);
    }

    // 最近更新筛选
    if (filters.recentlyUpdated) {
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      
      filtered = filtered.filter(skill => 
        new Date(skill.lastUpdated) > thirtyDaysAgo
      );
    }

    // 排序
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'popularity':
          return b.downloads - a.downloads;
        case 'rating':
          return b.rating - a.rating;
        case 'downloads':
          return b.downloads - a.downloads;
        case 'recent':
          return new Date(b.lastUpdated) - new Date(a.lastUpdated);
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

    return filtered;
  }, [skills, searchQuery, filters, sortBy]);

  // 初始化加载技能数据
  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  return {
    // 数据
    skills,
    filteredSkills,
    categories,
    
    // 状态
    isLoading,
    error,
    
    // 搜索和筛选
    searchQuery,
    setSearchQuery,
    filters,
    setFilters,
    sortBy,
    setSortBy,
    
    // 操作
    installSkill,
    uninstallSkill,
    refreshSkills
  };
};

export default useSkillMarket;