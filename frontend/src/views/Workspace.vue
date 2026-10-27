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
        </div>
      </div>

      <!-- Таймлайн этапов -->
      <h4 class="mb-3">Этапы работы</h4>
      <div class="row">
        <div class="col-md-8">
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
                  <strong>Дедлайн:</strong> {{ formatDate(stage.deadline) }}
                </div>

                <!-- Кнопки действий -->
                <div class="mt-3 d-flex gap-2">
                  <!-- Загрузка файла -->
                  <button 
                    class="btn btn-sm btn-outline-primary"
                    @click="openUploadModal(stage)"
                    :disabled="stage.status === 'approved'"
                  >
                    <i class="bi bi-upload"></i> Загрузить файл
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
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const thesis = ref(null)
const loading = ref(true)
const stageReviews = ref({})

// Загрузка файла
const showUploadModal = ref(false)
const selectedStage = ref(null)
const selectedFile = ref(null)
const uploading = ref(false)
const uploadError = ref('')

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

// Получение данных ВКР
const fetchThesis = async () => {
  loading.value = true
  try {
    const data = await api('/theses/my/')
    thesis.value = data
    if (data && data.stages) {
      // Загружаем отзывы для каждого этапа
      for (const stage of data.stages) {
        fetchReviews(stage.id)
      }
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

// Получение отзывов конкретного этапа
const fetchReviews = async (stageId) => {
  try {
    const data = await api(`/stages/${stageId}/reviews/`)
    stageReviews.value[stageId] = data
  } catch (error) {
    console.error('Ошибка загрузки отзывов:', error)
  }
}

// Работа с загрузкой файла
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
    // Внимание: здесь мы передаём FormData, а не JSON
    const token = localStorage.getItem('access_token')
    const res = await fetch(`/api/stages/${selectedStage.value.id}/upload/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // Content-Type НЕ ставим, браузер сам поставит multipart/form-data с boundary
      },
      body: formData
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Ошибка загрузки файла')
    }

    closeUploadModal()
    alert('Файл успешно загружен и отправлен на проверку!')
    fetchThesis() // Обновляем данные
  } catch (error) {
    uploadError.value = error.message
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  fetchThesis()
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