<template>
  <div>
    <div class="mb-3">
      <router-link to="/supervisor/inbox" class="text-decoration-none">← Назад в инбокс</router-link>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="stage">
      <h2 class="mb-4">Проверка этапа: {{ stage.type_display }}</h2>

      <div class="row">
        <!-- Левая колонка: файлы -->
        <div class="col-md-6">
          <div class="card shadow-sm mb-4">
            <div class="card-header bg-white">
              <h5 class="mb-0">Загруженные файлы</h5>
            </div>
            <div class="card-body">
              <div v-if="!stage.files || stage.files.length === 0" class="text-muted">Файлы не загружены.</div>
              <ul v-else class="list-group list-group-flush">
                <li v-for="file in stage.files" :key="file.id" class="list-group-item d-flex justify-content-between align-items-center px-0">
                  <span>{{ file.file_name }}</span>
                  <button @click="downloadFile(file.id)" class="btn btn-sm btn-outline-primary">Скачать</button>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Правая колонка: форма отзыва -->
        <div class="col-md-6">
          <div class="card shadow-sm border-primary">
            <div class="card-header bg-primary text-white">
              <h5 class="mb-0">Ваш отзыв</h5>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <label class="form-label">Решение</label>
                <select v-model="reviewDecision" class="form-select">
                  <option value="approved">Одобрено (перевести на следующий этап)</option>
                  <option value="needs_revision">Доработать (вернуть студенту)</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label">Текст отзыва</label>
                <textarea v-model="reviewText" class="form-control" rows="4" placeholder="Опишите замечания или похвалите..."></textarea>
              </div>
              <div v-if="error" class="alert alert-danger py-2 small">{{ error }}</div>
              <button class="btn btn-primary w-100" @click="submitReview" :disabled="submitting || !reviewText">
                {{ submitting ? 'Отправка...' : 'Сохранить отзыв' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const stageId = route.params.id

const stage = ref(null)
const loading = ref(true)

const reviewText = ref('')
const reviewDecision = ref('approved')
const submitting = ref(false)
const error = ref('')

const fetchStage = async () => {
  loading.value = true
  try {
    stage.value = await api(`/stages/${stageId}/`)
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const submitReview = async () => {
  submitting.value = true
  error.value = ''
  try {
    await api(`/stages/${stageId}/review/`, {
      method: 'POST',
      body: JSON.stringify({
        decision: reviewDecision.value,
        text: reviewText.value
      })
    })
    alert('Отзыв сохранён!')
    router.push('/supervisor/inbox')
  } catch (err) {
    error.value = err.message
  } finally {
    submitting.value = false
  }
}

// Принудительное скачивание файла
const downloadFile = async (fileId) => {
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch(`/api/stages/${stageId}/files/${fileId}/download/`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) throw new Error('Ошибка скачивания')

    const blob = await response.blob()
    
    let filename = 'file'
    const disposition = response.headers.get('Content-Disposition')
    if (disposition && disposition.includes('filename=')) {
      filename = disposition.split('filename=')[1].replace(/"/g, '')
    }

    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    a.remove()
  } catch (error) {
    alert('Не удалось скачать файл: ' + error.message)
  }
}

onMounted(() => {
  fetchStage()
})
</script>