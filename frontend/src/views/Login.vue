<template>
  <div class="row justify-content-center mt-5">
    <div class="col-md-5">
      <div class="card shadow">
        <div class="card-body p-4">
          <h3 class="text-center mb-4">Вход в CampusThesis</h3>
          
          <form @submit.prevent="handleLogin">
            <div class="mb-3">
              <label class="form-label">Логин</label>
              <input v-model="username" type="text" class="form-control" required />
            </div>
            <div class="mb-3">
              <label class="form-label">Пароль</label>
              <input v-model="password" type="password" class="form-control" required />
            </div>
            
            <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
            
            <button type="submit" class="btn btn-primary w-100" :disabled="loading">
              {{ loading ? 'Вход...' : 'Войти' }}
            </button>
          </form>

          <hr class="my-4">
          <div class="text-center small text-muted">
            <p class="mb-1">Тестовые аккаунты:</p>
            <p class="mb-1"><strong>Студент:</strong> smirnov / Student2026!</p>
            <p class="mb-0"><strong>Рук-ль:</strong> ivanov / Supervisor2026!</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from '../api'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/catalog')
    window.location.reload()
  } catch (err) {
    error.value = 'Неверный логин или пароль'
  } finally {
    loading.value = false
  }
}
</script>