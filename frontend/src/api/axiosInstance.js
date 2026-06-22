import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api', // Backend routes are mounted under /api
})

// INTERCEPTOR - adds token to every request before sending
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token') // get token from browser storage
  if (token) {
    config.headers.Authorization = `Bearer ${token}` // attach token to header
  }
  return config // send request with token
})

// INTERCEPTOR - handles expired or invalid token in response
api.interceptors.response.use(
  (response) => response, // if response is OK, just return it
  (error) => {
    if (error.response?.status === 401) { // 401 = unauthorized (token expired)
      localStorage.removeItem('token')    // delete old token
      window.location.href = '/login'     // redirect user to login page
    }
    return Promise.reject(error)
  }
)

export default api // export so the whole FE team can import this