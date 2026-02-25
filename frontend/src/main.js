import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import { useAuthStore } from './store/auth'
import './assets/main.css'

const app = createApp(App)
const pinia = createPinia()

app.use(router)
app.use(pinia)

// 在应用挂载前检查并恢复登录状态
const authStore = useAuthStore()
authStore.checkAuth()

app.mount('#app')
