<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/axiosInstance'

const authStore = useAuthStore()

// ref() is like a class field that Vue "watches"
// when you change .value, Vue automatically re-renders the template
// think of it like a field with a built-in observer/listener
const portfolio = ref([])   // will hold array of stock holdings from API
const loading = ref(true)   // controls whether we show spinner or content
const error = ref(null)     // holds error message if API call fails

const cash = ref(0)         // cash balance from API response
const netWorth = ref(0)     // total net worth from API response
const startingBalance = 10000  // fixed starting capital (no need for ref, never changes)

const autoTradesCount = ref(0)   // number of active auto-trade rules
const todayChange = ref(null)    // net worth change vs the last recorded snapshot
const todayChangePercent = ref(null)

// computed() is like a @Getter that automatically recalculates
// when any ref() it depends on changes — no need to call it manually
// portfolioValue recalculates whenever portfolio.value changes
// same as: portfolio.stream().mapToDouble(h -> h.shares * h.price).sum()
const portfolioValue = computed(() =>
  portfolio.value.reduce((sum, h) => sum + h.quantity * h.current_price, 0)
)

// these two also recalculate automatically when netWorth changes
const profitLoss = computed(() => netWorth.value - startingBalance)
const profitLossPercent = computed(() =>
  ((profitLoss.value / startingBalance) * 100).toFixed(2)
)

// onMounted is like @PostConstruct in Spring —
// runs once, after the component appears on screen
// async because we're calling the backend API
onMounted(async () => {
  try {
    // GET http://localhost:8000/api/portfolio
    // axiosInstance automatically attaches the Bearer token to this request
    const response = await api.get('/portfolio')

    // ?? is null-coalescing — same as in modern Java:
    // if response.data.holdings is null or undefined, use [] instead
    portfolio.value = response.data.holdings ?? []
    cash.value = response.data.cash_balance ?? 0
    netWorth.value = (response.data.cash_balance ?? 0) + (response.data.total_current_value ?? 0)

  } catch (e) {
    // Backend not running locally yet — using mock data for now
    portfolio.value = [
      { symbol: 'AAPL', shares: 10, current_price: 189.5 },
      { symbol: 'TSLA', shares: 5, current_price: 242.3 },
      { symbol: 'NVDA', shares: 3, current_price: 875.0 },
    ]
    cash.value = 2450.00
    netWorth.value = 2450.00 + (10 * 189.5) + (5 * 242.3) + (3 * 875.0)
  
  } finally {
    // finally block runs whether request succeeded or failed
    // always hide the loading spinner when we're done
    loading.value = false
  }

  // Active auto-trades count, for the "Auto orders" summary card
  try {
    const autoTradesResponse = await api.get('/auto-trades')
    autoTradesCount.value = (autoTradesResponse.data.auto_trades ?? []).length
  } catch (e) {
    autoTradesCount.value = 0
  }

  // Today's change: compare live net worth against the most recent saved snapshot
  try {
    if (authStore.user?.id) {
      const historyResponse = await api.get(`/users/${authStore.user.id}/portfolio/history`)
      const history = historyResponse.data ?? []
      if (history.length > 0) {
        const previousNetWorth = history[history.length - 1].net_worth
        if (previousNetWorth > 0) {
          todayChange.value = netWorth.value - previousNetWorth
          todayChangePercent.value = ((todayChange.value / previousNetWorth) * 100).toFixed(2)
        }
      }
    }
  } catch (e) {
    todayChange.value = null
    todayChangePercent.value = null
  }
})
</script>

