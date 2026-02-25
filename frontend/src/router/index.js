import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

// 懒加载组件
const Login = () => import('../pages/Login.vue')
const TeacherDashboard = () => import('../pages/TeacherDashboard.vue')
const StudentDashboard = () => import('../pages/StudentDashboard.vue')

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/teacher/dashboard',
    name: 'TeacherDashboard',
    component: TeacherDashboard,
    meta: { requiresAuth: true, role: 'teacher' }
  },
  {
    path: '/student/dashboard',
    name: 'StudentDashboard',
    component: StudentDashboard,
    meta: { requiresAuth: true, role: 'student' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth
  const requiredRole = to.meta.role
  const isAuthenticated = authStore.isAuthenticated
  const userRole = authStore.user?.role

  if (requiresAuth && !isAuthenticated) {
    // 需要认证但未登录，重定向到登录页
    next('/login')
  } else if (requiresAuth && requiredRole && userRole !== requiredRole) {
    // 角色不匹配，根据用户角色重定向到对应仪表盘
    if (userRole === 'teacher') {
      next('/teacher/dashboard')
    } else if (userRole === 'student') {
      next('/student/dashboard')
    } else {
      next('/login')
    }
  } else {
    // 其他情况允许访问
    next()
  }
})

export default router
