<template>
  <div>
    <h2 class="mb-4">Панель руководителя</h2>

    <!-- Вкладки -->
    <ul class="nav nav-tabs mb-4">
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'applications' }" @click="activeTab = 'applications'">
          Заявки на темы <span v-if="pendingAppsCount" class="badge bg-danger ms-1">{{ pendingAppsCount }}</span>
        </button>
      </li>
      <li class="nav-item">
        <button class="nav-link" :class="{ active: activeTab === 'stages' }" @click="activeTab = 'stages'">
          Этапы на проверку <span v-if="pendingStages.length" class="badge bg-danger ms-1">{{ pendingStages.length }}</span>
        </button>
      </li>
    </ul>

    <!-- Контент вкладок -->
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else>
      <!-- Вкладка: Заявки -->
      <div v-if="activeTab === 'applications'">
        <div v-if="applications.length === 0" class="text-muted text-center py-4">Заявок пока нет.</div>
        
        <div v-for="app in applications" :key="app.id" class="card mb-3 shadow-sm">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start">
              <h5 class="card-title">{{ app.topic.title }}</h5>
              <span :class="getAppStatusBadge(app.status)" class="badge">{{ app.status_display }}</span>
            </div>
            
            <p class="text-muted small mb-2 mt-2">
              <strong>Студент:</strong> {{ app.student_name }}<br>
              <strong>Комментарий:</strong> {{ app.comment || 'Нет' }}
            </p>
            
            <!-- Блок действий показываем ТОЛЬКО если статус "submitted" -->
            <div v-if="app.status === 'submitted'" class="mt-3">
              <input v-model="app.reviewComment" type="text" class="form-control form-control-sm mb-2" placeholder="Комментарий (необязательно)">
              <div class="d-flex gap-2">
                <button class="btn btn-sm btn-success" @click="handleApprove(app)">Одобрить</button>
                <button class="btn btn-sm btn-outline-danger" @click="handleReject(app)">Отклонить</button>
              </div>
            </div>
            
            <!-- Если заявка уже обработана, показываем комментарий руководителя -->
            <div v-else-if="app.supervisor_comment" class="mt-3 pt-3 border-top">
               <p class="small text-muted mb-0"><strong>Ваш комментарий:</strong> {{ app.supervisor_comment }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Вкладка: Этапы -->
      <div v-if="activeTab === 'stages'">
        <div v-if="pendingStages.length === 0" class="text-muted text-center py-4">Нет этапов на проверку.</div>
        
        <div v-for="stage in pendingStages" :key="stage.id" class="card mb-3 shadow-sm">
          <div class="card-body d-flex justify-content-between align-items-center">
            <div>
              <h5 class="mb-1">{{ stage.type_display }}</h5>
              <p class="text-muted small mb-0">
                Студент: {{ stage.student_name }}<br>
                Файлов: {{ stage.files_count }}
              </p>
            </div>
            <router-link :to="`/supervisor/stage/${stage.id}`" class="btn btn-primary">
              Проверить
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'

const activeTab = ref('applications')
const applications = ref([])
const pendingStages = ref([])
const loading = ref(true)

// Считаем количество необработанных заявок для бейджа
const pendingAppsCount = computed(() => {
  return applications.value.filter(a => a.status === 'submitted').length
})

// Загрузка данных
const fetchData = async () => {
  loading.value = true
  try {
    // 1. Заявки (все свои)
    const appsData = await api('/applications/inbox/')
    applications.value = Array.isArray(appsData) ? appsData : (appsData.results || [])
    // Добавляем поле для комментария
    applications.value.forEach(a => a.reviewComment = '')

    // 2. Этапы на проверке
    const allStages = await api('/stages/')
    const stagesList = Array.isArray(allStages) ? allStages : (allStages.results || [])
    
    // Фильтруем на фронтенде только те, что ждут проверки
    pendingStages.value = stagesList.filter(s => s.status === 'submitted')
    
  } catch (error) {
    console.error('Ошибка загрузки данных:', error)
  } finally {
    loading.value = false
  }
}

// Действия с заявками
const handleApprove = async (app) => {
  try {
    await api(`/applications/${app.id}/approve/`, {
      method: 'PATCH',
      body: JSON.stringify({ comment: app.reviewComment || 'Тема согласована.' })
    })
    fetchData()
    alert('Заявка одобрена!')
  } catch (error) {
    alert('Ошибка: ' + error.message)
  }
}

const handleReject = async (app) => {
  try {
    await api(`/applications/${app.id}/reject/`, {
      method: 'PATCH',
      body: JSON.stringify({ comment: app.reviewComment || 'Заявка отклонена.' })
    })
    fetchData()
    alert('Заявка отклонена.')
  } catch (error) {
    alert('Ошибка: ' + error.message)
  }
}

// Бейджи статусов
const getAppStatusBadge = (status) => {
  if (status === 'approved') return 'bg-success'
  if (status === 'submitted') return 'bg-primary'
  if (status === 'rejected') return 'bg-danger'
  return 'bg-secondary'
}

onMounted(() => {
  fetchData()
})
</script>