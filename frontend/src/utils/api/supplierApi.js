import { request } from '../apiUtils';

// 供应商相关API
export const supplierApi = {
  // 获取所有供应商
  getAll: async () => {
    console.log('🔄 supplierApi.getAll - 开始调用后端API');
    const response = await request('/model-management/suppliers', {
      method: 'GET'
    });
    
    console.log('🔄 supplierApi.getAll - 收到后端响应:', response);
    
    // 处理后端返回格式
    let suppliersData = [];
    
    // 检查是否直接返回了数组
    if (Array.isArray(response)) {
      suppliersData = response;
    }
    
    // 转换后端数据格式为前端所需格式，包含website、is_active和logo字段
    const formattedSuppliers = suppliersData.map(supplier => ({
      id: supplier.id,
      key: String(supplier.id),
      name: supplier.name || supplier.display_name || '',
      description: supplier.description || '',
      logo: supplier.logo || '',  // 添加logo字段
      category: supplier.category || '',  // 添加category字段
      apiUrl: supplier.api_endpoint || supplier.api_url || supplier.base_url || '',
      api_docs: supplier.api_docs || '',  // 添加api_docs字段
      website: supplier.website || '',  // 添加官网字段
      apiKeyRequired: supplier.api_key_required || (supplier.api_key ? true : false),
      is_active: supplier.is_active !== undefined ? supplier.is_active : false // 添加is_active字段
    }));
    
    console.log('✅ supplierApi.getAll - 格式化后的供应商数据数量:', formattedSuppliers.length);
    
    return formattedSuppliers;
  },
  
  // 获取单个供应商
  getById: async (id) => {
    const endpoint = `/model-management/suppliers/${id}`;
    console.log('🔄 supplierApi.getById - 请求URL:', endpoint);
    const supplier = await request(endpoint, {
      method: 'GET'
    });
    
    // 格式化响应数据以匹配前端需求
    if (supplier) {
      return {
        id: supplier.id,
        key: String(supplier.id),
        name: supplier.name || supplier.display_name || '',
        logo: supplier.logo || '',  // 添加logo字段
        category: supplier.category || '',  // 添加category字段
        website: supplier.website || '',  // 添加官网字段
        description: supplier.description || '',
        apiUrl: supplier.api_endpoint || supplier.api_url || supplier.base_url || '',
        api_docs: supplier.api_docs || '',  // 添加api_docs字段
        apiKeyRequired: supplier.api_key_required || (supplier.api_key ? true : false),
        is_active: supplier.is_active !== undefined ? supplier.is_active : false // 添加is_active字段
      };
    }
    return { error: 'Supplier not found' };
  },
  
  // 创建新供应商
  create: async (supplier) => {
    console.log('🔄 supplierApi.create - 原始数据:', supplier);
    
    // 修正字段映射，确保与数据库字段一致，使用新的字段名
    const backendSupplierData = {
        name: supplier.name,
        description: supplier.description || '',
        logo: supplier.logo || '',
        category: supplier.category || '',
        website: supplier.website || '', // 确保正确处理website字段
        api_endpoint: supplier.api_endpoint || '',
        api_docs: supplier.api_docs || '',
        api_key: supplier.api_key || '',
        api_key_required: supplier.api_key_required !== undefined ? supplier.api_key_required : !!supplier.api_key,
        is_active: supplier.is_active !== undefined ? supplier.is_active : true
    };
    
    console.log('🔄 supplierApi.create - 发送到后端的供应商数据:', backendSupplierData);
    
    // 使用正确的API路径
    const response = await request('/model-management/suppliers', {
      method: 'POST',
      body: JSON.stringify(backendSupplierData),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // 格式化响应以匹配前端需求
    return {
      id: response.id,
      key: String(response.id),
      name: response.name,
      description: response.description || '',
      logo: response.logo || '',
      category: response.category || '',
      website: response.website || '',
      api_endpoint: response.api_endpoint || '',
      api_docs: response.api_docs || '',
      api_key: response.api_key || '',
      api_key_required: response.api_key_required,
      is_active: response.is_active
    };
  },
  
  // 只更新供应商状态(is_active)
  updateSupplierStatus: async (id, isActive) => {
    console.log('🔄 supplierApi.updateSupplierStatus - 开始执行状态更新操作');
    
    // 确保ID是数字类型
    const numericId = Number(id);
    console.log('🔄 supplierApi.updateSupplierStatus - ID:', id, '转换为数字:', numericId);
    console.log('🔄 supplierApi.updateSupplierStatus - 新状态:', isActive);
    
    // 先获取当前供应商的完整数据，使用直接的request调用避免循环引用
    const getEndpoint = `/model-management/suppliers/${numericId}`;
    console.log('🔄 supplierApi.updateSupplierStatus - 获取供应商数据的端点:', getEndpoint);
    const currentSupplier = await request(getEndpoint, { method: 'GET' });
    console.log('🔄 supplierApi.updateSupplierStatus - 当前供应商数据:', currentSupplier);
    
    // 创建一个包含所有现有字段但只更新is_active的对象，保持与后端期望的字段名一致
    // 先复制所有字段
    const backendUpdateData = { ...currentSupplier };
    // 然后明确设置is_active为新值，确保覆盖原始值
    backendUpdateData.is_active = isActive;
    // 确保包含所有必要字段并处理不同的字段名
    backendUpdateData.name = currentSupplier.name || currentSupplier.display_name || '';
    backendUpdateData.description = currentSupplier.description || '';
    backendUpdateData.logo = currentSupplier.logo || '';
    backendUpdateData.category = currentSupplier.category || '';
    backendUpdateData.website = currentSupplier.website || '';
    backendUpdateData.api_endpoint = currentSupplier.api_endpoint || currentSupplier.apiUrl || '';
    backendUpdateData.api_docs = currentSupplier.api_docs || currentSupplier.api_documentation || '';
    backendUpdateData.api_key = currentSupplier.api_key || '';
    backendUpdateData.api_key_required = currentSupplier.api_key_required !== undefined ? currentSupplier.api_key_required : !!currentSupplier.api_key;
    
    console.log('🔄 supplierApi.updateSupplierStatus - 发送到后端的更新数据:', JSON.stringify(backendUpdateData));
    
    // 使用正确的端点
    const endpoint = `/model-management/suppliers/${numericId}`;
    console.log('🔄 supplierApi.updateSupplierStatus - endpoint:', endpoint);
    
    // 发送PUT请求
    const response = await request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(backendUpdateData),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ supplierApi.updateSupplierStatus - 状态更新成功');
    
    // 返回更新后的供应商数据
    return {
      id: response.id,
      key: String(response.id),
      name: response.name,
      description: response.description || '',
      website: response.website || '',
      api_endpoint: response.api_endpoint || '',
      api_docs: response.api_docs || '',
      api_key: response.api_key || '',
      api_key_required: response.api_key_required,
      is_active: response.is_active
    };
  },
  
  // 更新供应商（完整更新）
  update: async (id, updatedSupplier) => {
    console.log('🟢 supplierApi.update - 开始执行完整更新操作');
    
    // 确保ID是数字类型
    const numericId = Number(id);
    console.log('🟢 supplierApi.update - ID:', id, '转换为数字:', numericId);
    
    console.log('🟢 supplierApi.update - 原始数据:', updatedSupplier);
    
    // 发送完整的供应商数据，确保包含所有必需字段
    // 先复制所有字段
    const backendUpdateData = { ...updatedSupplier };
    // 然后确保所有必需字段都有正确的值
    backendUpdateData.name = updatedSupplier.name || '';
    backendUpdateData.description = updatedSupplier.description || '';
    backendUpdateData.logo = updatedSupplier.logo || '';
    backendUpdateData.category = updatedSupplier.category || '';
    backendUpdateData.website = updatedSupplier.website || '';
    backendUpdateData.api_endpoint = updatedSupplier.api_endpoint || '';
    backendUpdateData.api_docs = updatedSupplier.api_docs || '';
    backendUpdateData.api_key = updatedSupplier.api_key || '';
    backendUpdateData.api_key_required = updatedSupplier.api_key_required !== undefined ? updatedSupplier.api_key_required : !!updatedSupplier.api_key;
    backendUpdateData.is_active = updatedSupplier.is_active !== undefined ? updatedSupplier.is_active : true;
    
    console.log('🟢 supplierApi.update - 发送到后端的更新数据:', JSON.stringify(backendUpdateData, null, 2));
    
    // 修正endpoint，后端路由是/model-management/suppliers/{id}
    const endpoint = `/model-management/suppliers/${numericId}`;
    console.log('🟢 supplierApi.update - endpoint:', endpoint);
    
    console.log('🟢 supplierApi.update - 准备发送PUT请求...');
    
    // 直接发送请求，不使用嵌套try-catch，确保错误正确抛出
    const response = await request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(backendUpdateData),
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    console.log('✅ supplierApi.update - 请求成功完成，收到响应');
    
    // 格式化响应以匹配前端需求
    return {
      id: response.id,
      key: String(response.id),
      name: response.name,
      description: response.description || '',
      logo: response.logo || '',
      category: response.category || '',
      website: response.website || '',
      api_endpoint: response.api_endpoint || '',
      api_docs: response.api_docs || '',
      api_key: response.api_key || '',
      api_key_required: response.api_key_required,
      is_active: response.is_active
    };
  },
  
  // 删除供应商
  delete: async (id) => {
    const endpoint = `/model-management/suppliers/${id}`;
    console.log('🔄 supplierApi.delete - 请求URL:', endpoint);
    return await request(endpoint, {
      method: 'DELETE'
    });
  }
};

export default supplierApi;