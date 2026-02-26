/**
 * 工作空间选择器组件
 *
 * 提供工作空间的切换、创建、编辑、删除功能
 * 支持下拉选择和弹窗管理两种模式
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    Dropdown,
    Menu,
    Modal,
    Form,
    Input,
    Button,
    Space,
    Typography,
    Tooltip,
    Progress,
    message,
    Popconfirm,
    List,
    Badge
} from 'antd';
import {
    DownOutlined,
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    CheckOutlined,
    SettingOutlined,
    DatabaseOutlined
} from '@ant-design/icons';
import useAuthStore from '../../stores/authStore';
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

const { Text, Title } = Typography;

/**
 * 工作空间选择器组件
 *
 * @param {Object} props - 组件属性
 * @param {boolean} [props.showStorage=true] - 是否显示存储使用情况
 * @param {string} [props.mode='dropdown'] - 显示模式：'dropdown' | 'modal'
 */
const WorkspaceSelector = ({ showStorage = true, mode = 'dropdown' }) => {
    const [loading, setLoading] = useState(false);
    const [modalVisible, setModalVisible] = useState(false);
    const [createModalVisible, setCreateModalVisible] = useState(false);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [editingWorkspace, setEditingWorkspace] = useState(null);
    const [storageInfo, setStorageInfo] = useState(null);
    const [form] = Form.useForm();
    const [editForm] = Form.useForm();

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
            message.error('加载工作空间失败');
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
    const loadStorageUsage = useCallback(async () => {
        if (!currentWorkspace?.id || !showStorage) return;

        try {
            const usage = await getStorageUsage(currentWorkspace.id);
            setStorageInfo(usage);
        } catch (error) {
            console.error('加载存储使用情况失败:', error);
        }
    }, [currentWorkspace, showStorage]);

    // 组件挂载时加载数据
    useEffect(() => {
        loadWorkspaces();
        loadCurrentWorkspace();
    }, [loadWorkspaces, loadCurrentWorkspace]);

    // 当前工作空间变化时加载存储信息
    useEffect(() => {
        loadStorageUsage();
    }, [loadStorageUsage]);

    /**
     * 处理工作空间切换
     *
     * @param {number} workspaceId - 目标工作空间ID
     */
    const handleSwitchWorkspace = async (workspaceId) => {
        if (workspaceId === currentWorkspace?.id) return;

        setLoading(true);
        try {
            const workspace = await switchWorkspace(workspaceId);
            setCurrentWorkspace(workspace);
            message.success(`已切换到工作空间: ${workspace.name}`);
            // 刷新页面以应用新的工作空间上下文
            window.location.reload();
        } catch (error) {
            console.error('切换工作空间失败:', error);
            message.error('切换工作空间失败');
        } finally {
            setLoading(false);
        }
    };

    /**
     * 处理创建工作空间
     *
     * @param {Object} values - 表单数据
     */
    const handleCreateWorkspace = async (values) => {
        setLoading(true);
        try {
            const workspace = await createWorkspace(values);
            setWorkspaces([...workspaces, workspace]);
            setCreateModalVisible(false);
            form.resetFields();
            message.success('工作空间创建成功');
        } catch (error) {
            console.error('创建工作空间失败:', error);
            message.error(error.response?.data?.detail || '创建工作空间失败');
        } finally {
            setLoading(false);
        }
    };

    /**
     * 处理编辑工作空间
     *
     * @param {Object} values - 表单数据
     */
    const handleEditWorkspace = async (values) => {
        if (!editingWorkspace) return;

        setLoading(true);
        try {
            const workspace = await updateWorkspace(editingWorkspace.id, values);
            setWorkspaces(workspaces.map(w =>
                w.id === workspace.id ? workspace : w
            ));
            if (currentWorkspace?.id === workspace.id) {
                setCurrentWorkspace(workspace);
            }
            setEditModalVisible(false);
            setEditingWorkspace(null);
            editForm.resetFields();
            message.success('工作空间更新成功');
        } catch (error) {
            console.error('更新工作空间失败:', error);
            message.error(error.response?.data?.detail || '更新工作空间失败');
        } finally {
            setLoading(false);
        }
    };

    /**
     * 处理删除工作空间
     *
     * @param {number} workspaceId - 工作空间ID
     */
    const handleDeleteWorkspace = async (workspaceId) => {
        setLoading(true);
        try {
            await deleteWorkspace(workspaceId);
            setWorkspaces(workspaces.filter(w => w.id !== workspaceId));
            message.success('工作空间删除成功');
        } catch (error) {
            console.error('删除工作空间失败:', error);
            message.error(error.response?.data?.detail || '删除工作空间失败');
        } finally {
            setLoading(false);
        }
    };

    /**
     * 打开编辑弹窗
     *
     * @param {Object} workspace - 工作空间对象
     */
    const openEditModal = (workspace) => {
        setEditingWorkspace(workspace);
        editForm.setFieldsValue({
            name: workspace.name,
            description: workspace.description || ''
        });
        setEditModalVisible(true);
    };

    /**
     * 渲染工作空间下拉菜单
     */
    const renderWorkspaceMenu = () => (
        <Menu className="workspace-menu">
            <Menu.ItemGroup title="我的工作空间">
                {workspaces.map(workspace => (
                    <Menu.Item
                        key={workspace.id}
                        onClick={() => handleSwitchWorkspace(workspace.id)}
                        className={workspace.id === currentWorkspace?.id ? 'active' : ''}
                    >
                        <Space>
                            {workspace.id === currentWorkspace?.id && (
                                <CheckOutlined style={{ color: '#52c41a' }} />
                            )}
                            <span>{workspace.name}</span>
                            {workspace.is_default && (
                                <Badge count="默认" style={{ backgroundColor: '#1890ff' }} />
                            )}
                        </Space>
                    </Menu.Item>
                ))}
            </Menu.ItemGroup>
            <Menu.Divider />
            <Menu.Item
                key="create"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
            >
                新建工作空间
            </Menu.Item>
            <Menu.Item
                key="manage"
                icon={<SettingOutlined />}
                onClick={() => setModalVisible(true)}
            >
                管理工作空间
            </Menu.Item>
        </Menu>
    );

    /**
     * 渲染存储使用进度条
     */
    const renderStorageProgress = () => {
        if (!storageInfo || !showStorage) return null;

        const percent = storageInfo.usage_percentage || 0;
        const status = percent > 90 ? 'exception' : percent > 70 ? 'warning' : 'normal';

        return (
            <div className="workspace-storage">
                <Tooltip title={`已用 ${storageInfo.used_storage_bytes} / 总计 ${storageInfo.max_storage_bytes} 字节`}>
                    <Progress
                        percent={Math.round(percent)}
                        size="small"
                        status={status}
                        showInfo={false}
                        strokeWidth={4}
                    />
                </Tooltip>
            </div>
        );
    };

    return (
        <div className="workspace-selector">
            {mode === 'dropdown' ? (
                <Dropdown
                    overlay={renderWorkspaceMenu()}
                    trigger={['click']}
                    placement="bottomLeft"
                >
                    <Button loading={loading} className="workspace-dropdown-btn">
                        <Space>
                            <DatabaseOutlined />
                            <span className="workspace-name">
                                {currentWorkspace?.name || '选择工作空间'}
                            </span>
                            <DownOutlined />
                        </Space>
                    </Button>
                </Dropdown>
            ) : null}

            {renderStorageProgress()}

            {/* 管理工作空间弹窗 */}
            <Modal
                title="管理工作空间"
                visible={modalVisible}
                onCancel={() => setModalVisible(false)}
                footer={null}
                width={600}
            >
                <List
                    dataSource={workspaces}
                    renderItem={workspace => (
                        <List.Item
                            actions={[
                                <Button
                                    type="text"
                                    icon={<EditOutlined />}
                                    onClick={() => openEditModal(workspace)}
                                />,
                                !workspace.is_default && (
                                    <Popconfirm
                                        title="确定要删除此工作空间吗？"
                                        description="删除后工作空间内的数据将无法恢复"
                                        onConfirm={() => handleDeleteWorkspace(workspace.id)}
                                        okText="删除"
                                        cancelText="取消"
                                        okButtonProps={{ danger: true }}
                                    >
                                        <Button
                                            type="text"
                                            danger
                                            icon={<DeleteOutlined />}
                                        />
                                    </Popconfirm>
                                )
                            ]}
                        >
                            <List.Item.Meta
                                title={
                                    <Space>
                                        <span>{workspace.name}</span>
                                        {workspace.is_default && (
                                            <Badge count="默认" style={{ backgroundColor: '#1890ff' }} />
                                        )}
                                        {workspace.id === currentWorkspace?.id && (
                                            <Badge count="当前" style={{ backgroundColor: '#52c41a' }} />
                                        )}
                                    </Space>
                                }
                                description={workspace.description || '暂无描述'}
                            />
                        </List.Item>
                    )}
                />
                <Button
                    type="dashed"
                    block
                    icon={<PlusOutlined />}
                    onClick={() => {
                        setModalVisible(false);
                        setCreateModalVisible(true);
                    }}
                    style={{ marginTop: 16 }}
                >
                    新建工作空间
                </Button>
            </Modal>

            {/* 创建工作空间弹窗 */}
            <Modal
                title="新建工作空间"
                visible={createModalVisible}
                onCancel={() => setCreateModalVisible(false)}
                footer={null}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleCreateWorkspace}
                >
                    <Form.Item
                        name="name"
                        label="工作空间名称"
                        rules={[
                            { required: true, message: '请输入工作空间名称' },
                            { max: 100, message: '名称不能超过100个字符' }
                        ]}
                    >
                        <Input placeholder="例如：项目A、个人笔记" />
                    </Form.Item>

                    <Form.Item
                        name="description"
                        label="描述"
                        rules={[{ max: 500, message: '描述不能超过500个字符' }]}
                    >
                        <Input.TextArea
                            rows={3}
                            placeholder="工作空间的描述（可选）"
                        />
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setCreateModalVisible(false)}>
                                取消
                            </Button>
                            <Button type="primary" htmlType="submit" loading={loading}>
                                创建
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>

            {/* 编辑工作空间弹窗 */}
            <Modal
                title="编辑工作空间"
                visible={editModalVisible}
                onCancel={() => {
                    setEditModalVisible(false);
                    setEditingWorkspace(null);
                }}
                footer={null}
            >
                <Form
                    form={editForm}
                    layout="vertical"
                    onFinish={handleEditWorkspace}
                >
                    <Form.Item
                        name="name"
                        label="工作空间名称"
                        rules={[
                            { required: true, message: '请输入工作空间名称' },
                            { max: 100, message: '名称不能超过100个字符' }
                        ]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        name="description"
                        label="描述"
                        rules={[{ max: 500, message: '描述不能超过500个字符' }]}
                    >
                        <Input.TextArea rows={3} />
                    </Form.Item>

                    <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => {
                                setEditModalVisible(false);
                                setEditingWorkspace(null);
                            }}>
                                取消
                            </Button>
                            <Button type="primary" htmlType="submit" loading={loading}>
                                保存
                            </Button>
                        </Space>
                    </Form.Item>
                </Form>
            </Modal>
        </div>
    );
};

export default WorkspaceSelector;