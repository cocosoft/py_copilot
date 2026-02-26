/**
 * 工作空间选择器组件
 *
 * 提供工作空间的切换、创建、编辑、删除功能
 */

import React, { useState, useEffect, useCallback } from 'react';
import { FiChevronDown, FiPlus, FiEdit2, FiTrash2, FiCheck, FiSettings, FiDatabase } from 'react-icons/fi';
import useAuthStore from '../../stores/authStore';
import Button from '../UI/Button';
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
    const [modalVisible, setModalVisible] = useState(false);
    const [createModalVisible, setCreateModalVisible] = useState(false);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [editingWorkspace, setEditingWorkspace] = useState(null);
    const [storageInfo, setStorageInfo] = useState(null);
    const [formData, setFormData] = useState({ name: '', description: '' });
    const [dropdownOpen, setDropdownOpen] = useState(false);

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
            console.error('加载工作空间失败:', error);
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
            console.error('加载当前工作空间失败:', error);
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

    // 组件挂载时加载数据
    useEffect(() => {
        loadWorkspaces();
        loadCurrentWorkspace();
    }, [loadWorkspaces, loadCurrentWorkspace]);

    // 当前工作空间变化时加载存储信息
    useEffect(() => {
        if (currentWorkspace?.id) {
            loadStorageInfo(currentWorkspace.id);
        }
    }, [currentWorkspace, loadStorageInfo]);

    /**
     * 处理切换工作空间
     */
    const handleSwitchWorkspace = async (workspaceId) => {
        if (workspaceId === currentWorkspace?.id) {
            setDropdownOpen(false);
            return;
        }

        setLoading(true);
        try {
            const workspace = await switchWorkspace(workspaceId);
            setCurrentWorkspace(workspace);
            setDropdownOpen(false);
            // 刷新页面以加载新工作空间的数据
            window.location.reload();
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

    /**
     * 渲染下拉菜单
     */
    const renderDropdown = () => {
        if (!dropdownOpen) return null;

        return (
            <div className="workspace-dropdown">
                <div className="workspace-dropdown-header">
                    <span className="workspace-dropdown-title">工作空间</span>
                    <Button
                        variant="ghost"
                        size="small"
                        icon={<FiPlus />}
                        onClick={openCreateModal}
                    >
                        新建
                    </Button>
                </div>
                <div className="workspace-dropdown-list">
                    {workspaces.map(workspace => (
                        <div
                            key={workspace.id}
                            className={`workspace-dropdown-item ${workspace.id === currentWorkspace?.id ? 'active' : ''}`}
                            onClick={() => handleSwitchWorkspace(workspace.id)}
                        >
                            <div className="workspace-item-info">
                                <div className="workspace-item-name">
                                    {workspace.name}
                                    {workspace.is_default && (
                                        <Badge variant="secondary" className="workspace-default-badge">默认</Badge>
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
                                <Button
                                    variant="ghost"
                                    size="small"
                                    icon={<FiEdit2 />}
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        openEditModal(workspace);
                                    }}
                                />
                                {!workspace.is_default && (
                                    <Button
                                        variant="ghost"
                                        size="small"
                                        icon={<FiTrash2 />}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            handleDeleteWorkspace(workspace);
                                        }}
                                    />
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    };

    /**
     * 渲染存储使用情况
     */
    const renderStorageInfo = () => {
        if (!showStorage || !storageInfo) return null;

        const usagePercent = storageInfo.usage_percentage || 0;

        return (
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
                        style={{ width: `${Math.min(usagePercent, 100)}%` }}
                    />
                </div>
            </div>
        );
    };

    return (
        <div className="workspace-selector">
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
                        <Badge variant="secondary" className="workspace-default-badge">默认</Badge>
                    )}
                </div>
                <FiChevronDown className={`workspace-chevron ${dropdownOpen ? 'open' : ''}`} />
            </div>

            {/* 下拉菜单 */}
            {renderDropdown()}

            {/* 存储使用情况 */}
            {renderStorageInfo()}

            {/* 创建弹窗 */}
            <Modal
                isOpen={createModalVisible}
                onClose={() => setCreateModalVisible(false)}
                title="创建工作空间"
            >
                <div className="workspace-form">
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
                        <Button variant="secondary" onClick={() => setCreateModalVisible(false)}>
                            取消
                        </Button>
                        <Button
                            variant="primary"
                            onClick={handleCreateWorkspace}
                            loading={loading}
                            disabled={!formData.name.trim()}
                        >
                            创建
                        </Button>
                    </div>
                </div>
            </Modal>

            {/* 编辑弹窗 */}
            <Modal
                isOpen={editModalVisible}
                onClose={() => setEditModalVisible(false)}
                title="编辑工作空间"
            >
                <div className="workspace-form">
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
                        <Button variant="secondary" onClick={() => setEditModalVisible(false)}>
                            取消
                        </Button>
                        <Button
                            variant="primary"
                            onClick={handleEditWorkspace}
                            loading={loading}
                            disabled={!formData.name.trim()}
                        >
                            保存
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default WorkspaceSelector;
