
<template>
  <div class="p-8 w-full max-w-6xl mx-auto">
    <h1 class="text-4xl font-bold mb-2 text-white">Leaderboard</h1>
    <p class="text-sm mb-10 text-yellow-600 uppercase tracking-widest font-medium">Top traders</p>

    <div v-if="loading" class="text-gray-400">Loading...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <div v-else class="flex gap-6 items-start">
      <!-- bar chart -->
      <div class="rounded-xl bg-zinc-900 border border-zinc-800 p-6 w-2/5">
        <LeaderboardChart :players="chartData" />
      </div>

      <!-- table -->
      <div class="rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden w-3/5">
        <div class="px-6 py-5 border-b border-zinc-800">
          <h2 class="text-base font-semibold text-white uppercase tracking-widest">Rankings</h2>
        </div>
        <table class="w-full">
          <thead>
            <tr class="text-left border-b border-zinc-800">
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Rank</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Trader</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Net Worth</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(user, index) in users"
              :key="user.user_id"
              class="border-b border-zinc-800 transition"
              :class="user.user_id === currentUserId ? 'bg-yellow-900/30' : 'hover:bg-zinc-800'"
            >
              <td class="px-6 py-4 text-zinc-400">
                <span v-if="index === 0">🥇</span>
                <span v-else-if="index === 1">🥈</span>
                <span v-else-if="index === 2">🥉</span>
                <span v-else class="text-zinc-500">{{ index + 1 }}</span>
              </td>
              <td class="px-6 py-4 font-medium text-white">
                {{ user.username }}
                <span v-if="user.user_id === currentUserId" class="ml-2 text-xs text-yellow-500">(you)</span>
              </td>
              <td class="px-6 py-4 text-emerald-400 font-semibold">${{ user.portfolio_value?.toLocaleString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import LeaderboardChart from '../components/shared/LeaderboardChart.vue'
import api from '@/api/axiosInstance'

const authStore = useAuthStore()
const users = ref([])
const loading = ref(true)
const error = ref(null)

const currentUserId = computed(() => authStore.user?.id ?? null)

const chartData = computed(() =>
  users.value.slice(0, 5).map(u => ({
    username: u.username,
    portfolio_value: u.portfolio_value,
  }))
)

onMounted(async () => {
  try {
    const response = await api.get('/leaderboard')
    users.value = response.data
  } catch (e) {
    error.value = 'Could not load leaderboard.'
  } finally {
    loading.value = false
  }
})
</script>
