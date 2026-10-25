<template>
  <div>
    <h2 class="mb-4">Каталог тем ВКР</h2>

    <!-- Панель поиска и фильтров -->
    <div class="card mb-4 p-3 bg-white">
      <div class="row g-3">
        <!-- Поиск -->
        <div class="col-md-4">
          <label class="form-label small text-muted mb-1">Поиск по названию/описанию</label>
          <input 
            v-model="filters.q" 
            @input="debouncedFetch" 
            type="text" 
            class="form-control" 
            placeholder="Введите ключевые слова..."
          />
        </div>

        <!-- Фильтр: Направление -->
        <div class="col-md-2">
          <label class="form-label small text-muted mb-1">Направление</label>
          <select v-model="filters.direction" @change="fetchTopics" class="form-select">
            <option value="">Все</option>
            <option v-for="d in filterOptions.directions" :key="d.id" :value="d.id">
              {{ d.code }}
            </option>
          </select>
        </div>

        <!-- Фильтр: Руководитель -->
        <div class="col-md-2">
          <label class="form-label small text-muted mb-1">Руководитель</label>
          <select v-model="filters.supervisor" @change="fetchTopics" class="form-select">
            <option value="">Все</option>
            <option v-for="s in filterOptions.supervisors" :key="s.id" :value="s.id">
              {{ s.last_name }} {{ s.first_name[0] }}.
            </option>
          </select>
        </div>

        <!-- Фильтр: Статус -->
        <div class="col-md-2">
          <label class="form-label small text-muted mb-1">Статус</label>
          <select v-model="filters.status" @change="fetchTopics" class="form-select">
            <option value="">Все</option>
            <option v-for="st in filterOptions.statuses" :key="st.value" :value="st.value">
              {{ st.label }}
            </option>
          </select>
        </div>

        <!-- Фильтр: Теги -->
        <div class="col-md-2">
          <label class="form-label small text-muted mb-1">Тег</label>
          <input 
            v-model="filters.tags" 
            @input="debouncedFetch" 
            type="text" 
            class="form-control" 
            placeholder="например: python"
          />
        </div>
      </div>
    </div>

    <!-- Индикатор загрузки -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2 text-muted">Загрузка тем...</p>
    </div>

    <!-- Список тем -->
    <div v-else class="row g-3">
      <div v-if="topics.length === 0" class="col-12 text-center py-5 text-muted">
        По вашему запросу ничего не найдено.
      </div>

      <div v-for="topic in topics" :key="topic.id" class="col-md-6 col-lg-4">
        <div class="card h-100">
          <div class="card-body d-flex flex-column">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <span class="badge bg-secondary">{{ topic.direction?.code }}</span>
              <span :class="statusBadgeClass(topic.status)" class="badge">
                {{ topic.status_display }}
              </span>
            </div>
            
            <h5 class="card-title">{{ topic.title }}</h5>
            <p class="card-text text-muted small flex-grow-1">{{ topic.description }}</p>
            
            <div class="mt-3 pt-3 border-top small text-muted">
              <div class="mb-1"><strong>Руководитель:</strong> {{ topic.supervisor?.full_name }}</div>
              <div v-if="topic.tags"><strong>Теги:</strong> {{ topic.tags }}</div>
            </div>
          </div>
          <div class="card-footer bg-white border-top-0 pt-0">
            <button 
              class="btn btn-sm btn-outline-primary w-100" 
              @click="openApplyModal(topic)"
              :disabled="topic.status !== 'free'"
            >
              {{ topic.status === 'free' ? 'Подать заявку' : 'Тема занята' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Модальное окно подачи заявки -->
    <div v-if="showModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Подача заявки</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <p>Вы хотите подать заявку на тему:</p>
            <p class="fw-bold">{{ selectedTopic?.title }}</p>
            <p class="text-muted small">Руководитель: {{ selectedTopic?.supervisor?.full_name }}</p>
            
            <div class="mb-3 mt-4">
              <label class="form-label">Комментарий (необязательно)</label>
              <textarea v-model="applyComment" class="form-control" rows="3" placeholder="Почему вы хотите заниматься этой темой?"></textarea>
            </div>
            <div v-if="applyError" class="alert alert-danger py-2 small">{{ applyError }}</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">Отмена</button>
            <button type="button" class="btn btn-primary" @click="submitApplication" :disabled="submitting">
              {{ submitting ? 'Отправка...' : 'Подать заявку' }}
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
const loading = ref(true)
const filterOptions = ref({ directions: [], supervisors: [], statuses: [] })

const filters = ref({
  q: '',
  direction: '',
  supervisor: '',
  status: '',
  tags: ''
})

// Модалка
const showModal = ref(false)
const selectedTopic = ref(null)
const applyComment = ref('')
const applyError = ref('')
const submitting = ref(false)

// --- Вспомогательные функции ---
const statusBadgeClass = (status) => {
  if (status === 'free') return 'bg-success'
  if (status === 'pending') return 'bg-warning text-dark'
  if (status === 'occupied') return 'bg-danger'
  return 'bg-secondary'
}

// Дебаунс для поиска
let debounceTimer;
const debouncedFetch = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchTopics()
  }, 400)
}

// --- Работа с API ---
const fetchFilterOptions = async () => {
  try {
    const data = await api('/topics/filters/')
    filterOptions.value = data
  } catch (error) {
    console.error('Ошибка загрузки фильтров:', error)
  }
}

const fetchTopics = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.q) params.append('q', filters.value.q)
    if (filters.value.direction) params.append('direction', filters.value.direction)
    if (filters.value.supervisor) params.append('supervisor', filters.value.supervisor)
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.tags) params.append('tags', filters.value.tags)

    const queryString = params.toString()
    const url = `/topics/${queryString ? '?' + queryString : ''}`
    
    const response = await api(url)
    
    // Обработка пагинации
    topics.value = Array.isArray(response) ? response : (response.results || [])
  } catch (error) {
    console.error('Ошибка загрузки тем:', error)
  } finally {
    loading.value = false
  }
}

// --- Подача заявки ---
const openApplyModal = (topic) => {
  selectedTopic.value = topic
  applyComment.value = ''
  applyError.value = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedTopic.value = null
}

const submitApplication = async () => {
  submitting.value = true
  applyError.value = ''
  try {
    await api('/applications/', {
      method: 'POST',
      body: JSON.stringify({
        topic_id: selectedTopic.value.id,
        comment: applyComment.value
      })
    })
    closeModal()
    fetchTopics() // обновить статусы тем
    alert('Заявка успешно подана!')
  } catch (error) {
    applyError.value = error.message || 'Ошибка при подаче заявки'
  } finally {
    submitting.value = false
  }
}

// --- Жизненный цикл ---
onMounted(() => {
  fetchFilterOptions()
  fetchTopics()
})
</script>