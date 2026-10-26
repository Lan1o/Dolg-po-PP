<template>
  <div>
    <h2 class="mb-4">Мои заявки на темы ВКР</h2>

    <!-- Загрузка -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="mt-2 text-muted">Загрузка заявок...</p>
    </div>

    <!-- Пусто -->
    <div v-else-if="applications.length === 0" class="text-center py-5">
      <p class="text-muted">У вас пока нет заявок.</p>
      <router-link to="/catalog" class="btn btn-primary">Перейти в каталог тем</router-link>
    </div>

    <!-- Список -->
    <div v-else class="row g-3">
      <div v-for="app in applications" :key="app.id" class="col-12">
        <div class="card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h5 class="card-title mb-0">{{ app.topic.title }}</h5>
              <span :class="statusBadgeClass(app.status)" class="badge fs-6">
                {{ app.status_display }}
              </span>
            </div>
            
            <p class="text-muted small mb-2">
              <strong>Направление:</strong> {{ app.topic.direction?.code }} — {{ app.topic.direction?.title }}<br>
              <strong>Руководитель:</strong> {{ app.topic.supervisor?.full_name }} ({{ app.topic.supervisor?.position }})
            </p>

            <p v-if="app.comment" class="small mb-1">
              <strong>Ваш комментарий:</strong> {{ app.comment }}
            </p>
            <p v-if="app.supervisor_comment" class="small mb-1 text-primary">
              <strong>Комментарий руководителя:</strong> {{ app.supervisor_comment }}
            </p>
            
            <div class="d-flex justify-content-between align-items-center mt-3 pt-3 border-top">
              <small class="text-muted">Подана: {{ formatDate(app.created_at) }}</small>
              
              <!-- Если одобрена — кнопка перехода в рабочую область -->
              <router-link 
                v-if="app.status === 'approved'" 
                to="/workspace" 
                class="btn btn-sm btn-success"
              >
                Перейти к работе →
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const applications = ref([])
const loading = ref(true)

const statusBadgeClass = (status) => {
  if (status === 'approved') return 'bg-success'
  if (status === 'submitted') return 'bg-primary'
  if (status === 'under_review') return 'bg-warning text-dark'
  if (status === 'rejected') return 'bg-danger'
  return 'bg-secondary'
}

const formatDate = (isoString) => {
  if (!isoString) return ''
  return new Date(isoString).toLocaleDateString('ru-RU', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

const fetchApplications = async () => {
  loading.value = true
  try {
    // Запрос к нашему кастомному эндпоинту /my
    const data = await api('/applications/my/')
    // DRF может вернуть объект пагинации
    applications.value = Array.isArray(data) ? data : (data.results || [])
  } catch (error) {
    console.error('Ошибка загрузки заявок:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchApplications()
})
</script>