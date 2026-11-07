<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Мои темы ВКР</h2>
      <button class="btn btn-primary" @click="openCreateModal">
        + Создать тему
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="topics.length === 0" class="text-center py-5 text-muted">
      У вас пока нет предложенных тем.
    </div>

    <div v-else class="row g-3">
      <div v-for="topic in topics" :key="topic.id" class="col-md-6 col-lg-4">
        <div class="card h-100 shadow-sm">
          <div class="card-body d-flex flex-column">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge bg-secondary">{{ topic.direction?.code }}</span>
              <span :class="statusBadgeClass(topic.status)" class="badge">
                {{ topic.status_display }}
              </span>
            </div>
            <h5 class="card-title">{{ topic.title }}</h5>
            <p class="card-text text-muted small flex-grow-1">{{ topic.description }}</p>
          </div>
          <div class="card-footer bg-white border-top-0 pt-0 pb-3">
            <button class="btn btn-sm btn-outline-secondary w-100" @click="openEditModal(topic)">
              Редактировать
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно создания/редактирования -->
    <div v-if="showModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? 'Редактировать тему' : 'Создать новую тему' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            
            <div class="mb-3">
              <label class="form-label">Название темы <span class="text-danger">*</span></label>
              <input v-model="form.title" type="text" class="form-control" placeholder="Например: Разработка веб-сервиса...">
            </div>

            <div class="mb-3">
              <label class="form-label">Направление подготовки <span class="text-danger">*</span></label>
              <select v-model="form.direction_id" class="form-select">
                <option value="">Выберите направление</option>
                <option v-for="d in directions" :key="d.id" :value="d.id">
                  {{ d.code }} — {{ d.title }}
                </option>
              </select>
            </div>

            <div class="mb-3">
              <label class="form-label">Описание <span class="text-danger">*</span></label>
              <textarea v-model="form.description" class="form-control" rows="3" placeholder="О чем эта тема?"></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label">Требования к работе</label>
              <textarea v-model="form.requirements" class="form-control" rows="2" placeholder="Навыки, инструменты, ожидаемый результат"></textarea>
            </div>

            <div class="mb-3">
              <label class="form-label">Теги (через запятую)</label>
              <input v-model="form.tags" type="text" class="form-control" placeholder="веб, python, django">
            </div>

            <div class="mb-3">
              <label class="form-label">Статус</label>
              <select v-model="form.status" class="form-select">
                <option value="free">Свободна</option>
                <option value="archived">В архиве</option>
              </select>
            </div>

            <div v-if="error" class="alert alert-danger py-2 small">{{ error }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button type="button" class="btn btn-primary" @click="submitForm" :disabled="submitting">
              {{ submitting ? 'Сохранение...' : 'Сохранить' }}
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

const topics = ref([])
const directions = ref([])
const loading = ref(true)

const showModal = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const error = ref('')

const form = ref({
  id: null,
  title: '',
  direction_id: '',
  description: '',
  requirements: '',
  tags: '',
  status: 'free'
})

const statusBadgeClass = (status) => {
  if (status === 'free') return 'bg-success'
  if (status === 'pending') return 'bg-warning text-dark'
  if (status === 'occupied') return 'bg-danger'
  return 'bg-secondary'
}

const fetchTopics = async () => {
  loading.value = true
  try {
    // Параметр my=true фильтрует темы только текущего руководителя
    const data = await api('/topics/?my=true')
    topics.value = Array.isArray(data) ? data : (data.results || [])
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const fetchDirections = async () => {
  try {
    const data = await api('/topics/filters/')
    directions.value = data.directions
  } catch (err) {
    console.error(err)
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = { id: null, title: '', direction_id: '', description: '', requirements: '', tags: '', status: 'free' }
  error.value = ''
  showModal.value = true
}

const openEditModal = (topic) => {
  isEditing.value = true
  form.value = {
    id: topic.id,
    title: topic.title,
    direction_id: topic.direction?.id || '',
    description: topic.description,
    requirements: topic.requirements || '',
    tags: topic.tags || '',
    status: topic.status
  }
  error.value = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const submitForm = async () => {
  if (!form.value.title || !form.value.direction_id || !form.value.description) {
    error.value = 'Заполните обязательные поля (*)'
    return
  }

  submitting.value = true
  error.value = ''

  try {
    if (isEditing.value) {
      await api(`/topics/${form.value.id}/`, {
        method: 'PUT',
        body: JSON.stringify({
          title: form.value.title,
          direction_id: form.value.direction_id,
          description: form.value.description,
          requirements: form.value.requirements,
          tags: form.value.tags,
          status: form.value.status
        })
      })
    } else {
      await api('/topics/', {
        method: 'POST',
        body: JSON.stringify({
          title: form.value.title,
          direction_id: form.value.direction_id,
          description: form.value.description,
          requirements: form.value.requirements,
          tags: form.value.tags,
          status: form.value.status
        })
      })
    }
    closeModal()
    fetchTopics()
  } catch (err) {
    error.value = err.message
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchDirections()
  fetchTopics()
})
</script>