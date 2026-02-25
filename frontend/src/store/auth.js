import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const isAuthenticated = ref(!!localStorage.getItem('user'))

  // 获取器
  const getUser = computed(() => user.value)
  const getToken = computed(() => token.value)
  const getIsAuthenticated = computed(() => isAuthenticated.value)
  const getRole = computed(() => user.value?.role)

  // 动作
  const login = async (email, password, role) => {
    try {
      const response = await apiLogin(email, password, role)
      if (response.success) {
        // 保存用户信息到localStorage
        localStorage.setItem('user', JSON.stringify(response.user))
        localStorage.setItem('token', response.token)
        
        // 更新状态
        user.value = response.user
        token.value = response.token
        isAuthenticated.value = true
        
        return { success: true, user: response.user }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, message: '登录失败，请检查网络连接' }
    }
  }

  const logout = () => {
    // 清除localStorage
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    
    // 重置状态
    user.value = null
    token.value = null
    isAuthenticated.value = false
  }

  const checkAuth = () => {
    // 从localStorage恢复认证状态
    const savedUser = localStorage.getItem('user')
    if (savedUser) {
      user.value = JSON.parse(savedUser)
      token.value = localStorage.getItem('token')
      isAuthenticated.value = true
      return true
    }
    return false
  }

  return {
    user: getUser,
    token: getToken,
    isAuthenticated: getIsAuthenticated,
    role: getRole,
    login,
    logout,
    checkAuth
  }
})
