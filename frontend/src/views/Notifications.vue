<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Уведомления</h2>
      <button v-if="notifications.some(n => !n.is_read)" @click="markAllRead" class="btn btn-sm btn-outline-secondary">
        Отметить все как прочитанные
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="notifications.length === 0" class="text-center py-5 text-muted">
      У вас пока нет уведомлений.
    </div>

    <div v-else class="list-group shadow-sm">
      <div 
        v-for="n in notifications" 
        :key="n.id" 
        class="list-group-item list-group-item-action d-flex justify-content-between align-items-center"
        :class="{ 'bg-light': !n.is_read }"
        @click="handleClick(n)"
        style="cursor: pointer;"
      >
        <div>
          <span class="badge me-2" :class="getTypeBadge(n.type)">{{ n.type_display }}</span>
          <span :class="{'fw-bold': !n.is_read}">{{ n.message }}</span>
        </div>
        <small class="text-muted ms-3 text-nowrap">{{ formatDate(n.created_at) }}</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const notifications = ref([])
const loading = ref(true)

const fetchNotifications = async () => {
  loading.value = true
  try {
    const data = await api('/notifications/')
    notifications.value = Array.isArray(data) ? data : (data.results || [])
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const markAllRead = async () => {
  try {
    await api('/notifications/read_all/', { method: 'PATCH' })
    fetchNotifications()
    // Обновляем счетчик в шапке (можно вызвать кастомное событие)
    window.dispatchEvent(new Event('update-unread-count'))
  } catch (error) {
    alert(error.message)
  }
}

const handleClick = async (n) => {
  // Если не прочитано - отмечаем
  if (!n.is_read) {
    try {
      await api(`/notifications/${n.id}/read/`, { method: 'PATCH' })
      n.is_read = true
      window.dispatchEvent(new Event('update-unread-count'))
    } catch (error) {
      console.error(error)
    }
  }
  
  // Переходим по ссылке, если она есть
  if (n.link) {
    router.push(n.link)
  }
}

const getTypeBadge = (type) => {
  if (type === 'application') return 'bg-primary'
  if (type === 'review') return 'bg-success'
  if (type === 'stage') return 'bg-warning text-dark'
  if (type === 'deadline') return 'bg-danger'
  return 'bg-secondary'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const d = new Date(dateString)
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  fetchNotifications()
})
</script>