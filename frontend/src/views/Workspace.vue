<template>
  <div>
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2 text-muted">Загрузка данных ВКР...</p>
    </div>

    <div v-else-if="!thesis" class="text-center py-5">
      <h4 class="text-muted">У вас пока нет активной ВКР</h4>
      <p class="text-muted">Для начала работы необходимо подать заявку и дождаться её одобрения руководителем.</p>
      <router-link to="/catalog" class="btn btn-primary mt-3">Перейти в каталог тем</router-link>
    </div>

    <div v-else>
      <!-- Шапка ВКР -->
      <div class="card mb-4 shadow-sm border-0">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start">
            <div>
              <h3 class="mb-1">{{ thesis.topic.title }}</h3>
              <p class="text-muted mb-0">
                <strong>Руководитель:</strong> {{ thesis.supervisor_name }}<br>
                <strong>Статус работы:</strong> <span class="badge bg-primary">{{ thesis.status_display }}</span>
              </p>
            </div>
          </div>
          
          <!-- Блок с описанием -->
          <div class="mt-4 p-3 bg-light rounded position-relative">
            <button class="btn btn-sm btn-outline-primary position-absolute top-0 end-0 m-3" @click="openDetailsModal">
              Редактировать
            </button>
            <h6 class="text-uppercase text-muted mb-3">Детали работы</h6>
            
            <div v-if="thesis.description || thesis.goal || thesis.relevance || thesis.expected_result">
              <div v-if="thesis.description" class="mb-2">
                <strong>Описание:</strong> <span class="text-muted">{{ thesis.description }}</span>
              </div>
              <div v-if="thesis.relevance" class="mb-2">
                <strong>Актуальность:</strong> <span class="text-muted">{{ thesis.relevance }}</span>
              </div>
              <div v-if="thesis.goal" class="mb-2">
                <strong>Цель:</strong> <span class="text-muted">{{ thesis.goal }}</span>
              </div>
              <div v-if="thesis.expected_result">
                <strong>Ожидаемый результат:</strong> <span class="text-muted">{{ thesis.expected_result }}</span>
              </div>
            </div>
            <div v-else class="text-muted small">
              Вы еще не заполнили детали работы. Нажмите «Редактировать», чтобы указать цель, актуальность и ожидаемый результат.
            </div>
          </div>

          <!-- Прогресс-бар -->
          <div class="mt-4">
            <div class="d-flex justify-content-between small text-muted mb-1">
              <span>Общий прогресс</span>
              <span>{{ progressPercent }}% ({{ approvedStagesCount }} из {{ thesis.stages.length }} этапов)</span>
            </div>
            <div class="progress" style="height: 10px;">
              <div class="progress-bar bg-success" role="progressbar" :style="{ width: progressPercent + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <!-- Левая колонка: Этапы -->
        <div class="col-md-7">
          <h4 class="mb-3">Этапы работы</h4>
          <div class="timeline">
            <div 
              v-for="(stage, index) in thesis.stages" 
              :key="stage.id" 
              class="card mb-3 stage-card"
              :class="{'border-primary': stage.status === 'in_progress' || stage.status === 'submitted'}"
            >
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                  <h5 class="mb-0">
                    <span class="badge bg-light text-dark border me-2">{{ index + 1 }}</span>
                    {{ stage.type_display }}
                  </h5>
                  <span :class="getStatusBadgeClass(stage.status)" class="badge">
                    {{ stage.status_display }}
                  </span>
                </div>

                <div class="mt-3 text-muted small">
                  <strong>Дедлайн:</strong> <span :class="{'text-danger': isDeadlineSoon(stage.deadline)}">{{ formatDate(stage.deadline) }}</span>
                </div>

                <!-- Кнопки действий -->
                <div class="mt-3 d-flex gap-2">
                  <button 
                    class="btn btn-sm btn-outline-primary"
                    @click="openUploadModal(stage)"
                    :disabled="stage.status === 'approved'"
                  >
                    Загрузить файл
                  </button>
                </div>

                <!-- Список отзывов (если есть) -->
                <div v-if="stageReviews[stage.id] && stageReviews[stage.id].length > 0" class="mt-3 pt-3 border-top">
                  <p class="small text-muted mb-2"><strong>Отзывы руководителя:</strong></p>
                  <div v-for="review in stageReviews[stage.id]" :key="review.id" class="alert alert-info py-2 px-3 mb-2 small">
                    <div class="d-flex justify-content-between mb-1">
                      <strong :class="review.decision === 'approved' ? 'text-success' : 'text-danger'">
                        {{ review.decision === 'approved' ? 'Одобрено' : 'Доработать' }}
                      </strong>
                      <span class="text-muted">{{ formatDate(review.created_at) }}</span>
                    </div>
                    {{ review.text }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Правая колонка: История -->
        <div class="col-md-5">
          <h4 class="mb-3">История взаимодействий</h4>
          <div class="card shadow-sm p-3">
            <div v-if="history.length === 0" class="text-muted small">История пуста.</div>
            <div v-else>
              <div v-for="log in history" :key="log.id" class="mb-3 pb-3 border-bottom">
                <div class="d-flex justify-content-between small text-muted mb-1">
                  <span>{{ formatDate(log.created_at) }}</span>
                  <span class="badge bg-secondary">{{ log.entity_type }}</span>
                </div>
                <div class="small">{{ log.action }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка загрузки файла -->
    <div v-if="showUploadModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Загрузка файла: {{ selectedStage?.type_display }}</h5>
            <button type="button" class="btn-close" @click="closeUploadModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Выберите файл</label>
              <input type="file" class="form-control" @change="handleFileChange" />
            </div>
            <div v-if="uploadError" class="alert alert-danger py-2 small">{{ uploadError }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeUploadModal">Отмена</button>
            <button type="button" class="btn btn-primary" @click="submitFile" :disabled="uploading || !selectedFile">
              {{ uploading ? 'Загрузка...' : 'Загрузить на проверку' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка редактирования деталей ВКР -->
    <div v-if="showDetailsModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Детали ВКР</h5>
            <button type="button" class="btn-close" @click="closeDetailsModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Описание работы</label>
              <textarea v-model="detailsForm.description" class="form-control" rows="3" placeholder="Кратко опишите, что будете делать"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Актуальность</label>
              <textarea v-model="detailsForm.relevance" class="form-control" rows="3" placeholder="Почему эта тема важна сейчас?"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Цель работы</label>
              <textarea v-model="detailsForm.goal" class="form-control" rows="3" placeholder="Какую проблему вы хотите решить?"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Ожидаемый результат</label>
              <textarea v-model="detailsForm.expected_result" class="form-control" rows="3" placeholder="Что должно получиться в итоге?"></textarea>
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
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'

const thesis = ref(null)
const history = ref([])
const loading = ref(true)
const stageReviews = ref({})

// Загрузка файла
const showUploadModal = ref(false)
const selectedStage = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadError = ref('')

// Редактирование деталей ВКР
const showDetailsModal = ref(false)
const detailsForm = ref({ description: '', relevance: '', goal: '', expected_result: '' })
const savingDetails = ref(false)
const detailsError = ref('')

// Вычисляем прогресс
const approvedStagesCount = computed(() => {
  if (!thesis.value) return 0
  return thesis.value.stages.filter(s => s.status === 'approved').length
})

const progressPercent = computed(() => {
  if (!thesis.value) return 0
  const total = thesis.value.stages.length
  if (total === 0) return 0
  return Math.round((approvedStagesCount.value / total) * 100)
})

const getStatusBadgeClass = (status) => {
  if (status === 'approved') return 'bg-success'
  if (status === 'submitted') return 'bg-info text-dark'
  if (status === 'in_progress') return 'bg-primary'
  if (status === 'needs_revision') return 'bg-warning text-dark'
  return 'bg-secondary'
}

const formatDate = (dateString) => {
  if (!dateString) return 'Не указан'
  return new Date(dateString).toLocaleDateString('ru-RU')
}

// Проверка, не горит ли дедлайн (меньше 3 дней)
const isDeadlineSoon = (dateString) => {
  if (!dateString) return false
  const deadline = new Date(dateString)
  const today = new Date()
  const diffTime = deadline - today
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays >= 0 && diffDays <= 3
}

const fetchData = async () => {
  loading.value = true
  try {
    // 1. Получаем ВКР
    const data = await api('/theses/my/')
    thesis.value = data
    
    if (data && data.stages) {
      // 2. Получаем отзывы для каждого этапа
      for (const stage of data.stages) {
        fetchReviews(stage.id)
      }
      // 3. Получаем историю
      const historyData = await api(`/theses/${data.id}/history/`)
      history.value = historyData
    }
  } catch (error) {
    if (error.message.includes('404')) {
      thesis.value = null
    } else {
      console.error('Ошибка загрузки ВКР:', error)
    }
  } finally {
    loading.value = false
  }
}

const fetchReviews = async (stageId) => {
  try {
    const data = await api(`/stages/${stageId}/reviews/`)
    stageReviews.value[stageId] = data
  } catch (error) {
    console.error('Ошибка загрузки отзывов:', error)
  }
}

// Загрузка файла
const openUploadModal = (stage) => {
  selectedStage.value = stage
  selectedFile.value = null
  uploadError.value = ''
  showUploadModal.value = true
}

const closeUploadModal = () => {
  showUploadModal.value = false
  selectedStage.value = null
}

const handleFileChange = (e) => {
  selectedFile.value = e.target.files[0]
}

const submitFile = async () => {
  if (!selectedFile.value) return
  uploading.value = true
  uploadError.value = ''

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('file_name', selectedFile.value.name)

  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/stages/${selectedStage.value.id}/upload/`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Ошибка загрузки файла')
    }

    closeUploadModal()
    alert('Файл успешно загружен и отправлен на проверку!')
    fetchData() // Обновляем всё
  } catch (error) {
    uploadError.value = error.message
  } finally {
    uploading.value = false
  }
}

// Редактирование деталей ВКР
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
    await api(`/theses/${thesis.value.id}/`, {
      method: 'PATCH',
      body: JSON.stringify(detailsForm.value)
    })
    closeDetailsModal()
    fetchData() // Обновляем данные, чтобы отобразились новые тексты
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

<style scoped>
.stage-card {
  transition: all 0.2s;
}
.stage-card:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
</style>