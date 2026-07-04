<template>
  <div class="p-8 w-full max-w-6xl mx-auto">
    <div class="mb-10">
      <h1 class="text-4xl font-bold mb-6 text-white">Market</h1>
      <input
        v-model="search"
        type="text"
        placeholder="Search stocks..."
        class="border border-zinc-800 bg-zinc-900 text-white p-3 rounded-xl w-full mb-4 focus:outline-none focus:ring-2 focus:ring-yellow-500"
      />

      <div class="flex flex-wrap gap-2">
        <button
          v-for="cat in categories"
          :key="cat"
          @click="activeCategory = cat"
          class="px-4 py-2 rounded-xl text-sm font-medium transition"
          :class="activeCategory === cat
            ? 'bg-yellow-500 text-black'
            : 'bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-700'"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-zinc-400">Loading stocks...</div>
    <div v-else-if="error" class="text-red-400">{{ error }}</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="stock in filteredStocks"
        :key="stock.ticker"
        class="w-full border border-zinc-800 rounded-xl p-6 shadow-md hover:shadow-xl transition bg-zinc-900"
      >
        <div class="flex justify-between items-start mb-6">
          <div>
            <h2 class="font-bold text-3xl text-white">{{ stock.ticker }}</h2>
            <p class="text-zinc-400 text-lg">{{ stock.name }}</p>
          </div>
          <p class="font-bold text-2xl text-yellow-400">${{ stock.price.toFixed(2) }}</p>
        </div>

        <div class="flex gap-3">
          <button
            @click="openModal(stock, 'buy')"
            class="bg-green-600 hover:bg-green-700 transition text-white px-5 py-2 rounded-xl flex-1"
          >Buy</button>
          <button
            @click="openModal(stock, 'sell')"
            class="bg-red-600 hover:bg-red-700 transition text-white px-5 py-2 rounded-xl flex-1"
          >Sell</button>
        </div>
      </div>
    </div>

    <!-- Buy / Sell modal -->
    <div
      v-if="modal.open"
      class="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50"
      @click.self="modal.open = false"
    >
      <div class="bg-zinc-900 border border-zinc-800 rounded-xl w-full max-w-md overflow-hidden">
        <div
          class="flex items-center justify-between px-8 py-5"
          :class="modal.type === 'buy' ? 'bg-emerald-400' : 'bg-red-400'"
        >
          <h2 class="text-xl font-bold text-black">
            {{ modal.type === 'buy' ? 'Buy' : 'Sell' }} {{ modal.stock?.ticker }}
          </h2>
          <button
            @click="modal.open = false"
            class="text-black/70 hover:text-black text-xl leading-none font-bold"
            aria-label="Close"
          >✕</button>
        </div>

        <div class="p-8">
        <p class="text-zinc-400 mb-6">Current price: <span class="text-yellow-400 font-semibold">${{ modal.stock?.price.toFixed(2) }}</span></p>

        <label class="text-zinc-400 text-sm uppercase tracking-widest">Quantity</label>
        <input
          v-model.number="modal.quantity"
          type="number"
          min="1"
          class="w-full mt-2 mb-4 p-3 rounded-xl bg-zinc-800 border border-zinc-700 text-white focus:outline-none focus:ring-2 focus:ring-yellow-500"
        />

        <div class="bg-zinc-800 rounded-xl p-4 mb-6">
          <div class="flex justify-between text-sm text-zinc-400 mb-1">
            <span>Total</span>
            <span class="text-white font-semibold">
              ${{ (modal.quantity * (modal.stock?.price ?? 0)).toFixed(2) }}
            </span>
          </div>
        </div>

        <p v-if="modal.error" class="text-red-400 text-sm mb-4">{{ modal.error }}</p>
        <p v-if="modal.success" class="text-emerald-400 text-sm mb-4">{{ modal.success }}</p>

        <div class="flex gap-3">
          <button
            @click="modal.open = false"
            class="flex-1 py-3 rounded-xl border border-zinc-700 text-zinc-300 hover:bg-zinc-800 transition"
          >Cancel</button>
          <button
            @click="confirmTrade"
            :disabled="modal.loading || modal.quantity < 1"
            class="flex-1 py-3 rounded-xl font-semibold transition"
            :class="modal.type === 'buy'
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-red-600 hover:bg-red-700 text-white'"
          >
            {{ modal.loading ? 'Processing...' : 'Confirm' }}
          </button>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/api/axiosInstance'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const search = ref('')
const stocks = ref([])
const loading = ref(true)
const error = ref(null)

// TODO: temporary client-side categorization until the backend provides real
// sector data (see PR #36 "hardcoded stocks picks across different categories").
// Only categories that actually match our current 20 tickers are included —
// there are no Finance/Energy/Healthcare stocks in the popular list yet.
const TICKER_CATEGORIES = {
  AAPL: 'Tech', MSFT: 'Tech', GOOGL: 'Tech', NVDA: 'Tech', META: 'Tech',
  ADBE: 'Tech', CRM: 'Tech', INTC: 'Tech', AMD: 'Tech', PYPL: 'Tech',
  NFLX: 'Entertainment', DIS: 'Entertainment', SPOT: 'Entertainment', SNAP: 'Entertainment',
  AMZN: 'Consumer', TSLA: 'Consumer', UBER: 'Consumer', SHOP: 'Consumer', BABA: 'Consumer', SQ: 'Consumer',
}

const categories = ['All', 'Tech', 'Entertainment', 'Consumer']
const activeCategory = ref('All')

const modal = ref({
  open: false,
  type: 'buy',
  stock: null,
  quantity: 1,
  loading: false,
  error: null,
  success: null,
})

onMounted(async () => {
  try {
    const response = await api.get('/stocks/popular')
    stocks.value = response.data.stocks
  } catch (e) {
    error.value = 'Could not load stocks. Is the backend running?'
  } finally {
    loading.value = false
  }

  // Deep-link support: /market?ticker=AAPL&action=sell opens the modal directly
  // (used by the "Sell →" link on the Portfolio page)
  const queryTicker = route.query.ticker
  const queryAction = route.query.action === 'sell' ? 'sell' : 'buy'
  if (queryTicker) {
    const stock = stocks.value.find(s => s.ticker === queryTicker)
    if (stock) {
      openModal(stock, queryAction)
    }
  }
})

const filteredStocks = computed(() => {
  const q = search.value.toLowerCase()
  return stocks.value.filter(s => {
    const matchesSearch = !q || s.ticker.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
    const matchesCategory = activeCategory.value === 'All'
      || TICKER_CATEGORIES[s.ticker] === activeCategory.value
    return matchesSearch && matchesCategory
  })
})

function openModal(stock, type) {
  if (!authStore.isLoggedIn) {
    router.push('/login')
    return
  }
  modal.value = { open: true, type, stock, quantity: 1, loading: false, error: null, success: null }
}

async function confirmTrade() {
  if (modal.value.quantity < 1) return
  modal.value.loading = true
  modal.value.error = null
  modal.value.success = null

  try {
    const endpoint = modal.value.type === 'buy' ? '/trades/buy' : '/trades/sell'
    await api.post(endpoint, {
      ticker: modal.value.stock.ticker,
      quantity: modal.value.quantity,
    })
    modal.value.success = `${modal.value.type === 'buy' ? 'Bought' : 'Sold'} ${modal.value.quantity} share(s) of ${modal.value.stock.ticker}!`
    modal.value.quantity = 1
  } catch (e) {
    modal.value.error = e.response?.data?.detail ?? 'Trade failed. Try again.'
  } finally {
    modal.value.loading = false
  }
}
</script>
