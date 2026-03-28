/**
 * 工作空间选择器组件
 *
 * 提供工作空间的切换、创建、编辑、删除功能
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { FiChevronDown, FiPlus, FiEdit2, FiTrash2, FiCheck, FiDatabase } from 'react-icons/fi';
import useAuthStore from '../../stores/authStore';
import Input from '../UI/Input';
import Modal from '../UI/Modal';
import Badge from '../UI/Badge';
import {
    getWorkspaces,
    getCurrentWorkspace,
    switchWorkspace,
    createWorkspace,
    updateWorkspace,
    deleteWorkspace,
    getStorageUsage
} from '../../utils/api/workspaceApi';
import './WorkspaceSelector.css';

/**
 * 工作空间选择器组件
 *
 * @param {Object} props - 组件属性
 * @param {boolean} [props.showStorage=true] - 是否显示存储使用情况
 */
const WorkspaceSelector = ({ showStorage = true }) => {
    const [loading, setLoading] = useState(false);
    const [createModalVisible, setCreateModalVisible] = useState(false);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [editingWorkspace, setEditingWorkspace] = useState(null);
    const [storageInfo, setStorageInfo] = useState(null);
    const [formData, setFormData] = useState({ name: '', description: '' });
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef(null);

    // 从全局状态获取工作空间信息
    const {
        currentWorkspace,
        workspaces,
        setCurrentWorkspace,
        setWorkspaces
    } = useAuthStore();

    /**
     * 加载工作空间列表
     */
    const loadWorkspaces = useCallback(async () => {
        try {
            const response = await getWorkspaces();
            if (response.workspaces) {
                setWorkspaces(response.workspaces);
            }
        } catch (error) {
            // 静默处理超时和500错误，避免在控制台显示错误堆栈
            if (error.status === 408 || error.message?.includes('超时')) {
                console.log('[WorkspaceSelector] 加载工作空间超时，使用本地缓存');
            } else if (error.status >= 500) {
                console.log('[WorkspaceSelector] 加载工作空间服务器错误，使用本地缓存');
            } else {
                console.error('加载工作空间失败:', error.message || error);
            }
        }
    }, [setWorkspaces]);

    /**
     * 加载当前工作空间
     */
    const loadCurrentWorkspace = useCallback(async () => {
        try {
            const workspace = await getCurrentWorkspace();
            setCurrentWorkspace(workspace);
        } catch (error) {
            // 静默处理超时和500错误，避免在控制台显示错误堆栈
            if (error.status === 408 || error.message?.includes('超时')) {
                console.log('[WorkspaceSelector] 加载当前工作空间超时，使用本地缓存');
            } else if (error.status >= 500) {
                console.log('[WorkspaceSelector] 加载当前工作空间服务器错误，使用本地缓存');
            } else {
                console.error('加载当前工作空间失败:', error.message || error);
            }
        }
    }, [setCurrentWorkspace]);

    /**
     * 加载存储使用情况
     */
    const loadStorageInfo = useCallback(async (workspaceId) => {
        if (!showStorage || !workspaceId) return;
        try {
            const info = await getStorageUsage(workspaceId);
            setStorageInfo(info);
        } catch (error) {
            console.error('加载存储信息失败:', error);
        }
    }, [showStorage]);

    // 组件挂载时加载数据（不阻塞页面）
    useEffect(() => {
        // 延迟加载，避免阻塞页面渲染
        const timer = setTimeout(() => {
            loadWorkspaces();
            loadCurrentWorkspace();
        }, 100);
        
        return () => clearTimeout(timer);
    }, [loadWorkspaces, loadCurrentWorkspace]);

    // 当前工作空间变化时加载存储信息（延迟加载）
    useEffect(() => {
        if (currentWorkspace?.id) {
            // 延迟加载存储信息，避免阻塞页面
            const timer = setTimeout(() => {
                loadStorageInfo(currentWorkspace.id);
            }, 200);
            
            return () => clearTimeout(timer);
        }
    }, [currentWorkspace, loadStorageInfo]);

    // 点击外部关闭下拉菜单
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setDropdownOpen(false);
            }
        };

        if (dropdownOpen) {
            // 使用 click 事件而不是 mousedown，避免与工作空间项的点击事件冲突
            document.addEventListener('click', handleClickOutside);
        }

        return () => {
            document.removeEventListener('click', handleClickOutside);
        };
    }, [dropdownOpen]);

    /**
     * 处理切换工作空间
     */
    const handleSwitchWorkspace = async (workspaceId) => {
        console.log('尝试切换工作空间:', workspaceId, '当前工作空间:', currentWorkspace?.id);
        if (workspaceId === currentWorkspace?.id) {
            console.log('已经是当前工作空间，无需切换');
            setDropdownOpen(false);
            return;
        }

        setLoading(true);
        try {
            console.log('调用switchWorkspace API');
            const workspace = await switchWorkspace(workspaceId);
            console.log('切换成功:', workspace);

            // 更新状态
            setCurrentWorkspace(workspace);
            setDropdownOpen(false);

            // 延迟刷新，确保状态已持久化到localStorage
            setTimeout(() => {
                window.location.reload();
            }, 300);
        } catch (error) {
            console.error('切换工作空间失败:', error);
            alert('切换工作空间失败: ' + (error.message || '未知错误'));
        } finally {
            setLoading(false);
        }
    };

    /**
     * 处理创建工作空间
     */
    const handleCreateWorkspace = async () => {
        if (!formData.name.trim()) {
            alert('请输入工作空间名称');
            return;
        }

        setLoading(true);
        try {
            await createWorkspace(formData);
            setCreateModalVisible(false);
            setFormData({ name: '', description: '' });
            await loadWorkspaces();
        } catch (error) {
            console.error('创建工作空间失败:', error);
            alert('创建工作空间失败: ' + (error.message || '未知错误'));
        } finally {
            setLoading(false);
        }
    };

    /**
     * 处理编辑工作空间
     */
    const handleEditWorkspace = async () => {
        if (!formData.name.trim()) {
            alert('请输入工作空间名称');
            return;
        }

        setLoading(true);
        try {
            await updateWorkspace(editingWorkspace.id, formData);
            setEditModalVisible(false);
            setEditingWorkspace(null);
            setFormData({ name: '', description: '' });
            await loadWorkspaces();
            if (currentWorkspace?.id === editingWorkspace.id) {
                await loadCurrentWorkspace();
            }
        } catch (error) {
            console.error('更新工作空间失败:', error);
            alert('更新工作空间失败: ' + (error.message || '未知错误'));
        } finally {
            setLoading(false);
        }
    };

    /**
     * 处理删除工作空间
     */
    const handleDeleteWorkspace = async (workspace) => {
        if (workspace.is_default) {
            alert('不能删除默认工作空间');
            return;
        }

        if (!confirm(`确定要删除工作空间 "${workspace.name}" 吗？此操作不可恢复。`)) {
            return;
        }

        setLoading(true);
        try {
            await deleteWorkspace(workspace.id);
            await loadWorkspaces();
            if (currentWorkspace?.id === workspace.id) {
                await loadCurrentWorkspace();
            }
        } catch (error) {
            console.error('删除工作空间失败:', error);
            alert('删除工作空间失败: ' + (error.message || '未知错误'));
        } finally {
            setLoading(false);
        }
    };

    /**
     * 打开编辑弹窗
     */
    const openEditModal = (workspace) => {
        console.log('打开编辑弹窗:', workspace);
        setEditingWorkspace(workspace);
        setFormData({
            name: workspace.name,
            description: workspace.description || ''
        });
        setEditModalVisible(true);
    };

    /**
     * 打开创建弹窗
     */
    const openCreateModal = () => {
        console.log('打开创建弹窗');
        setFormData({ name: '', description: '' });
        setCreateModalVisible(true);
    };

    /**
     * 格式化存储大小
     */
    const formatStorageSize = (bytes) => {
        if (!bytes) return '0 B';
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        return `${size.toFixed(2)} ${units[unitIndex]}`;
    };

    return (
        <div className="workspace-selector" ref={dropdownRef}>
            {/* 当前工作空间显示 */}
            <div
                className="workspace-current"
                onClick={() => setDropdownOpen(!dropdownOpen)}
            >
                <div className="workspace-current-info">
                    <FiDatabase className="workspace-icon" />
                    <span className="workspace-name">
                        {currentWorkspace?.name || '加载中...'}
                    </span>
                    {currentWorkspace?.is_default && (
                        <Badge variant="default" className="workspace-default-badge">默认</Badge>
                    )}
                </div>
                <FiChevronDown className={`workspace-chevron ${dropdownOpen ? 'open' : ''}`} />
            </div>

            {/* 下拉菜单 */}
            {dropdownOpen && (
                <div className="workspace-dropdown">
                    <div className="workspace-dropdown-header">
                        <span className="workspace-dropdown-title">工作空间</span>
                        <button
                            className="workspace-action-btn"
                            onClick={(e) => {
                                e.stopPropagation();
                                openCreateModal();
                            }}
                            type="button"
                        >
                            <FiPlus className="btn-icon" />
                            <span>新建</span>
                        </button>
                    </div>
                    <div className="workspace-dropdown-list">
                        {workspaces.map(workspace => (
                            <div
                                key={workspace.id}
                                className={`workspace-dropdown-item ${workspace.id === currentWorkspace?.id ? 'active' : ''}`}
                                onClick={(e) => {
                                    console.log('点击工作空间项:', workspace.id, workspace.name);
                                    handleSwitchWorkspace(workspace.id);
                                }}
                            >
                                <div className="workspace-item-info">
                                    <div className="workspace-item-name">
                                        {workspace.name}
                                        {workspace.is_default && (
                                            <Badge variant="default" className="workspace-default-badge">默认</Badge>
                                        )}
                                    </div>
                                    {workspace.description && (
                                        <div className="workspace-item-desc">{workspace.description}</div>
                                    )}
                                </div>
                                <div className="workspace-item-actions">
                                    {workspace.id === currentWorkspace?.id && (
                                        <FiCheck className="workspace-check-icon" />
                                    )}
                                    <button
                                        className="workspace-action-btn"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            openEditModal(workspace);
                                        }}
                                        type="button"
                                        title="编辑"
                                    >
                                        <FiEdit2 className="btn-icon" />
                                    </button>
                                    {!workspace.is_default && (
                                        <button
                                            className="workspace-action-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleDeleteWorkspace(workspace);
                                            }}
                                            type="button"
                                            title="删除"
                                        >
                                            <FiTrash2 className="btn-icon" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* 存储使用情况 */}
            {showStorage && storageInfo && (
                <div className="workspace-storage-info">
                    <div className="storage-info-header">
                        <FiDatabase className="storage-icon" />
                        <span className="storage-text">
                            {formatStorageSize(storageInfo.used_storage_bytes)} / {formatStorageSize(storageInfo.max_storage_bytes)}
                        </span>
                    </div>
                    <div className="storage-progress-bar">
                        <div
                            className="storage-progress-fill"
                            style={{ width: `${Math.min(storageInfo.usage_percentage || 0, 100)}%` }}
                        />
                    </div>
                </div>
            )}

            {/* 创建弹窗 */}
            {createModalVisible && (
                <div className="workspace-modal-overlay" onClick={() => setCreateModalVisible(false)}>
                    <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="workspace-modal-header">
                            <h3>创建工作空间</h3>
                            <button
                                className="workspace-modal-close"
                                onClick={() => setCreateModalVisible(false)}
                                type="button"
                            >
                                ×
                            </button>
                        </div>
                        <div className="workspace-modal-content">
                            <div className="form-field">
                                <label>工作空间名称 *</label>
                                <Input
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="请输入工作空间名称"
                                    maxLength={100}
                                />
                            </div>
                            <div className="form-field">
                                <label>描述</label>
                                <Input
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="请输入工作空间描述（可选）"
                                    maxLength={500}
                                />
                            </div>
                            <div className="form-actions">
                                <button
                                    className="workspace-form-btn secondary"
                                    onClick={() => setCreateModalVisible(false)}
                                    type="button"
                                >
                                    取消
                                </button>
                                <button
                                    className="workspace-form-btn primary"
                                    onClick={handleCreateWorkspace}
                                    disabled={loading || !formData.name.trim()}
                                    type="button"
                                >
                                    {loading ? '创建中...' : '创建'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* 编辑弹窗 */}
            {editModalVisible && (
                <div className="workspace-modal-overlay" onClick={() => setEditModalVisible(false)}>
                    <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="workspace-modal-header">
                            <h3>编辑工作空间</h3>
                            <button
                                className="workspace-modal-close"
                                onClick={() => setEditModalVisible(false)}
                                type="button"
                            >
                                ×
                            </button>
                        </div>
                        <div className="workspace-modal-content">
                            <div className="form-field">
                                <label>工作空间名称 *</label>
                                <Input
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="请输入工作空间名称"
                                    maxLength={100}
                                />
                            </div>
                            <div className="form-field">
                                <label>描述</label>
                                <Input
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="请输入工作空间描述（可选）"
                                    maxLength={500}
                                />
                            </div>
                            <div className="form-actions">
                                <button
                                    className="workspace-form-btn secondary"
                                    onClick={() => setEditModalVisible(false)}
                                    type="button"
                                >
                                    取消
                                </button>
                                <button
                                    className="workspace-form-btn primary"
                                    onClick={handleEditWorkspace}
                                    disabled={loading || !formData.name.trim()}
                                    type="button"
                                >
                                    {loading ? '保存中...' : '保存'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default WorkspaceSelector;
