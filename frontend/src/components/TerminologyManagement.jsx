import React, { useState, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getTerminology, saveTerminology, searchTerminology } from '../services/translationService';
import { useI18n } from '../hooks/useI18n';
import './TerminologyManagement.css';

const TerminologyManagement = ({ 
  isOpen = false, 
  onClose = () => {},
  sourceLanguage = 'en',
  targetLanguage = 'zh',
  onTermSelect = () => {}
}) => {
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState('search');
  const [searchQuery, setSearchQuery] = useState('');
  const [newTerm, setNewTerm] = useState({
    source_term: '',
    target_term: '',
    domain: 'general',
    description: '',
    tags: ''
  });
  const [terminologyList, setTerminologyList] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const queryClient = useQueryClient();

  // 获取术语库列表查询
  const { data: terminologyData, refetch: refetchTerminology } = useQuery({
    queryKey: ['terminology', sourceLanguage, targetLanguage],
    queryFn: () => getTerminology({
      source_language: sourceLanguage,
      target_language: targetLanguage,
      page_size: 50
    }),
    enabled: isOpen && activeTab === 'browse',
    staleTime: 5 * 60 * 1000
  });

  // 保存术语库条目的mutation
  const saveTerminologyMutation = useMutation({
    mutationFn: saveTerminology,
    onSuccess: () => {
      queryClient.invalidateQueries(['terminology']);
      setNewTerm({
        source_term: '',
        target_term: '',
        domain: 'general',
        description: '',
        tags: ''
      });
      alert(t('settings.terminology.messages.saveSuccess'));
    },
    onError: (error) => {
      console.error('保存术语失败:', error);
      alert(t('settings.terminology.messages.saveFailed'));
    }
  });

  // 搜索术语库的mutation
  const searchTerminologyMutation = useMutation({
    mutationFn: searchTerminology,
    onSuccess: (data) => {
      setSearchResults(data.data?.items || []);
      setIsLoading(false);
    },
    onError: (error) => {
      console.error('搜索术语失败:', error);
      setSearchResults([]);
      setIsLoading(false);
    }
  });

  useEffect(() => {
    if (terminologyData?.data?.items) {
      setTerminologyList(terminologyData.data.items);
    }
  }, [terminologyData]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setIsLoading(true);
    searchTerminologyMutation.mutate({
      query: searchQuery.trim(),
      source_language: sourceLanguage,
      target_language: targetLanguage
    });
  };

  const handleSaveTerminology = () => {
    if (!newTerm.source_term.trim() || !newTerm.target_term.trim()) {
      alert(t('settings.terminology.messages.fillRequired'));
      return;
    }

    saveTerminologyMutation.mutate({
      ...newTerm,
      source_language: sourceLanguage,
      target_language: targetLanguage
    });
  };

  const handleUseTerm = (term) => {
    onTermSelect(term);
    onClose();
  };

  const domains = [
    'general', 'business', 'technical', 'medical', 'legal', 'academic',
    'finance', 'it', 'engineering', 'science', 'education', 'government'
  ];

  if (!isOpen) return null;

  return (
    <div className="terminology-modal-overlay" onClick={onClose}>
      <div className="terminology-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="terminology-modal-header">
          <h3>{t('settings.terminology.title')}</h3>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="terminology-tabs">
          <button
            className={`tab-button ${activeTab === 'search' ? 'active' : ''}`}
            onClick={() => setActiveTab('search')}
          >
            {t('settings.terminology.tabs.search')}
          </button>
          <button
            className={`tab-button ${activeTab === 'browse' ? 'active' : ''}`}
            onClick={() => setActiveTab('browse')}
          >
            {t('settings.terminology.tabs.browse')}
          </button>
          <button
            className={`tab-button ${activeTab === 'add' ? 'active' : ''}`}
            onClick={() => setActiveTab('add')}
          >
            {t('settings.terminology.tabs.add')}
          </button>
        </div>

        <div className="terminology-tab-content">
          {/* 搜索术语标签页 */}
          {activeTab === 'search' && (
            <div className="search-tab">
              <div className="search-input-group">
                <input
                  type="text"
                  placeholder={t('settings.terminology.search.placeholder')}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  className="search-input"
                />
                <button
                  onClick={handleSearch}
                  disabled={isLoading}
                  className="search-button"
                >
                  {isLoading ? t('settings.terminology.search.searching') : t('settings.terminology.search.button')}
                </button>
              </div>

              <div className="search-results">
                {searchResults.length > 0 ? (
                  <div className="results-list">
                    <h4>{t('settings.terminology.search.results', { count: searchResults.length })}</h4>
                    {searchResults.map((term) => (
                      <div key={term.id} className="term-card">
                        <div className="term-content">
                          <div className="term-pair">
                            <span className="source-term">{term.source_term}</span>
                            <span className="arrow">→</span>
                            <span className="target-term">{term.target_term}</span>
                          </div>
                          {term.domain && (
                            <span className="term-domain">{term.domain}</span>
                          )}
                          {term.description && (
                            <p className="term-description">{term.description}</p>
                          )}
                        </div>
                        <button
                          onClick={() => handleUseTerm(term)}
                          className="use-term-button"
                        >
                          {t('settings.terminology.search.use')}
                        </button>
                      </div>
                    ))}
                  </div>
                ) : searchQuery && !isLoading ? (
                  <div className="no-results">{t('settings.terminology.search.noResults')}</div>
                ) : null}
              </div>
            </div>
          )}

          {/* 浏览术语标签页 */}
          {activeTab === 'browse' && (
            <div className="browse-tab">
              <div className="terminology-list">
                {terminologyList.length > 0 ? (
                  terminologyList.map((term) => (
                    <div key={term.id} className="term-card">
                      <div className="term-content">
                        <div className="term-pair">
                          <span className="source-term">{term.source_term}</span>
                          <span className="arrow">→</span>
                          <span className="target-term">{term.target_term}</span>
                        </div>
                        <div className="term-meta">
                          {term.domain && (
                            <span className="term-domain">{term.domain}</span>
                          )}
                          <span className="term-usage">{t('settings.terminology.browse.usageCount', { count: term.usage_count })}</span>
                        </div>
                        {term.description && (
                          <p className="term-description">{term.description}</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleUseTerm(term)}
                        className="use-term-button"
                      >
                        {t('settings.terminology.browse.use')}
                      </button>
                    </div>
                  ))
                ) : (
                  <div className="no-terms">{t('settings.terminology.browse.noTerms')}</div>
                )}
              </div>
            </div>
          )}

          {/* 添加术语标签页 */}
          {activeTab === 'add' && (
            <div className="add-tab">
              <div className="add-term-form">
                <div className="form-group">
                  <label>{t('settings.terminology.add.sourceTerm')}</label>
                  <input
                    type="text"
                    value={newTerm.source_term}
                    onChange={(e) => setNewTerm({...newTerm, source_term: e.target.value})}
                    placeholder={t('settings.terminology.add.sourcePlaceholder')}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>{t('settings.terminology.add.targetTerm')}</label>
                  <input
                    type="text"
                    value={newTerm.target_term}
                    onChange={(e) => setNewTerm({...newTerm, target_term: e.target.value})}
                    placeholder={t('settings.terminology.add.targetPlaceholder')}
                    className="form-input"
                  />
                </div>

                <div className="form-group">
                  <label>{t('settings.terminology.add.domain')}</label>
                  <select
                    value={newTerm.domain}
                    onChange={(e) => setNewTerm({...newTerm, domain: e.target.value})}
                    className="form-select"
                  >
                    {domains.map((domain) => (
                      <option key={domain} value={domain}>{domain}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>{t('settings.terminology.add.description')}</label>
                  <textarea
                    value={newTerm.description}
                    onChange={(e) => setNewTerm({...newTerm, description: e.target.value})}
                    placeholder={t('settings.terminology.add.descriptionPlaceholder')}
                    className="form-textarea"
                    rows="3"
                  />
                </div>

                <div className="form-group">
                  <label>{t('settings.terminology.add.tags')}</label>
                  <input
                    type="text"
                    value={newTerm.tags}
                    onChange={(e) => setNewTerm({...newTerm, tags: e.target.value})}
                    placeholder={t('settings.terminology.add.tagsPlaceholder')}
                    className="form-input"
                  />
                </div>

                <div className="form-actions">
                  <button
                    onClick={handleSaveTerminology}
                    disabled={saveTerminologyMutation.isLoading}
                    className="save-button"
                  >
                    {saveTerminologyMutation.isLoading ? t('settings.terminology.add.saving') : t('settings.terminology.add.save')}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default TerminologyManagement;