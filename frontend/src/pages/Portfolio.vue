<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/axiosInstance'

const portfolio = ref(null)
const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    const response = await api.get('/portfolio')
    portfolio.value = response.data
  } catch (e) {
    error.value = 'Failed to load portfolio.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="p-8 w-full max-w-5xl mx-auto">
    <h1 class="text-4xl font-bold mb-2 text-white">Portfolio</h1>
    <p class="text-sm mb-10 text-yellow-600 uppercase tracking-widest font-medium">Your holdings</p>

    <div v-if="loading" class="text-gray-400">Loading...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <div v-else>
      <!-- summary cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Cash balance</p>
          <p class="text-3xl font-semibold text-white">${{ portfolio.cash_balance?.toFixed(2) }}</p>
        </div>
        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Stocks value</p>
          <p class="text-3xl font-semibold text-white">${{ portfolio.total_current_value?.toFixed(2) }}</p>
        </div>
        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Total P&L</p>
          <p
            class="text-3xl font-semibold"
            :class="portfolio.total_pnl >= 0 ? 'text-emerald-400' : 'text-red-400'"
          >
            {{ portfolio.total_pnl >= 0 ? '+' : '' }}${{ portfolio.total_pnl?.toFixed(2) }}
          </p>
        </div>
      </div>

      <!-- holdings table -->
      <div class="rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden">
        <div class="px-6 py-5 border-b border-zinc-800 flex items-center justify-between">
          <h2 class="text-base font-semibold text-white uppercase tracking-widest">Holdings</h2>
          <span class="text-xs text-yellow-600 uppercase tracking-widest">
            {{ portfolio.holdings?.length ?? 0 }} positions
          </span>
        </div>

        <p v-if="!portfolio.holdings?.length" class="p-6 text-zinc-500">
          No holdings yet. Go buy some stocks!
        </p>

        <table v-else class="w-full">
          <thead>
            <tr class="text-left border-b border-zinc-800">
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Ticker</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Qty</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Avg buy</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Current</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Value</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">P&L</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="h in portfolio.holdings"
              :key="h.ticker"
              class="border-b border-zinc-800 hover:bg-zinc-800 transition"
            >
              <td class="px-6 py-4 font-bold text-yellow-500">{{ h.ticker }}</td>
              <td class="px-6 py-4 text-zinc-300">{{ h.quantity }}</td>
              <td class="px-6 py-4 text-zinc-300">${{ h.average_buy_price?.toFixed(2) }}</td>
              <td class="px-6 py-4 text-zinc-300">${{ h.current_price?.toFixed(2) }}</td>
              <td class="px-6 py-4 text-white font-medium">${{ h.current_value?.toFixed(2) }}</td>
              <td
                class="px-6 py-4 font-medium"
                :class="h.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'"
              >
                {{ h.pnl >= 0 ? '+' : '' }}${{ h.pnl?.toFixed(2) }}
                <span class="text-xs ml-1">({{ h.pnl_percent?.toFixed(2) }}%)</span>
              </td>
              <td class="px-6 py-4 text-right">
                <RouterLink :to="`/market?ticker=${h.ticker}&action=sell`" class="text-red-400 hover:text-red-300 text-sm font-medium whitespace-nowrap">
                  Sell →
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
