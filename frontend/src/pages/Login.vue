<template>
  <div class="login-container">
    <div class="login-form-wrapper">
      <div class="login-header">
        <h1 class="login-title">智能教育系统</h1>
        <p class="login-subtitle">请登录您的账号</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <!-- 角色选择 -->
        <div class="form-group">
          <label class="form-label">角色选择</label>
          <div class="role-selector">
            <label 
              :class="['role-option', { active: selectedRole === 'teacher' }]"
              @click="selectedRole = 'teacher'"
            >
              <input 
                type="radio" 
                name="role" 
                value="teacher" 
                v-model="selectedRole" 
                class="role-radio"
              >
              <span class="role-text">教师</span>
            </label>
            <label 
              :class="['role-option', { active: selectedRole === 'student' }]"
              @click="selectedRole = 'student'"
            >
              <input 
                type="radio" 
                name="role" 
                value="student" 
                v-model="selectedRole" 
                class="role-radio"
              >
              <span class="role-text">学生</span>
            </label>
          </div>
        </div>

        <!-- 用户名输入 -->
        <div class="form-group">
          <label for="username" class="form-label">用户名</label>
          <input
            type="text"
            id="username"
            v-model="username"
            placeholder="请输入用户名"
            class="form-input"
            required
          >
        </div>

        <!-- 密码输入 -->
        <div class="form-group">
          <label for="password" class="form-label">密码</label>
          <input
            type="password"
            id="password"
            v-model="password"
            placeholder="请输入密码"
            class="form-input"
            required
          >
        </div>

        <!-- 登录按钮 -->
        <button
          type="submit"
          class="login-button"
          :disabled="isLoading"
        >
          {{ isLoading ? '登录中...' : '登录' }}
        </button>

        <!-- 错误信息 -->
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <!-- 提示信息 -->
        <div class="hint-message">
          <p>教师账号: user / 1234</p>
          <p>学生账号: 小明 / 12345</p>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()

// 表单数据
const selectedRole = ref('teacher')
const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

// 登录处理
const handleLogin = async () => {
  // 表单验证
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  try {
    isLoading.value = true
    errorMessage.value = ''

    const result = await authStore.login(username.value, password.value, selectedRole.value)
    
    if (result.success) {
      // 登录成功，根据角色跳转
      if (selectedRole.value === 'teacher') {
        router.push('/teacher/dashboard')
      } else {
        router.push('/student/dashboard')
      }
    } else {
      errorMessage.value = result.message || '登录失败，请检查账号和密码'
    }
  } catch (error) {
    console.error('Login error:', error)
    errorMessage.value = '登录失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-form-wrapper {
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-title {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin-bottom: 8px;
}

.login-subtitle {
  font-size: 14px;
  color: #666;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.role-selector {
  display: flex;
  gap: 16px;
}

.role-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
  justify-content: center;
}

.role-option:hover {
  border-color: #667eea;
}

.role-option.active {
  border-color: #667eea;
  background-color: rgba(102, 126, 234, 0.1);
}

.role-radio {
  cursor: pointer;
}

.role-text {
  cursor: pointer;
  font-weight: 500;
}

.form-input {
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.login-button {
  padding: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  color: #ff4d4f;
  font-size: 14px;
  text-align: center;
  padding: 8px;
}

.hint-message {
  margin-top: 16px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  font-size: 12px;
  color: #666;
}

.hint-message p {
  margin-bottom: 4px;
}

.hint-message p:last-child {
  margin-bottom: 0;
}
</style>
