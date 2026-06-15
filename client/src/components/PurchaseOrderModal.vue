<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.titleView') : t('purchaseOrder.titleCreate') }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Item header -->
            <div class="item-header">
              <div class="item-icon">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                  <rect x="3" y="7" width="22" height="16" rx="2" stroke="currentColor" stroke-width="2"/>
                  <path d="M9 7V5a5 5 0 0 1 10 0v2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
              </div>
              <div class="item-title-section">
                <h4 class="item-name">{{ backlogItem.item_name }}</h4>
                <div class="item-sku">{{ t('purchaseOrder.sku') }}: {{ backlogItem.item_sku }}</div>
              </div>
              <span class="priority-badge" :class="backlogItem.priority">
                {{ backlogItem.priority }} {{ t('purchaseOrder.priority') }}
              </span>
            </div>

            <!-- View mode: read-only PO details -->
            <template v-if="mode === 'view' && backlogItem.purchase_order">
              <div class="section-label">{{ t('purchaseOrder.section.details') }}</div>
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.labels.poId') }}</div>
                  <div class="info-value mono">{{ backlogItem.purchase_order.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.labels.status') }}</div>
                  <div class="info-value">
                    <span class="badge" :class="statusClass(backlogItem.purchase_order.status)">
                      {{ backlogItem.purchase_order.status }}
                    </span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.labels.supplier') }}</div>
                  <div class="info-value">{{ backlogItem.purchase_order.supplier }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.labels.quantity') }}</div>
                  <div class="info-value">{{ backlogItem.purchase_order.quantity }} {{ t('purchaseOrder.labels.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.labels.unitCost') }}</div>
                  <div class="info-value">${{ Number(backlogItem.purchase_order.unitCost).toFixed(2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.labels.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(backlogItem.purchase_order.expectedDelivery) }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode: form -->
            <template v-else-if="mode === 'create'">
              <div class="section-label">{{ t('purchaseOrder.section.newOrder') }}</div>
              <form class="po-form" @submit.prevent="submitForm">
                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label" for="po-supplier">{{ t('purchaseOrder.form.supplier') }}</label>
                    <input
                      id="po-supplier"
                      v-model="form.supplier"
                      type="text"
                      class="form-input"
                      :placeholder="t('purchaseOrder.form.supplierPlaceholder')"
                      required
                    />
                  </div>
                </div>

                <div class="form-row two-col">
                  <div class="form-group">
                    <label class="form-label" for="po-quantity">{{ t('purchaseOrder.form.quantity') }}</label>
                    <input
                      id="po-quantity"
                      v-model.number="form.quantity"
                      type="number"
                      min="1"
                      class="form-input"
                      required
                    />
                  </div>
                  <div class="form-group">
                    <label class="form-label" for="po-unit-cost">Unit Cost ($)</label>
                    <input
                      id="po-unit-cost"
                      v-model.number="form.unitCost"
                      type="number"
                      min="0"
                      step="0.01"
                      class="form-input"
                      placeholder="0.00"
                      required
                    />
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label class="form-label" for="po-delivery">Expected Delivery Date</label>
                    <input
                      id="po-delivery"
                      v-model="form.expectedDelivery"
                      type="date"
                      class="form-input"
                      required
                    />
                  </div>
                </div>

                <!-- Total cost preview -->
                <div v-if="totalCost > 0" class="cost-preview">
                  <span class="cost-label">Total Order Cost</span>
                  <span class="cost-value">${{ totalCost.toFixed(2) }}</span>
                </div>
              </form>
            </template>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">Close</button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              :disabled="!formValid"
              @click="submitForm"
            >
              Create Purchase Order
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from '../composables/useI18n'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    default: 'create'
  }
})

const emit = defineEmits(['close', 'po-created'])

const { t } = useI18n()

// Form state — reset when modal opens or backlogItem changes
const form = ref({
  supplier: '',
  quantity: 0,
  unitCost: '',
  expectedDelivery: ''
})

// Pre-fill quantity from the backlog item whenever the modal opens
watch(
  () => [props.isOpen, props.backlogItem],
  ([open, item]) => {
    if (open && item && props.mode === 'create') {
      // quantity_needed represents the units short; default to the shortage amount
      const shortage = (item.quantity_needed ?? 0) - (item.quantity_available ?? 0)
      form.value = {
        supplier: '',
        quantity: shortage > 0 ? shortage : item.quantity_needed ?? 1,
        unitCost: '',
        expectedDelivery: ''
      }
    }
  },
  { immediate: true }
)

const totalCost = computed(() => {
  const qty = Number(form.value.quantity)
  const cost = Number(form.value.unitCost)
  if (!qty || !cost) return 0
  return qty * cost
})

const formValid = computed(() => {
  return (
    form.value.supplier.trim().length > 0 &&
    Number(form.value.quantity) > 0 &&
    Number(form.value.unitCost) > 0 &&
    form.value.expectedDelivery.length > 0
  )
})

const submitForm = () => {
  if (!formValid.value) return

  // Emit a PO object that satisfies handlePOCreated: { id, backlog_item_id, ... }
  const poData = {
    id: 'PO-' + Date.now(),
    backlog_item_id: props.backlogItem.id,
    supplier: form.value.supplier.trim(),
    quantity: Number(form.value.quantity),
    unitCost: Number(form.value.unitCost),
    expectedDelivery: form.value.expectedDelivery,
    status: 'Pending'
  }

  emit('po-created', poData)
}

const close = () => {
  emit('close')
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return dateString
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const statusClass = (status) => {
  if (!status) return ''
  const s = status.toLowerCase()
  if (s === 'pending') return 'warning'
  if (s === 'approved' || s === 'delivered') return 'success'
  if (s === 'cancelled') return 'danger'
  return 'info'
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

/* Item header */
.item-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.item-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.item-title-section {
  flex: 1;
  min-width: 0;
}

.item-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 0.375rem 0;
}

.item-sku {
  font-size: 0.875rem;
  color: #64748b;
  font-family: 'Monaco', 'Courier New', monospace;
}

/* Priority badge */
.priority-badge {
  padding: 0.375rem 0.875rem;
  border-radius: 6px;
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  flex-shrink: 0;
}

.priority-badge.high {
  background: #fecaca;
  color: #991b1b;
}

.priority-badge.medium {
  background: #fed7aa;
  color: #92400e;
}

.priority-badge.low {
  background: #dbeafe;
  color: #1e40af;
}

/* Section label */
.section-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin-bottom: 1.25rem;
}

/* Info grid (view mode) */
.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1.25rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
}

/* Status badge */
.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.813rem;
  font-weight: 600;
}

.badge.success {
  background: #dcfce7;
  color: #166534;
}

.badge.warning {
  background: #fef9c3;
  color: #854d0e;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

/* Form (create mode) */
.po-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-row {
  display: flex;
  gap: 1rem;
}

.form-row.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.form-label {
  font-size: 0.813rem;
  font-weight: 600;
  color: #374151;
}

.form-input {
  padding: 0.625rem 0.875rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.938rem;
  color: #0f172a;
  font-family: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  background: #fff;
}

.form-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-input::placeholder {
  color: #94a3b8;
}

/* Total cost preview */
.cost-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin-top: 0.25rem;
}

.cost-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.cost-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

/* Footer */
.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

.btn-primary {
  padding: 0.625rem 1.25rem;
  background: #2563eb;
  border: 1px solid transparent;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  color: white;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal transition animations — identical to BacklogDetailModal */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
