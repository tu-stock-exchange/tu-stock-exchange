import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/axiosInstance'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  async function login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    token.value = response.data.access_token
    localStorage.setItem('token', token.value)

    // fetch full user profile so username is available everywhere
    const meResponse = await api.get('/users/me')
    user.value = meResponse.data
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  // logic needed for default page; if the user's net worth falls under 100 then he will be redirected to the default page
  const isBankrupt = computed(() => {
    return isLoggedIn.value && netWorth.value < 100
  })

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return { token, user, isLoggedIn, login, logout }
})
