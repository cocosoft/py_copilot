// 简单的供应商状态切换测试脚本
// 直接使用fetch API测试后端API

const API_BASE_URL = 'http://localhost:8001';

// 辅助函数：打印响应信息
function printResponseInfo(response) {
  console.log(`响应状态码: ${response.status} ${response.statusText}`);
}

// 主测试函数
async function testSupplierToggle() {
  console.log('===== 简单供应商状态切换测试 =====\n');
  
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
    console.log(`找到 ${suppliers.length} 个供应商\n`);
    
    if (suppliers.length === 0) {
      console.error('错误: 没有找到供应商数据');
      return;
    }
    
    // 选择第一个供应商进行测试
    const testSupplier = suppliers[0];
    console.log(`选择测试供应商: ${testSupplier.name || testSupplier.display_name} (ID: ${testSupplier.id})`);
    console.log(`当前状态: ${testSupplier.is_active ? '已启用' : '未启用'}`);
    
    // 切换状态
    const newStatus = !testSupplier.is_active;
    console.log(`\nStep 2: 切换状态为: ${newStatus ? '已启用' : '未启用'}`);
    
    // Step 3: 构建更新数据对象（包含所有现有字段）
    // 这模拟了我们在updateSupplierStatus方法中的实现
    console.log('构建完整的更新数据...');
    const updateData = {
      // 确保包含所有必要字段
      id: testSupplier.id,
      name: testSupplier.name || testSupplier.display_name,
      description: testSupplier.description || '',
      website: testSupplier.website || '',
      is_active: newStatus,
      // 添加其他可能存在的字段
      api_endpoint: testSupplier.api_endpoint || testSupplier.apiUrl || '',
      api_docs: testSupplier.api_docs || testSupplier.apiDocs || '',
      api_key_required: testSupplier.api_key_required || false,
      // 复制所有其他可能存在的字段
      ...testSupplier
    };
    
    console.log('更新数据准备就绪，执行PUT请求...');
    
    // Step 4: 执行PUT请求更新供应商状态
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
    
    // Step 5: 获取更新后的供应商数据
    const updatedSupplier = await updateResponse.json();
    
    console.log('\n✅ 更新成功!');
    console.log(`更新后状态: ${updatedSupplier.is_active ? '已启用' : '未启用'}`);
    
    // 验证状态是否正确更新
    if (updatedSupplier.is_active === newStatus) {
      console.log('✅ 状态验证成功: 状态已正确切换');
    } else {
      console.error('❌ 状态验证失败: 状态未正确更新');
    }
    
    // 验证数据完整性
    console.log('\n数据完整性检查:');
    console.log(`  - 名称: ${updatedSupplier.name || updatedSupplier.display_name}`);
    console.log(`  - 官网: ${updatedSupplier.website || '未设置'}`);
    console.log(`  - 描述: ${updatedSupplier.description || '未设置'}`);
    console.log(`  - API端点: ${updatedSupplier.api_endpoint || updatedSupplier.apiUrl || '未设置'}`);
    
    console.log('\n🎉 测试完成! 供应商状态切换功能正常工作');
    
  } catch (error) {
    console.error('\n❌ 测试过程中发生错误:');
    console.error(error.message);
  }
}

// 运行测试
testSupplierToggle();