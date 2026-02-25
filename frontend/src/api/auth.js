import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 10000
})

// 登录API
export const login = async (username, password, role) => {
  try {
    const response = await api.post('/login', {
      username,
      password,
      role
    })
    return response.data
  } catch (error) {
    console.error('Login API error:', error)
    throw error
  }
}
