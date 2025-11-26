// 最终验证脚本 - 测试修复后的供应商状态切换功能
// 此脚本将直接使用fetch API模拟前端API调用的行为

const API_BASE_URL = 'http://localhost:8001';

// 辅助函数：打印信息
function log(message) {
  console.log(`[${new Date().toISOString()}] ${message}`);
}

// 模拟updateSupplierStatus方法的行为
async function simulateUpdateSupplierStatus(id, isActive) {
  log(`开始模拟updateSupplierStatus操作 - ID: ${id}, 新状态: ${isActive}`);
  
  try {
    // Step 1: 获取当前供应商数据
    log('Step 1: 获取当前供应商完整数据');
    const getResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (!getResponse.ok) {
      throw new Error(`获取供应商数据失败: ${getResponse.statusText}`);
    }
    
    const currentSupplier = await getResponse.json();
    log(`成功获取供应商数据: ${currentSupplier.name || currentSupplier.display_name}`);
    
    // Step 2: 构建更新数据 - 这是修复后的逻辑
    log('Step 2: 构建更新数据（应用修复后的逻辑）');
    // 先复制所有字段
    const updateData = { ...currentSupplier };
    // 然后明确设置is_active为新值，确保覆盖原始值
    updateData.is_active = isActive;
    // 确保包含所有必要字段并处理不同的字段名
    updateData.name = currentSupplier.name || currentSupplier.display_name || '';
    updateData.description = currentSupplier.description || '';
    updateData.logo = currentSupplier.logo || '';
    updateData.category = currentSupplier.category || '';
    updateData.website = currentSupplier.website || '';
    updateData.api_endpoint = currentSupplier.api_endpoint || currentSupplier.apiUrl || '';
    updateData.api_docs = currentSupplier.api_docs || currentSupplier.api_documentation || '';
    updateData.api_key = currentSupplier.api_key || '';
    updateData.api_key_required = currentSupplier.api_key_required !== undefined ? currentSupplier.api_key_required : !!currentSupplier.api_key;
    
    log(`更新数据准备就绪 - is_active: ${updateData.is_active}`);
    
    // Step 3: 执行PUT请求
    log('Step 3: 执行PUT请求更新供应商');
    const updateResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData)
    });
    
    if (!updateResponse.ok) {
      const errorData = await updateResponse.json().catch(() => ({}));
      throw new Error(`更新失败: ${updateResponse.statusText}\n${JSON.stringify(errorData, null, 2)}`);
    }
    
    // Step 4: 获取并验证更新结果
    const updatedSupplier = await updateResponse.json();
    log(`✅ 更新成功! 返回的状态: ${updatedSupplier.is_active}`);
    
    // Step 5: 再次获取确认数据库中的状态
    log('Step 5: 再次获取供应商数据确认数据库中的实际状态');
    const verifyResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers/${id}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const verifiedSupplier = await verifyResponse.json();
    log(`数据库中的实际状态: ${verifiedSupplier.is_active}`);
    
    // 返回验证结果
    return {
      success: verifiedSupplier.is_active === isActive,
      expected: isActive,
      actual: verifiedSupplier.is_active,
      supplier: verifiedSupplier
    };
    
  } catch (error) {
    log(`❌ 操作失败: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}

// 主测试函数
async function runVerification() {
  log('===== 供应商状态切换功能 - 最终验证 =====');
  
  try {
    // 获取一个供应商进行测试
    const suppliersResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (!suppliersResponse.ok) {
      throw new Error(`无法获取供应商列表: ${suppliersResponse.statusText}`);
    }
    
    const suppliers = await suppliersResponse.json();
    if (suppliers.length === 0) {
      throw new Error('没有找到供应商数据');
    }
    
    const testSupplier = suppliers[0];
    log(`\n选择测试供应商: ${testSupplier.name || testSupplier.display_name} (ID: ${testSupplier.id})`);
    log(`当前状态: ${testSupplier.is_active ? '已启用' : '未启用'}`);
    
    // 测试切换状态
    const newStatus = !testSupplier.is_active;
    log(`\n测试 1: 切换状态为 ${newStatus ? '已启用' : '未启用'}`);
    
    const result1 = await simulateUpdateSupplierStatus(testSupplier.id, newStatus);
    
    if (result1.success) {
      log('✅ 测试 1 通过! 状态成功更新');
      
      // 测试切换回原状态
      log(`\n测试 2: 切换回原始状态 ${!newStatus ? '已启用' : '未启用'}`);
      const result2 = await simulateUpdateSupplierStatus(testSupplier.id, !newStatus);
      
      if (result2.success) {
        log('✅ 测试 2 通过! 状态成功切换回原始值');
        log('\n🎉 所有测试通过! updateSupplierStatus方法已成功修复');
      } else {
        log('❌ 测试 2 失败');
        log(`错误详情: ${result2.error || `期望 ${!newStatus}, 实际 ${result2.actual}`}`);
      }
    } else {
      log('❌ 测试 1 失败');
      log(`错误详情: ${result1.error || `期望 ${newStatus}, 实际 ${result1.actual}`}`);
    }
    
    log('\n===== 验证完成 =====');
    
  } catch (error) {
    log(`\n❌ 验证过程中发生错误: ${error.message}`);
  }
}

// 运行验证
runVerification();