<template>
  <div class="p-8 w-full max-w-5xl mx-auto">
    <h1 class="text-4xl font-bold mb-2 text-white">
      Welcome, {{ authStore.user?.username ?? 'Trader' }}
    </h1>
    <p class="text-sm mb-10 text-yellow-600 uppercase tracking-widest font-medium">Portfolio overview</p>

    <div v-if="loading" class="text-gray-500">Loading...</div>
    <div v-else-if="error" class="text-red-500">{{ error }}</div>

    <div v-else>

      <!-- warning banner: net worth below $500 -->
      <div
        v-if="netWorth > 0 && netWorth < 500"
        class="mb-6 rounded-xl border border-red-500 bg-red-900/30 px-6 py-4 text-red-300"
      >
        Warning: your net worth is below $500. You may be defaulted soon if it drops below $100.
      </div>

      <!-- summary cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">

        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Cash balance</p>
          <p class="text-3xl font-semibold text-white">${{ cash.toFixed(2) }}</p>
        </div>

        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Portfolio value</p>
          <p class="text-3xl font-semibold text-white">${{ portfolioValue.toFixed(2) }}</p>
        </div>

        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Net worth</p>
          <p class="text-3xl font-semibold text-white">${{ netWorth.toFixed(2) }}</p>
          <p :class="profitLoss >= 0 ? 'text-emerald-400' : 'text-red-400'" class="text-sm mt-2 font-medium">
            {{ profitLoss >= 0 ? '+' : '' }}${{ profitLoss.toFixed(2) }}
            ({{ profitLossPercent }}%)
          </p>
        </div>

      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">

        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Today's change</p>
          <template v-if="todayChange !== null">
            <p :class="todayChange >= 0 ? 'text-emerald-400' : 'text-red-400'" class="text-3xl font-semibold">
              {{ todayChange >= 0 ? '+' : '' }}${{ todayChange.toFixed(2) }}
            </p>
            <p :class="todayChange >= 0 ? 'text-emerald-400' : 'text-red-400'" class="text-sm mt-2 font-medium">
              {{ todayChangePercent >= 0 ? '+' : '' }}{{ todayChangePercent }}% vs yesterday
            </p>
          </template>
          <p v-else class="text-zinc-500 text-sm mt-1">Not enough history yet</p>
        </div>

        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Positions</p>
          <p class="text-3xl font-semibold text-white">{{ portfolio.length }}</p>
          <p class="text-zinc-500 text-sm mt-2">{{ portfolio.length === 1 ? 'stock' : 'stocks' }}</p>
        </div>

        <div class="rounded-xl p-6 bg-zinc-900 border border-zinc-800">
          <p class="text-xs uppercase tracking-widest text-zinc-500 mb-3">Auto orders</p>
          <p class="text-3xl font-semibold text-white">{{ autoTradesCount }}</p>
          <p class="text-zinc-500 text-sm mt-2">active</p>
        </div>

      </div>

      <!-- portfolio table (quick glance only — full breakdown lives on the Portfolio page) -->
      <div class="rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden">
        <div class="px-6 py-5 border-b border-zinc-800 flex items-center justify-between">
          <h2 class="text-base font-semibold text-white uppercase tracking-widest">Portfolio summary</h2>
          <RouterLink to="/portfolio" class="text-xs text-yellow-600 hover:text-yellow-500 uppercase tracking-widest">
            View full portfolio →
          </RouterLink>
        </div>

        <p v-if="portfolio.length === 0" class="p-6 text-zinc-500">
          No holdings yet. Go buy some stocks!
        </p>

        <table v-else class="w-full">
          <thead>
            <tr class="text-left border-b border-zinc-800">
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Symbol</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Shares</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Price</th>
              <th class="px-6 py-3 text-xs uppercase tracking-widest text-zinc-500">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="holding in portfolio"
              :key="holding.ticker"
              class="border-b border-zinc-800 hover:bg-zinc-800 transition"
            >
              <td class="px-6 py-4 font-bold text-yellow-500">{{ holding.ticker }}</td>
              <td class="px-6 py-4 text-zinc-300">{{ holding.quantity }}</td>
              <td class="px-6 py-4 text-zinc-300">${{ holding.current_price?.toFixed(2) ?? '—' }}</td>
              <td class="px-6 py-4 text-white font-medium">${{ (holding.quantity * holding.current_price).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  </div>
</template>
