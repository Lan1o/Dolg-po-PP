<template>
  <div>
    <h2 class="mb-4">Мои студенты</h2>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else-if="theses.length === 0" class="text-center py-5 text-muted">
      У вас пока нет студентов с активными ВКР.
    </div>

    <div v-else class="row g-3">
      <div v-for="thesis in theses" :key="thesis.id" class="col-md-6 col-lg-4">
        <div class="card h-100 shadow-sm">
          <div class="card-body">
            <h5 class="card-title">{{ thesis.student_name }}</h5>
            <p class="card-text text-muted small mb-2">{{ thesis.topic_title }}</p>
            <span class="badge bg-primary">{{ thesis.status_display }}</span>
          </div>
          <div class="card-footer bg-white border-top-0 pt-0 pb-3">
            <router-link :to="`/supervisor/student/${thesis.id}`" class="btn btn-sm btn-outline-primary w-100">
              Открыть карточку
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'

const theses = ref([])
const loading = ref(true)

const fetchTheses = async () => {
  loading.value = true
  try {
    const data = await api('/theses/')
    theses.value = Array.isArray(data) ? data : (data.results || [])
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTheses()
})
</script>