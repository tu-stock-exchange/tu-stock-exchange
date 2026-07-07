<script setup>
import { ref, watch } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/axiosInstance'

const authStore = useAuthStore()
const route = useRoute()
const cashBalance = ref(null)

async function refreshCashBalance() {
  if (!authStore.isLoggedIn) {
    cashBalance.value = null
    return
  }
  try {
    const response = await api.get('/portfolio')
    cashBalance.value = response.data.cash_balance ?? 0
  } catch (e) {
    cashBalance.value = null
  }
}

// refresh whenever the user navigates, so the balance stays up to date after trades
watch(() => route.fullPath, refreshCashBalance, { immediate: true })
</script>

<template>
  <nav class="w-full flex items-center gap-6 px-10 py-4 border-b border-zinc-800 bg-zinc-950">
    <span class="text-white font-bold text-lg mr-4 flex items-center gap-2">
      <span aria-hidden="true">📈</span> StockGame
    </span>
    <RouterLink to="/market" class="nav-link">Market</RouterLink>
    <RouterLink to="/leaderboard" class="nav-link">Leaderboard</RouterLink>
    <template v-if="authStore.isLoggedIn">
      <RouterLink to="/dashboard" class="nav-link">Dashboard</RouterLink>
      <RouterLink to="/portfolio" class="nav-link">Portfolio</RouterLink>
      <RouterLink to="/auto-trades" class="nav-link">Auto-trades</RouterLink>
      <RouterLink to="/profile" class="nav-link">Profile</RouterLink>
    </template>
    <div class="ml-auto flex items-center gap-4">
      <template v-if="authStore.isLoggedIn">
        <span
          v-if="cashBalance !== null"
          class="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 text-yellow-500 font-semibold text-sm px-3 py-1.5 rounded-xl"
        >
          <span aria-hidden="true">💰</span> ${{ cashBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
        </span>
        <span class="text-zinc-500 text-sm self-center">{{ authStore.user?.username }}</span>
        <button @click="authStore.logout()" class="nav-link">Logout</button>
      </template>
      <template v-else>
        <RouterLink to="/login" class="nav-link">Login</RouterLink>
        <RouterLink to="/register" class="nav-link">Register</RouterLink>
      </template>
    </div>
  </nav>
  <main class="min-h-screen bg-zinc-950 text-white">
    <RouterView />
  </main>
</template>

<style scoped>
/* css logic for task manager (all the pages) */
/* normal */
.nav-link {
  color: #71717A;
  text-decoration: none;
  padding-bottom: 4px;
  border-bottom: 2px solid transparent;  /* placeholder — unsichtbar */
}
/* hover */
.nav-link:hover {
  color: #EAB308;
  border-bottom: 2px solid #EAB308;
}
/* actual page */
.nav-link.router-link-active {
  color: #EAB308;
  border-bottom: 2px solid #EAB308;
}
</style>
<!--  -->
<!--  -->
<!--  -->
