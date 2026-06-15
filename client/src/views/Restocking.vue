<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <!-- Budget Configuration -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budgetConfig') }}</h3>
      </div>
      <div class="budget-config">
        <div class="budget-inputs">
          <div class="input-group">
            <label>{{ t('restocking.maxBudget') }}</label>
            <input type="number" v-model.number="maxBudget" :min="stepSize" :step="stepSize" class="number-input" />
          </div>
          <div class="input-group">
            <label>{{ t('restocking.stepSize') }}</label>
            <input type="number" v-model.number="stepSize" min="100" step="100" class="number-input" />
          </div>
        </div>
        <div class="budget-slider-section">
          <div class="budget-display">
            <span class="budget-label">{{ t('restocking.availableBudget') }}</span>
            <span class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</span>
          </div>
          <input
            type="range"
            :min="0"
            :max="maxBudget"
            :step="stepSize"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-range-labels">
            <span>{{ currencySymbol }}0</span>
            <span>{{ currencySymbol }}{{ maxBudget.toLocaleString() }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>

    <!-- Recommended Items -->
    <div v-else class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendedItems.length }})</h3>
        <div class="budget-summary">
          <span class="summary-item">
            {{ t('restocking.totalCost') }}:
            <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong>
          </span>
          <span class="summary-item" :class="{ 'remaining-ok': remainingBudget >= 0, 'remaining-over': remainingBudget < 0 }">
            {{ t('restocking.remainingBudget') }}:
            <strong>{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</strong>
          </span>
        </div>
      </div>

      <p class="hint-text">{{ t('restocking.recommendationHint') }}</p>

      <div v-if="recommendedItems.length === 0" class="empty-state">
        {{ t('restocking.noRecommendations') }}
      </div>
      <div v-else class="table-container">
        <table class="recommendations-table">
          <thead>
            <tr>
              <th>{{ t('restocking.table.sku') }}</th>
              <th>{{ t('restocking.table.itemName') }}</th>
              <th>{{ t('restocking.table.trend') }}</th>
              <th>{{ t('restocking.table.quantity') }}</th>
              <th>{{ t('restocking.table.unitCost') }}</th>
              <th>{{ t('restocking.table.subtotal') }}</th>
              <th>{{ t('restocking.table.leadTime') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in recommendedItems" :key="item.id">
              <td><strong>{{ item.item_sku }}</strong></td>
              <td>{{ item.item_name }}</td>
              <td><span :class="['badge', item.trend]">{{ t(`trends.${item.trend}`) }}</span></td>
              <td>{{ item.forecasted_demand.toLocaleString() }}</td>
              <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
              <td><strong>{{ currencySymbol }}{{ Math.round(item.subtotal).toLocaleString() }}</strong></td>
              <td>{{ item.period }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="place-order-bar">
        <button
          class="btn-place-order"
          :disabled="recommendedItems.length === 0 || submitting"
          @click="placeOrder"
        >
          {{ submitting ? t('restocking.placing') : t('restocking.placeOrder') }}
        </button>
        <div v-if="orderSuccess" class="order-success">{{ t('restocking.orderSuccess') }}</div>
        <div v-if="orderError" class="order-error">{{ orderError }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

const TREND_ORDER = { increasing: 0, stable: 1, decreasing: 2 }

// Parse "Next 30 days" → 30, "Next 3 months" → 90
function parsePeriodToDays(period) {
  const daysMatch = period.match(/(\d+)\s*days?/i)
  if (daysMatch) return parseInt(daysMatch[1])
  const monthsMatch = period.match(/(\d+)\s*months?/i)
  if (monthsMatch) return parseInt(monthsMatch[1]) * 30
  return 30
}

export default {
  name: 'Restocking',
  setup() {
    const router = useRouter()
    const { t, currentCurrency } = useI18n()
    const { selectedLocation, selectedCategory } = useFilters()

    const currencySymbol = computed(() => currentCurrency.value === 'JPY' ? '¥' : '$')

    // Both max budget and step increment are user-configurable
    const maxBudget = ref(100000)
    const stepSize = ref(5000)
    const budget = ref(50000)

    const loading = ref(true)
    const allForecasts = ref([])
    const inventoryMap = ref({})

    const submitting = ref(false)
    const orderSuccess = ref(false)
    const orderError = ref(null)

    const loadData = async () => {
      try {
        loading.value = true
        const [forecasts, inventory] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory()
        ])
        allForecasts.value = forecasts
        // SKU → inventory item map for O(1) cost lookups
        inventoryMap.value = Object.fromEntries(inventory.map(i => [i.sku, i]))
      } catch (err) {
        console.error('Failed to load restocking data:', err)
      } finally {
        loading.value = false
      }
    }

    // Enrich forecasts with unit_cost from inventory, skip items with no cost data
    const enrichedForecasts = computed(() =>
      allForecasts.value
        .map(f => {
          const inv = inventoryMap.value[f.item_sku]
          const unit_cost = inv?.unit_cost ?? 0
          return { ...f, unit_cost, subtotal: unit_cost * f.forecasted_demand }
        })
        .filter(f => f.unit_cost > 0)
        .sort((a, b) => (TREND_ORDER[a.trend] ?? 3) - (TREND_ORDER[b.trend] ?? 3))
    )

    // Greedy selection: take trend-sorted items while budget allows
    const recommendedItems = computed(() => {
      let running = 0
      return enrichedForecasts.value.filter(item => {
        if (running + item.subtotal <= budget.value) {
          running += item.subtotal
          return true
        }
        return false
      })
    })

    const totalCost = computed(() =>
      Math.round(recommendedItems.value.reduce((sum, i) => sum + i.subtotal, 0))
    )

    const remainingBudget = computed(() => budget.value - totalCost.value)

    const placeOrder = async () => {
      if (recommendedItems.value.length === 0) return

      submitting.value = true
      orderError.value = null
      orderSuccess.value = false

      try {
        // Use max lead time across all recommended items for expected delivery
        const maxDays = Math.max(...recommendedItems.value.map(i => parsePeriodToDays(i.period)))
        const deliveryDate = new Date()
        deliveryDate.setDate(deliveryDate.getDate() + maxDays)

        await api.createRestockingOrder({
          customer: 'Restocking System',
          items: recommendedItems.value.map(i => ({
            sku: i.item_sku,
            name: i.item_name,
            quantity: i.forecasted_demand,
            unit_price: i.unit_cost
          })),
          warehouse: selectedLocation.value !== 'all' ? selectedLocation.value : 'San Francisco',
          category: selectedCategory.value !== 'all' ? selectedCategory.value : null,
          expected_delivery: deliveryDate.toISOString()
        })

        orderSuccess.value = true
        setTimeout(() => router.push('/orders'), 1500)
      } catch (err) {
        orderError.value = 'Failed to place order: ' + (err.response?.data?.detail || err.message)
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadData)

    return {
      t,
      currencySymbol,
      maxBudget,
      stepSize,
      budget,
      loading,
      recommendedItems,
      totalCost,
      remainingBudget,
      submitting,
      orderSuccess,
      orderError,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-config {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.budget-inputs {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.input-group label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.number-input {
  width: 180px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.938rem;
  color: #0f172a;
  background: #f8fafc;
  transition: border-color 0.2s;
}

.number-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
}

.budget-slider-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.budget-display {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.budget-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.budget-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.budget-slider {
  width: 100%;
  max-width: 600px;
  height: 6px;
  accent-color: #2563eb;
  cursor: pointer;
}

.budget-range-labels {
  display: flex;
  justify-content: space-between;
  max-width: 600px;
  font-size: 0.813rem;
  color: #94a3b8;
}

.budget-summary {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.summary-item {
  font-size: 0.875rem;
  color: #64748b;
}

.remaining-ok strong { color: #059669; }
.remaining-over strong { color: #dc2626; }

.hint-text {
  font-size: 0.813rem;
  color: #94a3b8;
  margin-bottom: 1rem;
  font-style: italic;
}

.recommendations-table {
  table-layout: auto;
  width: 100%;
}

.empty-state {
  text-align: center;
  padding: 2.5rem;
  color: #94a3b8;
  font-size: 0.938rem;
}

.place-order-bar {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-top: 1.25rem;
  margin-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.btn-place-order {
  padding: 0.625rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
}

.btn-place-order:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-place-order:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.order-success {
  color: #059669;
  font-size: 0.938rem;
  font-weight: 500;
}

.order-error {
  color: #dc2626;
  font-size: 0.938rem;
}
</style>
