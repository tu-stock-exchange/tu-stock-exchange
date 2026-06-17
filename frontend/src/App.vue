<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <nav class="w-full flex items-center gap-6 px-10 py-4 border-b border-zinc-800 bg-zinc-950">
    <span class="text-white font-bold text-lg mr-4">TU Stock Exchange</span>

    <RouterLink to="/market" class="nav-link">Market</RouterLink>
    <RouterLink to="/leaderboard" class="nav-link">Leaderboard</RouterLink>

    <template v-if="authStore.isLoggedIn">
      <RouterLink to="/dashboard" class="nav-link">Dashboard</RouterLink>
      <RouterLink to="/portfolio" class="nav-link">Portfolio</RouterLink>
      <RouterLink to="/auto-trades" class="nav-link">Auto-trades</RouterLink>
      <RouterLink to="/profile" class="nav-link">Profile</RouterLink>
    </template>

    <div class="ml-auto flex gap-4">
      <template v-if="authStore.isLoggedIn">
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
