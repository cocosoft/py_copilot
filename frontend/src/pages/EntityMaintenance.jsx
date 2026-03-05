import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  Snackbar,
  Tabs,
  Tab,
  Tooltip,
  Checkbox,
  Toolbar,
  AppBar,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  MergeType as MergeIcon,
  Feedback as FeedbackIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import {
  getDocumentEntities,
  getKBEntities,
  getGlobalEntities,
  getEntityDetail,
  updateDocumentEntity,
  updateKBEntity,
  deleteDocumentEntity,
  batchDeleteEntities,
  addDocumentEntity,
  submitEntityFeedback,
  getEntityStatistics,
  ENTITY_TYPES,
} from '../services/entityMaintenanceApi';

// 标签页组件
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`entity-tabpanel-${index}`}
      aria-labelledby={`entity-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

// 实体列表组件
function EntityList({
  level,
  entities,
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  onEdit,
  onDelete,
  onSelect,
  selectedIds,
  loading,
}) {
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      onSelect(entities.map((e) => e.id));
    } else {
      onSelect([]);
    }
  };

  const handleSelectOne = (id) => {
    if (selectedIds.includes(id)) {
      onSelect(selectedIds.filter((sid) => sid !== id));
    } else {
      onSelect([...selectedIds, id]);
    }
  };

  const getEntityDisplayName = (entity) => {
    if (level === 'document') return entity.text;
    if (level === 'kb') return entity.canonical_name;
    if (level === 'global') return entity.global_name;
    return '';
  };

  return (
    <Paper>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedIds.length > 0 && selectedIds.length < entities.length}
                  checked={entities.length > 0 && selectedIds.length === entities.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>ID</TableCell>
              <TableCell>实体名称</TableCell>
              <TableCell>类型</TableCell>
              {level === 'document' && (
                <>
                  <TableCell>置信度</TableCell>
                  <TableCell>位置</TableCell>
                </>
              )}
              {level === 'kb' && (
                <>
                  <TableCell>别名</TableCell>
                  <TableCell>文档数</TableCell>
                </>
              )}
              {level === 'global' && (
                <>
                  <TableCell>知识库数</TableCell>
                  <TableCell>文档数</TableCell>
                </>
              )}
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entities.map((entity) => (
              <TableRow key={entity.id} hover>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedIds.includes(entity.id)}
                    onChange={() => handleSelectOne(entity.id)}
                  />
                </TableCell>
                <TableCell>{entity.id}</TableCell>
                <TableCell>{getEntityDisplayName(entity)}</TableCell>
                <TableCell>
                  <Chip
                    label={ENTITY_TYPES.find((t) => t.value === entity.type)?.label || entity.type}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </TableCell>
                {level === 'document' && (
                  <>
                    <TableCell>{(entity.confidence * 100).toFixed(1)}%</TableCell>
                    <TableCell>{entity.start_pos}-{entity.end_pos}</TableCell>
                  </>
                )}
                {level === 'kb' && (
                  <>
                    <TableCell>{entity.aliases?.join(', ') || '-'}</TableCell>
                    <TableCell>{entity.document_count}</TableCell>
                  </>
                )}
                {level === 'global' && (
                  <>
                    <TableCell>{entity.kb_count}</TableCell>
                    <TableCell>{entity.document_count}</TableCell>
                  </>
                )}
                <TableCell>
                  <Tooltip title="编辑">
                    <IconButton size="small" onClick={() => onEdit(entity)}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="删除">
                    <IconButton size="small" onClick={() => onDelete(entity.id)} color="error">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={total}
        page={page - 1}
        onPageChange={(e, newPage) => onPageChange(newPage + 1)}
        rowsPerPage={pageSize}
        onRowsPerPageChange={(e) => onPageSizeChange(parseInt(e.target.value, 10))}
        rowsPerPageOptions={[10, 25, 50, 100]}
        labelRowsPerPage="每页数量"
        labelDisplayedRows={({ from, to, count }) => `${from}-${to} / ${count}`}
      />
    </Paper>
  );
}

// 编辑对话框
function EditDialog({ open, onClose, entity, level, onSave }) {
  const [formData, setFormData] = useState({
    entity_text: '',
    entity_type: '',
    aliases: '',
  });

  useEffect(() => {
    if (entity) {
      setFormData({
        entity_text: entity.text || entity.canonical_name || entity.global_name || '',
        entity_type: entity.type || '',
        aliases: entity.aliases?.join(', ') || '',
      });
    }
  }, [entity]);

  const handleSubmit = () => {
    const data = {
      entity_text: formData.entity_text,
      entity_type: formData.entity_type,
    };
    if (level === 'kb' && formData.aliases) {
      data.aliases = formData.aliases.split(',').map((a) => a.trim()).filter(Boolean);
    }
    onSave(entity.id, data);
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>编辑实体</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            label="实体名称"
            value={formData.entity_text}
            onChange={(e) => setFormData({ ...formData, entity_text: e.target.value })}
            fullWidth
          />
          <FormControl fullWidth>
            <InputLabel>实体类型</InputLabel>
            <Select
              value={formData.entity_type}
              onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
              label="实体类型"
            >
              {ENTITY_TYPES.filter((t) => t.value).map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          {level === 'kb' && (
            <TextField
              label="别名（用逗号分隔）"
              value={formData.aliases}
              onChange={(e) => setFormData({ ...formData, aliases: e.target.value })}
              fullWidth
              multiline
              rows={2}
            />
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained">
          保存
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// 添加实体对话框
function AddDialog({ open, onClose, documentId, onSave }) {
  const [formData, setFormData] = useState({
    entity_text: '',
    entity_type: '',
    start_pos: 0,
    end_pos: 0,
  });

  const handleSubmit = () => {
    onSave({
      ...formData,
      document_id: documentId,
      confidence: 1.0,
    });
    setFormData({ entity_text: '', entity_type: '', start_pos: 0, end_pos: 0 });
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>添加实体</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <TextField
            label="实体名称"
            value={formData.entity_text}
            onChange={(e) => setFormData({ ...formData, entity_text: e.target.value })}
            fullWidth
            required
          />
          <FormControl fullWidth>
            <InputLabel>实体类型</InputLabel>
            <Select
              value={formData.entity_type}
              onChange={(e) => setFormData({ ...formData, entity_type: e.target.value })}
              label="实体类型"
              required
            >
              {ENTITY_TYPES.filter((t) => t.value).map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  {type.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="起始位置"
              type="number"
              value={formData.start_pos}
              onChange={(e) => setFormData({ ...formData, start_pos: parseInt(e.target.value) || 0 })}
              fullWidth
            />
            <TextField
              label="结束位置"
              type="number"
              value={formData.end_pos}
              onChange={(e) => setFormData({ ...formData, end_pos: parseInt(e.target.value) || 0 })}
              fullWidth
            />
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained">
          添加
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// 反馈对话框
function FeedbackDialog({ open, onClose, entity, level }) {
  const [formData, setFormData] = useState({
    issue_type: 'wrong_type',
    suggestion: '',
  });

  const handleSubmit = async () => {
    try {
      await submitEntityFeedback({
        entity_id: entity?.id,
        level,
        issue_type: formData.issue_type,
        suggestion: formData.suggestion,
      });
      onClose();
    } catch (error) {
      console.error('提交反馈失败:', error);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>实体反馈</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          <FormControl fullWidth>
            <InputLabel>问题类型</InputLabel>
            <Select
              value={formData.issue_type}
              onChange={(e) => setFormData({ ...formData, issue_type: e.target.value })}
              label="问题类型"
            >
              <MenuItem value="wrong_type">类型错误</MenuItem>
              <MenuItem value="wrong_text">名称错误</MenuItem>
              <MenuItem value="should_merge">应该合并</MenuItem>
              <MenuItem value="should_delete">应该删除</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="详细建议"
            value={formData.suggestion}
            onChange={(e) => setFormData({ ...formData, suggestion: e.target.value })}
            fullWidth
            multiline
            rows={3}
            placeholder="请描述问题或提供建议..."
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button onClick={handleSubmit} variant="contained">
          提交反馈
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// 主组件
export default function EntityMaintenance({ knowledgeBaseId: propKnowledgeBaseId, documentId: propDocumentId, embedded = false }) {
  const [activeTab, setActiveTab] = useState(0);
  const [entities, setEntities] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [entityType, setEntityType] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [currentEntity, setCurrentEntity] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [stats, setStats] = useState(null);

  // 使用传入的props或默认值
  const knowledgeBaseId = propKnowledgeBaseId || 1;
  const documentId = propDocumentId || 1;

  const showMessage = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const loadEntities = useCallback(async () => {
    setLoading(true);
    try {
      let response;
      const params = { page, pageSize, entityType };

      switch (activeTab) {
        case 0:
          response = await getDocumentEntities(documentId, params);
          break;
        case 1:
          response = await getKBEntities(knowledgeBaseId, params);
          break;
        case 2:
          response = await getGlobalEntities(params);
          break;
        default:
          return;
      }

      setEntities(response.entities || []);
      setTotal(response.total || 0);
    } catch (error) {
      console.error('加载实体失败:', error);
      showMessage('加载实体失败', 'error');
    } finally {
      setLoading(false);
    }
  }, [activeTab, page, pageSize, entityType, knowledgeBaseId, documentId]);

  const loadStats = useCallback(async () => {
    try {
      const response = await getEntityStatistics(knowledgeBaseId);
      setStats(response);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  }, [knowledgeBaseId]);

  useEffect(() => {
    loadEntities();
  }, [loadEntities]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setPage(1);
    setSelectedIds([]);
  };

  const handleEdit = (entity) => {
    setCurrentEntity(entity);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async (entityId, data) => {
    try {
      if (activeTab === 0) {
        await updateDocumentEntity(entityId, data);
      } else if (activeTab === 1) {
        await updateKBEntity(entityId, data);
      }
      showMessage('更新成功', 'success');
      loadEntities();
    } catch (error) {
      console.error('更新失败:', error);
      showMessage('更新失败', 'error');
    }
  };

  const handleDelete = async (entityId) => {
    if (!window.confirm('确定要删除这个实体吗？')) return;

    try {
      await deleteDocumentEntity(entityId);
      showMessage('删除成功', 'success');
      loadEntities();
    } catch (error) {
      console.error('删除失败:', error);
      showMessage('删除失败', 'error');
    }
  };

  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) {
      showMessage('请先选择要删除的实体', 'warning');
      return;
    }
    if (!window.confirm(`确定要删除选中的 ${selectedIds.length} 个实体吗？`)) return;

    try {
      const level = activeTab === 0 ? 'document' : activeTab === 1 ? 'kb' : 'global';
      await batchDeleteEntities(selectedIds, level);
      showMessage('批量删除成功', 'success');
      setSelectedIds([]);
      loadEntities();
    } catch (error) {
      console.error('批量删除失败:', error);
      showMessage('批量删除失败', 'error');
    }
  };

  const handleAdd = async (data) => {
    try {
      await addDocumentEntity(data);
      showMessage('添加成功', 'success');
      loadEntities();
    } catch (error) {
      console.error('添加失败:', error);
      showMessage('添加失败', 'error');
    }
  };

  const getLevelName = () => {
    switch (activeTab) {
      case 0:
        return 'document';
      case 1:
        return 'kb';
      case 2:
        return 'global';
      default:
        return 'document';
    }
  };

  return (
    <Box sx={{ width: '100%', height: '100%', overflow: 'auto' }}>
      {!embedded && (
        <AppBar position="static" color="default" elevation={0}>
          <Toolbar>
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              实体维护
            </Typography>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadEntities}
              sx={{ mr: 1 }}
            >
              刷新
            </Button>
            {activeTab === 0 && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setAddDialogOpen(true)}
                sx={{ mr: 1 }}
              >
                添加实体
              </Button>
            )}
            {selectedIds.length > 0 && (
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteIcon />}
                onClick={handleBatchDelete}
              >
                批量删除 ({selectedIds.length})
              </Button>
            )}
          </Toolbar>
        </AppBar>
      )}

      {/* 嵌入模式下的工具栏 */}
      {embedded && (
        <Box sx={{ p: 1, display: 'flex', gap: 1, alignItems: 'center', borderBottom: '1px solid #e0e0e0' }}>
          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshIcon />}
            onClick={loadEntities}
          >
            刷新
          </Button>
          {activeTab === 0 && (
            <Button
              variant="contained"
              size="small"
              startIcon={<AddIcon />}
              onClick={() => setAddDialogOpen(true)}
            >
              添加
            </Button>
          )}
          {selectedIds.length > 0 && (
            <Button
              variant="outlined"
              size="small"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={handleBatchDelete}
            >
              删除 ({selectedIds.length})
            </Button>
          )}
        </Box>
      )}

      {/* 统计信息 */}
      {stats && (
        <Box sx={{ p: 2, display: 'flex', gap: 2 }}>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Typography variant="subtitle2" color="text.secondary">
              文档级实体
            </Typography>
            <Typography variant="h4">{stats.document_entities}</Typography>
          </Paper>
          <Paper sx={{ p: 2, flex: 1 }}>
            <Typography variant="subtitle2" color="text.secondary">
              知识库级实体
            </Typography>
            <Typography variant="h4">{stats.kb_entities}</Typography>
          </Paper>
        </Box>
      )}

      {/* 标签页 */}
      <Tabs value={activeTab} onChange={handleTabChange} sx={{ px: 2 }}>
        <Tab label="文档级实体" />
        <Tab label="知识库级实体" />
        <Tab label="全局级实体" />
      </Tabs>

      {/* 过滤器 */}
      <Box sx={{ p: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <FormControl sx={{ minWidth: 150 }} size="small">
          <InputLabel>实体类型</InputLabel>
          <Select
            value={entityType}
            onChange={(e) => {
              setEntityType(e.target.value);
              setPage(1);
            }}
            label="实体类型"
          >
            {ENTITY_TYPES.map((type) => (
              <MenuItem key={type.value} value={type.value}>
                {type.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Typography variant="body2" color="text.secondary">
          共 {total} 个实体
        </Typography>
      </Box>

      {/* 实体列表 */}
      <TabPanel value={activeTab} index={0}>
        <EntityList
          level="document"
          entities={entities}
          total={total}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSelect={setSelectedIds}
          selectedIds={selectedIds}
          loading={loading}
        />
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <EntityList
          level="kb"
          entities={entities}
          total={total}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSelect={setSelectedIds}
          selectedIds={selectedIds}
          loading={loading}
        />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <EntityList
          level="global"
          entities={entities}
          total={total}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSelect={setSelectedIds}
          selectedIds={selectedIds}
          loading={loading}
        />
      </TabPanel>

      {/* 编辑对话框 */}
      <EditDialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        entity={currentEntity}
        level={getLevelName()}
        onSave={handleSaveEdit}
      />

      {/* 添加对话框 */}
      <AddDialog
        open={addDialogOpen}
        onClose={() => setAddDialogOpen(false)}
        documentId={documentId}
        onSave={handleAdd}
      />

      {/* 反馈对话框 */}
      <FeedbackDialog
        open={feedbackDialogOpen}
        onClose={() => setFeedbackDialogOpen(false)}
        entity={currentEntity}
        level={getLevelName()}
      />

      {/* 消息提示 */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
