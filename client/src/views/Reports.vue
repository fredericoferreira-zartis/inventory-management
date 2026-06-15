<template>
  <div class="reports">
    <div class="page-header">
      <div>
        <h2>{{ t('reports.title') }}</h2>
        <p>{{ t('reports.subtitle') }}</p>
      </div>
      <button class="export-btn" @click="exportReport">{{ t('reports.exportCsv') }}</button>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div v-for="kpi in kpiData" :key="kpi.id" class="kpi-card">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-trend" :class="kpi.trend >= 0 ? 'trend-up' : 'trend-down'">
            {{ kpi.trend >= 0 ? '+' : '' }}{{ kpi.trend }}%
          </div>
        </div>
      </div>

      <div class="charts-grid">
        <!-- Revenue vs Target -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.revenueVsTarget') }}</h3>
          </div>
          <div class="chart-container">
            <div class="bar-chart">
              <div
                v-for="month in monthlyRevenueData"
                :key="month.month"
                class="bar-wrapper"
              >
                <div class="bar-container">
                  <div
                    class="bar bar-target"
                    :style="{ height: getBarHeight(month.target) + 'px' }"
                    :title="t('reports.target') + ': $' + formatNumber(month.target)"
                  ></div>
                  <div
                    class="bar bar-revenue"
                    :style="{ height: getBarHeight(month.revenue) + 'px' }"
                    :title="t('reports.revenue') + ': $' + formatNumber(month.revenue)"
                  ></div>
                </div>
                <div class="bar-label">{{ month.month }}</div>
              </div>
            </div>
            <div class="chart-legend">
              <span class="legend-item"><span class="legend-dot dot-revenue"></span>{{ t('reports.revenue') }}</span>
              <span class="legend-item"><span class="legend-dot dot-target"></span>{{ t('reports.target') }}</span>
            </div>
          </div>
        </div>

        <!-- Inventory Health -->
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('reports.inventoryHealth') }}</h3>
          </div>
          <div class="health-container">
            <div class="health-item">
              <div class="health-label">{{ t('reports.healthy') }}</div>
              <div class="health-bar-wrap">
                <div
                  class="health-bar health-bar-healthy"
                  :style="{ width: healthPercent(inventoryHealth.healthy) + '%' }"
                ></div>
              </div>
              <div class="health-count">{{ inventoryHealth.healthy }} {{ t('reports.items') }}</div>
            </div>
            <div class="health-item">
              <div class="health-label">{{ t('reports.lowStock') }}</div>
              <div class="health-bar-wrap">
                <div
                  class="health-bar health-bar-low"
                  :style="{ width: healthPercent(inventoryHealth.lowStock) + '%' }"
                ></div>
              </div>
              <div class="health-count">{{ inventoryHealth.lowStock }} {{ t('reports.items') }}</div>
            </div>
            <div class="health-item">
              <div class="health-label">{{ t('reports.critical') }}</div>
              <div class="health-bar-wrap">
                <div
                  class="health-bar health-bar-critical"
                  :style="{ width: healthPercent(inventoryHealth.critical) + '%' }"
                ></div>
              </div>
              <div class="health-count">{{ inventoryHealth.critical }} {{ t('reports.items') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Performing Products -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.topProducts') }}</h3>
        </div>
        <div class="table-container">
          <table class="reports-table">
            <thead>
              <tr>
                <th>{{ t('reports.table.product') }}</th>
                <th>{{ t('reports.table.sku') }}</th>
                <th>{{ t('reports.table.unitsSold') }}</th>
                <th>{{ t('reports.table.revenue') }}</th>
                <th>{{ t('reports.table.margin') }}</th>
                <th>{{ t('reports.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="product in topProducts" :key="product.sku">
                <td><strong>{{ product.name }}</strong></td>
                <td>{{ product.sku }}</td>
                <td>{{ product.unitsSold }}</td>
                <td>${{ formatNumber(product.revenue) }}</td>
                <td>{{ product.margin }}%</td>
                <td>
                  <span :class="['badge', getStatusClass(product.status)]">
                    {{ product.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('reports.recentActivity') }}</h3>
        </div>
        <div class="activity-list">
          <div v-for="activity in activityLog" :key="activity.id" class="activity-item">
            <div class="activity-content">
              <div class="activity-title">{{ activity.title }}</div>
              <div class="activity-time">{{ activity.time }}</div>
            </div>
            <span :class="['badge', activity.badgeClass]">{{ activity.badge }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { useFilters } from '../composables/useFilters'

export default {
  name: 'Reports',
  setup() {
    const { t } = useI18n()
    const { selectedPeriod, selectedLocation, selectedCategory } = useFilters()

    const loading = ref(true)
    const error = ref(null)
    const inventoryData = ref([])
    const ordersData = ref([])

    // Inventory health derived from inventory data
    const inventoryHealth = computed(() => {
      const healthy = inventoryData.value.filter(
        item => item.quantity_on_hand > item.reorder_point * 1.5
      ).length
      const lowStock = inventoryData.value.filter(
        item => item.quantity_on_hand > 0 && item.quantity_on_hand <= item.reorder_point * 1.5
      ).length
      // Critical: quantity at or below reorder point (or zero)
      const critical = inventoryData.value.filter(
        item => item.quantity_on_hand <= item.reorder_point
      ).length
      return { healthy, lowStock, critical }
    })

    // Bug 6: kpiData as computed so labels re-evaluate on locale change
    const kpiData = computed(() => [
      {
        id: 1,
        label: t('reports.kpi.totalRevenue'),
        value: '$2.4M',
        trend: 12
      },
      {
        id: 2,
        label: t('reports.kpi.ordersFulfilled'),
        value: ordersData.value.filter(o => o.status === 'Delivered').length.toLocaleString(),
        trend: 8
      },
      {
        id: 3,
        label: t('reports.kpi.lowStockAlerts'),
        value: inventoryHealth.value.critical.toString(),
        trend: -5
      },
      {
        id: 4,
        label: t('reports.kpi.inventoryTurnover'),
        value: '4.2x',
        trend: 3
      }
    ])

    // Monthly revenue vs target derived from orders data
    const monthlyRevenueData = computed(() => {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      // Monthly target: $800K
      const monthlyTarget = 800000
      const monthMap = {}
      monthNames.forEach(m => { monthMap[m] = { month: m, revenue: 0, target: monthlyTarget } })

      ordersData.value.forEach(order => {
        if (!order.order_date) return
        const date = new Date(order.order_date)
        if (isNaN(date.getTime())) return
        const monthName = monthNames[date.getMonth()]
        monthMap[monthName].revenue += order.total_value || 0
      })

      return monthNames.map(m => monthMap[m])
    })

    const maxBarValue = computed(() => {
      const allValues = monthlyRevenueData.value.flatMap(m => [m.revenue, m.target])
      return Math.max(...allValues, 1)
    })

    // Top products derived from orders data
    const topProducts = computed(() => {
      const productMap = {}

      ordersData.value.forEach(order => {
        if (!order.items) return
        order.items.forEach(item => {
          const sku = item.sku
          if (!productMap[sku]) {
            // Find inventory item for stock status
            const invItem = inventoryData.value.find(i => i.sku === sku)
            const status = invItem
              ? (invItem.quantity_on_hand > invItem.reorder_point ? 'In Stock' : 'Low Stock')
              : 'Unknown'
            productMap[sku] = {
              name: item.name,
              sku,
              unitsSold: 0,
              revenue: 0,
              unitCost: invItem ? invItem.unit_cost : item.unit_price * 0.6,
              status
            }
          }
          productMap[sku].unitsSold += item.quantity
          productMap[sku].revenue += item.quantity * item.unit_price
        })
      })

      return Object.values(productMap)
        .map(p => ({
          ...p,
          revenue: Math.round(p.revenue),
          // Margin: (revenue - cost) / revenue * 100, estimated from unit cost
          margin: p.revenue > 0
            ? Math.round(((p.revenue - p.unitsSold * p.unitCost) / p.revenue) * 100)
            : 0
        }))
        .sort((a, b) => b.revenue - a.revenue)
        .slice(0, 10)
    })

    // Recent activity derived from the most recent orders
    const activityLog = computed(() => {
      const recent = [...ordersData.value]
        .filter(o => o.order_date)
        .sort((a, b) => new Date(b.order_date) - new Date(a.order_date))
        .slice(0, 5)

      return recent.map((order, idx) => {
        const statusClassMap = {
          Delivered: 'success',
          Shipped: 'info',
          Processing: 'warning',
          Backordered: 'danger',
          Submitted: 'info'
        }
        return {
          id: order.id || idx,
          title: `Order ${order.order_number || order.id} — ${order.customer || ''}`,
          time: order.order_date,
          badge: order.status,
          badgeClass: statusClassMap[order.status] || 'info'
        }
      })
    })

    const loadData = async () => {
      loading.value = true
      // Bug 8: reset error before each load attempt
      error.value = null
      try {
        const [fetchedInventory, fetchedOrders] = await Promise.all([
          api.getInventory({
            warehouse: selectedLocation.value,
            category: selectedCategory.value
          }),
          api.getOrders({
            warehouse: selectedLocation.value,
            category: selectedCategory.value,
            month: selectedPeriod.value
          })
        ])
        inventoryData.value = fetchedInventory
        ordersData.value = fetchedOrders
      } catch (err) {
        // Bug 3: only console.error for real errors, no console.log spam
        console.error('Failed to load reports data:', err)
        // Bug 8: assign to the exposed error ref
        error.value = err.message
      } finally {
        loading.value = false
      }
    }

    watch([selectedPeriod, selectedLocation, selectedCategory], loadData)

    onMounted(loadData)

    // --- Helper functions ---

    const formatNumber = (num) => {
      if (num == null || isNaN(num)) return '0.00'
      return Number(num).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    const getBarHeight = (value) => {
      // Max bar height 160px
      return maxBarValue.value > 0 ? Math.round((value / maxBarValue.value) * 160) : 0
    }

    const healthPercent = (count) => {
      const total = inventoryData.value.length
      return total > 0 ? Math.round((count / total) * 100) : 0
    }

    const getStatusClass = (status) => {
      if (status === 'In Stock') return 'success'
      if (status === 'Low Stock') return 'warning'
      return 'danger'
    }

    const exportReport = () => {
      // Build CSV from topProducts data
      const headers = [
        t('reports.table.product'),
        t('reports.table.sku'),
        t('reports.table.unitsSold'),
        t('reports.table.revenue'),
        t('reports.table.margin'),
        t('reports.table.status')
      ]
      const rows = topProducts.value.map(p => [
        `"${p.name}"`,
        p.sku,
        p.unitsSold,
        p.revenue,
        p.margin,
        p.status
      ])
      const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'reports.csv'
      a.click()
      URL.revokeObjectURL(url)
    }

    return {
      t,
      loading,
      error,
      kpiData,
      inventoryHealth,
      monthlyRevenueData,
      topProducts,
      activityLog,
      formatNumber,
      getBarHeight,
      healthPercent,
      getStatusClass,
      exportReport
    }
  }
}
</script>

<style scoped>
.reports {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.page-header p {
  margin: 0;
  color: #64748b;
  font-size: 0.875rem;
}

.export-btn {
  padding: 0.5rem 1.25rem;
  background: #0f172a;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.export-btn:hover {
  background: #1e293b;
}

/* KPI Grid */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.kpi-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.kpi-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 0.5rem;
}

.kpi-value {
  font-size: 2rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  margin-bottom: 0.25rem;
}

.kpi-trend {
  font-size: 0.813rem;
  font-weight: 600;
}

.trend-up {
  color: #16a34a;
}

.trend-down {
  color: #dc2626;
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.card:last-child {
  margin-bottom: 0;
}

.card-header {
  margin-bottom: 1.25rem;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

/* Bar Chart */
.chart-container {
  padding: 0.5rem 0;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  height: 200px;
  gap: 0.25rem;
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bar-container {
  height: 160px;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  width: 100%;
  justify-content: center;
}

.bar {
  width: 45%;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
  cursor: pointer;
  min-height: 2px;
}

.bar-revenue {
  background: #3b82f6;
}

.bar-revenue:hover {
  background: #2563eb;
}

.bar-target {
  background: #e2e8f0;
}

.bar-target:hover {
  background: #cbd5e1;
}

.bar-label {
  margin-top: 1.5rem;
  font-size: 0.7rem;
  color: #64748b;
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.chart-legend {
  display: flex;
  gap: 1.5rem;
  margin-top: 2rem;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.813rem;
  color: #475569;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.dot-revenue {
  background: #3b82f6;
}

.dot-target {
  background: #e2e8f0;
  border: 1px solid #cbd5e1;
}

/* Inventory Health */
.health-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.health-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.health-label {
  width: 80px;
  min-width: 80px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #475569;
}

.health-bar-wrap {
  flex: 1;
  height: 20px;
  background: #f1f5f9;
  border-radius: 4px;
  overflow: hidden;
}

.health-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s;
}

.health-bar-healthy {
  background: #10b981;
}

.health-bar-low {
  background: #f59e0b;
}

.health-bar-critical {
  background: #ef4444;
}

.health-count {
  width: 80px;
  font-size: 0.813rem;
  color: #64748b;
  text-align: right;
}

/* Table */
.table-container {
  overflow-x: auto;
}

.reports-table {
  width: 100%;
  border-collapse: collapse;
}

.reports-table th {
  background: #f8fafc;
  padding: 0.75rem;
  text-align: left;
  font-weight: 600;
  color: #64748b;
  border-bottom: 2px solid #e2e8f0;
  font-size: 0.813rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.reports-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.875rem;
}

.reports-table tr:last-child td {
  border-bottom: none;
}

.reports-table tr:hover td {
  background: #f8fafc;
}

/* Activity Log */
.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.activity-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 0;
  border-bottom: 1px solid #f1f5f9;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #0f172a;
}

.activity-time {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-top: 0.2rem;
}

/* Badges */
.badge {
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge.success {
  background: #dcfce7;
  color: #166534;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

/* State messages */
.loading {
  text-align: center;
  padding: 3rem;
  color: #64748b;
}

.error {
  background: #fee2e2;
  color: #991b1b;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}
</style>
