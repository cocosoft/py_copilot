/**
 * 实时资源监控使用示例 - FE-008
 *
 * 展示如何使用资源监控组件
 *
 * @task FE-008
 * @phase 前端功能拓展
 */

import React, { useState, useCallback } from 'react';
import ResourceMonitor, { ResourceMonitorWithDetails } from './index';
import { Activity, Settings, Download, Bell, Shield } from 'lucide-react';

// ==================== 示例 1: 基础用法 ====================

/**
 * 基础资源监控示例
 */
export const BasicExample = () => {
  const handleRefresh = useCallback(() => {
    console.log('刷新数据');
  }, []);

  const handleExport = useCallback(() => {
    console.log('导出数据');
  }, []);

  const handleSettings = useCallback(() => {
    console.log('打开设置');
  }, []);

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', borderRadius: '8px' }}>
      <ResourceMonitor
        onRefresh={handleRefresh}
        onExport={handleExport}
        onSettings={handleSettings}
        thresholds={{ cpu: 80, memory: 85, disk: 90, queue: 50 }}
      />
    </div>
  );
};

// ==================== 示例 2: 带详情面板 ====================

/**
 * 带详情面板的资源监控示例
 */
export const WithDetailsExample = () => {
  return (
    <div style={{ padding: '24px', background: '#f5f5f5', borderRadius: '8px' }}>
      <ResourceMonitorWithDetails
        thresholds={{ cpu: 70, memory: 80, disk: 85, queue: 40 }}
      />
    </div>
  );
};

// ==================== 示例 3: 自定义阈值 ====================

/**
 * 自定义阈值示例
 */
export const CustomThresholdsExample = () => {
  const [thresholds, setThresholds] = useState({
    cpu: 60,
    memory: 70,
    disk: 80,
    queue: 30,
  });

  const handleThresholdChange = (key, value) => {
    setThresholds((prev) => ({ ...prev, [key]: Number(value) }));
  };

  return (
    <div>
      <div
        style={{
          padding: '16px',
          background: '#fff',
          borderRadius: '8px',
          marginBottom: '24px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <h4 style={{ margin: '0 0 16px 0' }}>自定义告警阈值</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          {Object.entries(thresholds).map(([key, value]) => (
            <div key={key}>
              <label
                style={{
                  display: 'block',
                  marginBottom: '8px',
                  fontSize: '13px',
                  color: '#666',
                  textTransform: 'uppercase',
                }}
              >
                {key === 'cpu' && 'CPU 阈值'}
                {key === 'memory' && '内存阈值'}
                {key === 'disk' && '磁盘阈值'}
                {key === 'queue' && '队列阈值'}
              </label>
              <input
                type="number"
                value={value}
                onChange={(e) => handleThresholdChange(key, e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d9d9d9',
                  borderRadius: '4px',
                  fontSize: '14px',
                }}
              />
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: '24px', background: '#f5f5f5', borderRadius: '8px' }}>
        <ResourceMonitor thresholds={thresholds} />
      </div>
    </div>
  );
};

// ==================== 示例 4: 嵌入仪表板 ====================

/**
 * 仪表板嵌入示例
 */
export const DashboardExample = () => {
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const handleRefresh = useCallback(() => {
    setLastUpdate(new Date());
  }, []);

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          padding: '16px',
          background: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Activity size={24} color="#1890ff" />
          <div>
            <h3 style={{ margin: 0, fontSize: '16px' }}>系统监控仪表板</h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#8c8c8c' }}>
              最后更新: {lastUpdate.toLocaleString()}
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={handleRefresh}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              background: '#1890ff',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            <Download size={14} />
            刷新
          </button>
        </div>
      </div>

      <div style={{ padding: '24px', background: '#f5f5f5', borderRadius: '8px' }}>
        <ResourceMonitor onRefresh={handleRefresh} />
      </div>
    </div>
  );
};

// ==================== 示例 5: 告警管理 ====================

/**
 * 告警管理示例
 */
export const AlertManagementExample = () => {
  const [alertHistory, setAlertHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const handleExport = useCallback(() => {
    const data = {
      exportTime: new Date().toISOString(),
      alertHistory,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `monitoring-data-${Date.now()}.json`;
    a.click();
  }, [alertHistory]);

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          padding: '16px',
          background: '#fff',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Bell size={24} color="#faad14" />
          <div>
            <h3 style={{ margin: 0, fontSize: '16px' }}>告警管理中心</h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#8c8c8c' }}>
              管理系统告警和通知
            </p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setShowHistory(!showHistory)}
            style={{
              padding: '8px 16px',
              background: '#f0f0f0',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            {showHistory ? '隐藏历史' : '查看历史'}
          </button>
          <button
            onClick={handleExport}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              background: '#52c41a',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            <Download size={14} />
            导出
          </button>
        </div>
      </div>

      <div style={{ padding: '24px', background: '#f5f5f5', borderRadius: '8px' }}>
        <ResourceMonitor />
      </div>

      {showHistory && (
        <div
          style={{
            marginTop: '24px',
            padding: '20px',
            background: '#fff',
            borderRadius: '8px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
          }}
        >
          <h4 style={{ margin: '0 0 16px 0' }}>告警历史记录</h4>
          {alertHistory.length === 0 ? (
            <p style={{ color: '#8c8c8c' }}>暂无历史记录</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {alertHistory.map((alert, index) => (
                <div
                  key={index}
                  style={{
                    padding: '12px',
                    background: '#f5f5f5',
                    borderRadius: '4px',
                    fontSize: '13px',
                  }}
                >
                  {alert}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ==================== 主示例页面 ====================

const ResourceMonitorExamples = () => {
  const [activeExample, setActiveExample] = useState('basic');

  const examples = {
    basic: { title: '基础用法', component: BasicExample, icon: Activity },
    details: { title: '带详情面板', component: WithDetailsExample, icon: Settings },
    thresholds: { title: '自定义阈值', component: CustomThresholdsExample, icon: Shield },
    dashboard: { title: '仪表板嵌入', component: DashboardExample, icon: Activity },
    alerts: { title: '告警管理', component: AlertManagementExample, icon: Bell },
  };

  const ActiveComponent = examples[activeExample].component;

  return (
    <div>
      <div
        style={{
          padding: '16px 24px',
          background: '#fff',
          borderBottom: '1px solid #f0f0f0',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <h1 style={{ margin: '0 0 16px 0' }}>实时资源监控示例 (FE-008)</h1>

        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {Object.entries(examples).map(([key, { title, icon: Icon }]) => (
            <button
              key={key}
              onClick={() => setActiveExample(key)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: activeExample === key ? '#1890ff' : '#f0f0f0',
                color: activeExample === key ? '#fff' : '#333',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <Icon size={16} />
              {title}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: '24px' }}>
        <ActiveComponent />
      </div>
    </div>
  );
};

export default ResourceMonitorExamples;
