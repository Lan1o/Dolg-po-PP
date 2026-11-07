<template>
  <div>
    <div class="mb-3">
      <router-link to="/supervisor/students" class="text-decoration-none">← Назад к списку студентов</router-link>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="thesis">
      <div class="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h2 class="mb-1">{{ thesis.student_name }}</h2>
          <p class="text-muted mb-0">Тема: {{ thesis.topic_title }}</p>
        </div>
        <span class="badge bg-primary fs-6">{{ thesis.status_display }}</span>
      </div>

      <!-- Блок с описанием работы -->
      <div class="card shadow-sm mb-4">
        <div class="card-header bg-white d-flex justify-content-between align-items-center">
          <h5 class="mb-0">Детали работы</h5>
          <button class="btn btn-sm btn-outline-primary" @click="openDetailsModal">Редактировать</button>
        </div>
        <div class="card-body">
          <div class="mb-3">
            <strong>Описание:</strong>
            <p class="text-muted mb-0">{{ thesis.description || 'Не заполнено' }}</p>
          </div>
          <div class="mb-3">
            <strong>Актуальность:</strong>
            <p class="text-muted mb-0">{{ thesis.relevance || 'Не заполнено' }}</p>
          </div>
          <div class="mb-3">
            <strong>Цель:</strong>
            <p class="text-muted mb-0">{{ thesis.goal || 'Не заполнено' }}</p>
          </div>
          <div>
            <strong>Ожидаемый результат:</strong>
            <p class="text-muted mb-0">{{ thesis.expected_result || 'Не заполнено' }}</p>
          </div>
        </div>
      </div>

      <div class="row">
        <!-- Левая колонка: Этапы -->
        <div class="col-md-6">
          <h4 class="mb-3">Этапы работы</h4>
          <div class="card shadow-sm">
            <ul class="list-group list-group-flush">
              <li v-for="stage in thesis.stages" :key="stage.id" class="list-group-item">
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <strong>{{ stage.type_display }}</strong>
                    <div class="small text-muted">Дедлайн: {{ formatDate(stage.deadline) }}</div>
                  </div>
                  <div class="d-flex gap-2 align-items-center">
                    <span :class="getStatusBadgeClass(stage.status)" class="badge">{{ stage.status_display }}</span>
                    <button class="btn btn-sm btn-outline-secondary" @click="openDeadlineModal(stage)" title="Изменить дедлайн">
                      ✎
                    </button>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <!-- Правая колонка: История действий -->
        <div class="col-md-6">
          <h4 class="mb-3">История взаимодействий</h4>
          <div class="card shadow-sm p-3">
            <div v-if="history.length === 0" class="text-muted small">История пуста.</div>
            <div v-else class="timeline">
              <div v-for="log in history" :key="log.id" class="mb-3 pb-3 border-bottom">
                <div class="d-flex justify-content-between small text-muted mb-1">
                  <span>{{ formatDate(log.created_at) }}</span>
                  <span class="badge bg-secondary">{{ log.entity_type }}</span>
                </div>
                <div>{{ log.action }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка изменения дедлайна -->
    <div v-if="showDeadlineModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Дедлайн для этапа: {{ selectedStage?.type_display }}</h5>
            <button type="button" class="btn-close" @click="closeDeadlineModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Новая дата</label>
              <input v-model="newDeadline" type="date" class="form-control" />
            </div>
            <div v-if="modalError" class="alert alert-danger py-2 small">{{ modalError }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeDeadlineModal">Отмена</button>
            <button type="button" class="btn btn-primary" @click="saveDeadline" :disabled="savingDeadline">
              {{ savingDeadline ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка редактирования деталей работы -->
    <div v-if="showDetailsModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Редактировать детали ВКР</h5>
            <button type="button" class="btn-close" @click="closeDetailsModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Описание работы</label>
              <textarea v-model="detailsForm.description" class="form-control" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Актуальность</label>
              <textarea v-model="detailsForm.relevance" class="form-control" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Цель работы</label>
              <textarea v-model="detailsForm.goal" class="form-control" rows="3"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Ожидаемый результат</label>
              <textarea v-model="detailsForm.expected_result" class="form-control" rows="3"></textarea>
            </div>
            <div v-if="detailsError" class="alert alert-danger py-2 small">{{ detailsError }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeDetailsModal">Отмена</button>
            <button type="button" class="btn btn-primary" @click="saveDetails" :disabled="savingDetails">
              {{ savingDetails ? 'Сохранение...' : 'Сохранить' }}
            </button>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const thesisId = route.params.id

const thesis = ref(null)
const history = ref([])
const loading = ref(true)

// Модалка дедлайна
const showDeadlineModal = ref(false)
const selectedStage = ref(null)
const newDeadline = ref('')
const savingDeadline = ref(false)
const modalError = ref('')

// Модалка деталей
const showDetailsModal = ref(false)
const detailsForm = ref({ description: '', relevance: '', goal: '', expected_result: '' })
const savingDetails = ref(false)
const detailsError = ref('')

const getStatusBadgeClass = (status) => {
  if (status === 'approved') return 'bg-success'
  if (status === 'submitted') return 'bg-info text-dark'
  if (status === 'in_progress') return 'bg-primary'
  if (status === 'needs_revision') return 'bg-warning text-dark'
  return 'bg-secondary'
}

const formatDate = (isoString) => {
  if (!isoString) return 'Нет'
  return new Date(isoString).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const fetchData = async () => {
  loading.value = true
  try {
    const thesisData = await api(`/theses/${thesisId}/`)
    thesis.value = thesisData
    
    const historyData = await api(`/theses/${thesisId}/history/`)
    history.value = historyData
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

// --- Дедлайны ---
const openDeadlineModal = (stage) => {
  selectedStage.value = stage
  newDeadline.value = stage.deadline ? stage.deadline.split('T')[0] : ''
  modalError.value = ''
  showDeadlineModal.value = true
}

const closeDeadlineModal = () => {
  showDeadlineModal.value = false
  selectedStage.value = null
}

const saveDeadline = async () => {
  if (!newDeadline.value) {
    modalError.value = 'Выберите дату'
    return
  }
  savingDeadline.value = true
  modalError.value = ''
  try {
    await api(`/stages/${selectedStage.value.id}/`, {
      method: 'PATCH',
      body: JSON.stringify({ deadline: newDeadline.value })
    })
    closeDeadlineModal()
    fetchData()
  } catch (err) {
    modalError.value = err.message
  } finally {
    savingDeadline.value = false
  }
}

// --- Детали работы ---
const openDetailsModal = () => {
  detailsForm.value = {
    description: thesis.value.description || '',
    relevance: thesis.value.relevance || '',
    goal: thesis.value.goal || '',
    expected_result: thesis.value.expected_result || ''
  }
  detailsError.value = ''
  showDetailsModal.value = true
}

const closeDetailsModal = () => {
  showDetailsModal.value = false
}

const saveDetails = async () => {
  savingDetails.value = true
  detailsError.value = ''
  try {
    await api(`/theses/${thesisId}/`, {
      method: 'PATCH',
      body: JSON.stringify(detailsForm.value)
    })
    closeDetailsModal()
    fetchData()
  } catch (err) {
    detailsError.value = err.message
  } finally {
    savingDetails.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>