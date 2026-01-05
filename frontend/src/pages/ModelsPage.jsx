import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Button,
  Card,
  Input,
  Select,
  Table,
  Modal,
  Badge,
  Icon,
  showSuccess,
  showError,
  ToastContainer,
} from '../components/UI';
import { 
  useModels, 
  useCreateModel, 
  useUpdateModel, 
  useDeleteModel,
  useSuppliers,
} from '../hooks/useApi';
import useApiStore from '../stores/apiStore';

const ModelsPage = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    supplier_id: '',
    version: '',
    parameters: {},
  });

  // API Store
  const {
    loading,
    errors,
    selectedItems,
    modals,
    tableStates,
    setLoading,
    setError,
    openModal,
    closeModal,
    setSelectedItem,
    clearSelectedItem,
    setTableState,
    setFormState,
  } = useApiStore();

  // API Hooks
  const { data: models = [], isLoading, refetch } = useModels({
    search: searchTerm,
    category: selectedCategory,
  });

  const { data: suppliers = [] } = useSuppliers();

  const createModelMutation = useCreateModel();
  const updateModelMutation = useUpdateModel();
  const deleteModelMutation = useDeleteModel();

  // Category options
  const categoryOptions = [
    { value: '', label: '所有类别' },
    { value: 'llm', label: '语言模型' },
    { value: 'image', label: '图像模型' },
    { value: 'audio', label: '音频模型' },
    { value: 'video', label: '视频模型' },
  ];

  // Table columns
  const columns = [
    {
      key: 'name',
      title: '模型名称',
      sortable: true,
      render: (value, row) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
            <Icon name="model" size={16} color="white" />
          </div>
          <div>
            <div className="font-medium text-gray-900">{value}</div>
            <div className="text-sm text-gray-500">{row.description}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'category',
      title: '类别',
      sortable: true,
      render: (value) => {
        const category = categoryOptions.find(opt => opt.value === value);
        return (
          <Badge variant="primary" size="small">
            {category?.label || value}
          </Badge>
        );
      },
    },
    {
      key: 'supplier',
      title: '供应商',
      sortable: true,
      render: (value) => value || '未知',
    },
    {
      key: 'version',
      title: '版本',
      sortable: true,
      render: (value) => (
        <Badge variant="default" size="small">
          {value}
        </Badge>
      ),
    },
    {
      key: 'status',
      title: '状态',
      sortable: true,
      render: (value) => (
        <Badge 
          variant={value === 'active' ? 'success' : 'default'} 
          size="small"
        >
          {value === 'active' ? '活跃' : '非活跃'}
        </Badge>
      ),
    },
    {
      key: 'created_at',
      title: '创建时间',
      sortable: true,
      render: (value) => new Date(value).toLocaleDateString('zh-CN'),
    },
    {
      key: 'actions',
      title: '操作',
      render: (_, row) => (
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="small"
            onClick={() => handleView(row)}
          >
            <Icon name="eye" size={14} />
          </Button>
          <Button
            variant="ghost"
            size="small"
            onClick={() => handleEdit(row)}
          >
            <Icon name="edit" size={14} />
          </Button>
          <Button
            variant="ghost"
            size="small"
            onClick={() => handleDelete(row.id)}
          >
            <Icon name="delete" size={14} />
          </Button>
        </div>
      ),
    },
  ];

  // Handlers
  const handleCreate = () => {
    setFormData({
      name: '',
      description: '',
      category: '',
      supplier_id: '',
      version: '',
      parameters: {},
    });
    openModal('createModel');
    setIsCreateModalOpen(true);
  };

  const handleEdit = (model) => {
    setSelectedModel(model);
    setFormData({
      name: model.name,
      description: model.description,
      category: model.category,
      supplier_id: model.supplier_id,
      version: model.version,
      parameters: model.parameters || {},
    });
    setSelectedItem('model', model);
    openModal('editModel');
    setIsEditModalOpen(true);
  };

  const handleView = (model) => {
    setSelectedModel(model);
    setSelectedItem('model', model);
    // Navigate to detail view or open modal
    console.log('View model:', model);
  };

  const handleDelete = async (id) => {
    if (window.confirm('确定要删除这个模型吗？')) {
      try {
        await deleteModelMutation.mutateAsync(id);
        refetch();
      } catch (error) {
        console.error('Delete failed:', error);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      if (selectedModel) {
        await updateModelMutation.mutateAsync({
          id: selectedModel.id,
          ...formData,
        });
        closeModal('editModel');
        setIsEditModalOpen(false);
      } else {
        await createModelMutation.mutateAsync(formData);
        closeModal('createModel');
        setIsCreateModalOpen(false);
      }
      refetch();
    } catch (error) {
      console.error('Submit failed:', error);
    }
  };

  const handleSort = (columnKey, sortOrder) => {
    setTableState('models', { sortBy: columnKey, sortOrder });
  };

  const handleSelectionChange = (selectedRows) => {
    setTableState('models', { selectedRows });
  };

  const handlePageChange = (page) => {
    setTableState('models', { 
      pagination: { ...tableStates.models.pagination, current: page } 
    });
  };

  return (
    <div className="space-y-6">
      <ToastContainer />
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">模型管理</h1>
          <p className="text-gray-600 mt-1">管理和配置AI模型</p>
        </div>
        <Button onClick={handleCreate}>
          <Icon name="plus" size={16} />
          创建模型
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[300px]">
            <Input
              placeholder="搜索模型..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              icon={<Icon name="search" size={16} />}
            />
          </div>
          <div className="w-48">
            <Select
              options={categoryOptions}
              value={selectedCategory}
              onChange={setSelectedCategory}
              placeholder="选择类别"
            />
          </div>
          <Button variant="outline" onClick={() => refetch()}>
            <Icon name="refresh" size={16} />
            刷新
          </Button>
        </div>
      </Card>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          data={models}
          loading={isLoading}
          pagination={true}
          pageSize={10}
          onPageChange={handlePageChange}
          selection={true}
          selectedRows={tableStates.models.selectedRows}
          onSelectionChange={handleSelectionChange}
          sortBy={tableStates.models.sortBy}
          sortOrder={tableStates.models.sortOrder}
          onSort={handleSort}
          rowKey="id"
          emptyText="暂无模型数据"
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={isCreateModalOpen || isEditModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setIsEditModalOpen(false);
          clearSelectedItem('model');
        }}
        title={selectedModel ? '编辑模型' : '创建模型'}
        size="large"
        footer={
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setIsCreateModalOpen(false);
                setIsEditModalOpen(false);
                clearSelectedItem('model');
              }}
            >
              取消
            </Button>
            <Button
              onClick={handleSubmit}
              loading={createModelMutation.isPending || updateModelMutation.isPending}
            >
              {selectedModel ? '更新' : '创建'}
            </Button>
          </div>
        }
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="模型名称"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
            <Input
              label="版本"
              value={formData.version}
              onChange={(e) => setFormData({ ...formData, version: e.target.value })}
              required
            />
          </div>
          
          <Input
            label="描述"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            multiline
            rows={3}
          />
          
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="类别"
              options={categoryOptions.filter(opt => opt.value)}
              value={formData.category}
              onChange={(value) => setFormData({ ...formData, category: value })}
              required
            />
            <Select
              label="供应商"
              options={suppliers.map(supplier => ({
                value: supplier.id,
                label: supplier.name,
              }))}
              value={formData.supplier_id}
              onChange={(value) => setFormData({ ...formData, supplier_id: value })}
            />
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default ModelsPage;