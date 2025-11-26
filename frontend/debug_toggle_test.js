// 详细的供应商状态切换调试脚本
// 打印完整的请求和响应数据

const API_BASE_URL = 'http://localhost:8001';

// 辅助函数：打印响应信息
function printResponseInfo(response) {
  console.log(`响应状态码: ${response.status} ${response.statusText}`);
  console.log(`响应头: ${JSON.stringify(Object.fromEntries(response.headers), null, 2)}`);
}

// 主测试函数
async function debugSupplierToggle() {
  console.log('===== 详细供应商状态切换调试 =====\n');
  
  try {
    // Step 1: 获取所有供应商
    console.log('Step 1: 获取所有供应商');
    const suppliersResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    printResponseInfo(suppliersResponse);
    
    if (!suppliersResponse.ok) {
      throw new Error(`获取供应商失败: ${suppliersResponse.statusText}`);
    }
    
    const suppliers = await suppliersResponse.json();
    console.log(`找到 ${suppliers.length} 个供应商`);
    console.log('供应商列表:', JSON.stringify(suppliers.map(s => ({ id: s.id, name: s.name || s.display_name, active: s.is_active })), null, 2));
    
    if (suppliers.length === 0) {
      console.error('错误: 没有找到供应商数据');
      return;
    }
    
    // 选择第一个供应商进行测试
    const testSupplier = suppliers[0];
    console.log(`\n选择测试供应商: ${testSupplier.name || testSupplier.display_name} (ID: ${testSupplier.id})`);
    console.log(`当前状态: ${testSupplier.is_active ? '已启用' : '未启用'}`);
    
    // 切换状态
    const newStatus = !testSupplier.is_active;
    console.log(`\nStep 2: 切换状态为: ${newStatus ? '已启用' : '未启用'}`);
    
    // Step 3: 获取该供应商的完整数据
    console.log(`\nStep 3: 获取供应商 ${testSupplier.id} 的完整数据`);
    const supplierDetailResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers/${testSupplier.id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    printResponseInfo(supplierDetailResponse);
    
    if (!supplierDetailResponse.ok) {
      throw new Error(`获取供应商详情失败: ${supplierDetailResponse.statusText}`);
    }
    
    const currentSupplier = await supplierDetailResponse.json();
    console.log('当前供应商完整数据:', JSON.stringify(currentSupplier, null, 2));
    
    // Step 4: 构建更新数据对象
    console.log('\nStep 4: 构建完整的更新数据');
    // 先复制所有字段
    const updateData = { ...currentSupplier };
    // 然后明确设置is_active为newStatus，确保覆盖原始值
    updateData.is_active = newStatus;
    // 确保包含所有必要字段
    updateData.name = currentSupplier.name || currentSupplier.display_name || '';
    updateData.description = currentSupplier.description || '';
    updateData.logo = currentSupplier.logo || '';
    updateData.category = currentSupplier.category || '';
    updateData.website = currentSupplier.website || '';
    updateData.api_endpoint = currentSupplier.api_endpoint || currentSupplier.apiUrl || '';
    updateData.api_docs = currentSupplier.api_docs || currentSupplier.api_documentation || '';
    updateData.api_key_required = currentSupplier.api_key_required !== undefined ? currentSupplier.api_key_required : !!currentSupplier.api_key;
    
    console.log('发送到后端的更新数据:', JSON.stringify(updateData, null, 2));
    console.log(`特别注意: is_active 字段值为 ${updateData.is_active}`);
    
    // Step 5: 执行PUT请求更新供应商状态
    console.log('\nStep 5: 执行PUT请求更新供应商状态');
    const updateResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers/${testSupplier.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });
    
    printResponseInfo(updateResponse);
    
    if (!updateResponse.ok) {
      const errorData = await updateResponse.json().catch(() => ({}));
      throw new Error(`更新失败: ${updateResponse.statusText}\n详细信息: ${JSON.stringify(errorData, null, 2)}`);
    }
    
    // Step 6: 获取更新后的供应商数据
    const updatedSupplier = await updateResponse.json();
    console.log('\nStep 6: 获取更新后的供应商数据');
    console.log('更新后供应商完整数据:', JSON.stringify(updatedSupplier, null, 2));
    
    console.log('\n✅ 更新成功!');
    console.log(`更新后状态: ${updatedSupplier.is_active ? '已启用' : '未启用'}`);
    
    // 验证状态是否正确更新
    if (updatedSupplier.is_active === newStatus) {
      console.log('✅ 状态验证成功: 状态已正确切换');
    } else {
      console.error('❌ 状态验证失败: 状态未正确更新');
      console.error(`  - 期望状态: ${newStatus}`);
      console.error(`  - 实际状态: ${updatedSupplier.is_active}`);
    }
    
    // Step 7: 再次GET请求确认数据库中的实际状态
    console.log('\nStep 7: 再次获取供应商数据确认实际状态');
    const verifyResponse = await fetch(`${API_BASE_URL}/api/model-management/suppliers/${testSupplier.id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    printResponseInfo(verifyResponse);
    
    if (!verifyResponse.ok) {
      throw new Error(`验证获取失败: ${verifyResponse.statusText}`);
    }
    
    const verifiedSupplier = await verifyResponse.json();
    console.log('验证后的供应商状态:', JSON.stringify({ id: verifiedSupplier.id, name: verifiedSupplier.name, is_active: verifiedSupplier.is_active }, null, 2));
    
    if (verifiedSupplier.is_active === newStatus) {
      console.log('✅ 数据库状态验证成功: 状态已正确更新');
    } else {
      console.error('❌ 数据库状态验证失败: 状态未正确更新');
      console.error(`  - 期望状态: ${newStatus}`);
      console.error(`  - 实际数据库状态: ${verifiedSupplier.is_active}`);
    }
    
    console.log('\n🎉 调试完成!');
    
  } catch (error) {
    console.error('\n❌ 调试过程中发生错误:');
    console.error(error.message);
    if (error.stack) {
      console.error(error.stack);
    }
  }
}

// 运行调试
debugSupplierToggle();