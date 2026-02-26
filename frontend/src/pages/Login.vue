<template>
  <div class="login-container">
    <div class="login-content">
      <h1 class="login-title" :class="{ visible: showTitle }">教师评语生成系统</h1>
      
      <form @submit.prevent="handleLogin" class="login-form" :class="{ visible: showForm }">
        <div class="input-row">
          <input
            type="text"
            v-model="username"
            placeholder="账号"
            class="form-input"
          >
          <input
            type="password"
            v-model="password"
            placeholder="密码"
            class="form-input"
          >
        </div>
        
        <div class="role-row">
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
        
        <button
          type="submit"
          class="login-button"
          :disabled="isLoading"
        >
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
        
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const router = useRouter()
const authStore = useAuthStore()

const selectedRole = ref('teacher')
const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const showTitle = ref(false)
const showForm = ref(false)

onMounted(() => {
  setTimeout(() => {
    showTitle.value = true
  }, 300)
  
  setTimeout(() => {
    showForm.value = true
  }, 800)
})

const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入账号和密码'
    return
  }

  try {
    isLoading.value = true
    errorMessage.value = ''

    const result = await authStore.login(username.value, password.value, selectedRole.value)
    
    if (result.success) {
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
  width: 100vw;
  height: 100vh;
  background-image: url('/login.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, rgba(0, 0, 0, 0.3) 0%, rgba(0, 0, 0, 0.1) 50%, rgba(0, 0, 0, 0.3) 100%);
  pointer-events: none;
}

.login-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 500px;
  padding: 0 20px;
}

.login-title {
  font-size: 48px;
  font-weight: bold;
  color: #ffffff;
  text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.5), 0 0 40px rgba(102, 126, 234, 0.5);
  letter-spacing: 8px;
  margin-bottom: 50px;
  opacity: 0;
  transform: translateY(-30px);
  transition: all 0.8s ease;
}

.login-title.visible {
  opacity: 1;
  transform: translateY(0);
}

.login-form {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 25px;
  width: 100%;
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.6s ease;
}

.login-form.visible {
  opacity: 1;
  transform: translateY(0);
}

.input-row {
  display: flex;
  gap: 20px;
  width: 100%;
}

.form-input {
  flex: 1;
  padding: 14px 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 30px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: #ffffff;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.form-input:focus {
  outline: none;
  border-color: rgba(102, 126, 234, 0.8);
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.4);
}

.role-row {
  display: flex;
  gap: 20px;
  width: 100%;
  justify-content: center;
}

.role-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 30px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.role-option:hover {
  border-color: rgba(102, 126, 234, 0.8);
  background: rgba(102, 126, 234, 0.2);
}

.role-option.active {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.4);
  box-shadow: 0 0 15px rgba(102, 126, 234, 0.5);
}

.role-radio {
  display: none;
}

.role-text {
  font-size: 16px;
  font-weight: 500;
  color: #ffffff;
  cursor: pointer;
}

.login-button {
  padding: 14px 60px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 30px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  margin-top: 10px;
}

.login-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.error-message {
  color: #ff6b6b;
  font-size: 14px;
  text-align: center;
  padding: 10px 20px;
  background: rgba(255, 107, 107, 0.2);
  border-radius: 20px;
  backdrop-filter: blur(10px);
}
</style>
