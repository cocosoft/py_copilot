// 身份验证相关工具函数

// Token存储键名
const STORAGE_PREFIX = 'llm_admin_';
const TOKEN_STORAGE_KEY = `${STORAGE_PREFIX}auth_token`;
const USER_INFO_STORAGE_KEY = `${STORAGE_PREFIX}user_info`;

/**
 * 保存认证令牌到本地存储
 * @param {string} token - JWT令牌
 */
export const saveAuthToken = (token) => {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } catch (error) {
    console.error('保存认证令牌失败:', error);
  }
};

/**
 * 从本地存储获取认证令牌
 * @returns {string|null} - JWT令牌或null
 */
export const getAuthToken = () => {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch (error) {
    console.error('获取认证令牌失败:', error);
    return null;
  }
};

/**
 * 移除本地存储中的认证令牌
 */
export const removeAuthToken = () => {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (error) {
    console.error('移除认证令牌失败:', error);
  }
};

/**
 * 保存用户信息到本地存储
 * @param {Object} userInfo - 用户信息对象
 */
export const saveUserInfo = (userInfo) => {
  try {
    localStorage.setItem(USER_INFO_STORAGE_KEY, JSON.stringify(userInfo));
  } catch (error) {
    console.error('保存用户信息失败:', error);
  }
};

/**
 * 从本地存储获取用户信息
 * @returns {Object|null} - 用户信息对象或null
 */
export const getUserInfo = () => {
  try {
    const userInfoStr = localStorage.getItem(USER_INFO_STORAGE_KEY);
    return userInfoStr ? JSON.parse(userInfoStr) : null;
  } catch (error) {
    console.error('获取用户信息失败:', error);
    return null;
  }
};

/**
 * 移除本地存储中的用户信息
 */
export const removeUserInfo = () => {
  try {
    localStorage.removeItem(USER_INFO_STORAGE_KEY);
  } catch (error) {
    console.error('移除用户信息失败:', error);
  }
};

/**
 * 清除所有认证相关数据
 */
export const clearAuthData = () => {
  removeAuthToken();
  removeUserInfo();
};

/**
 * 检查用户是否已登录
 * @returns {boolean} - 是否已登录
 */
export const isAuthenticated = () => {
  return !!getAuthToken();
};