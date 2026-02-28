/**
 * 能力中心组件入口文件
 *
 * 统一导出能力中心相关组件和状态管理
 */

// 导出能力中心页面组件
export { default as CapabilityCenter } from '../../pages/CapabilityCenter';

// 导出能力卡片组件
export { default as CapabilityCard } from './CapabilityCard';

// 导出状态管理
export { useCapabilityCenterStore } from '../../stores/capabilityCenterStore';

// 导出API客户端
export {
  capabilityCenterApi,
  capabilityCenterQueryKeys,
  useCapabilitiesQuery,
  useToggleCapabilityMutation,
  useDeleteCapabilityMutation,
  useAgentCapabilitiesQuery,
  useAssignCapabilityMutation,
  useRemoveCapabilityMutation
} from '../../services/capabilityCenterApi';
