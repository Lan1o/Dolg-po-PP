<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2>Управление пользователями</h2>
      <button class="btn btn-primary" @click="openCreateModal">
        + Добавить пользователя
      </button>
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status"></div>
    </div>

    <div v-else class="table-responsive shadow-sm rounded">
      <table class="table table-hover align-middle bg-white mb-0">
        <thead class="table-light">
          <tr>
            <th>ФИО</th>
            <th>Логин</th>
            <th>Роль</th>
            <th>Группа/Должность</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.full_name || u.username }}</td>
            <td>{{ u.username }}</td>
            <td><span :class="roleBadgeClass(u.role)" class="badge">{{ u.role_display }}</span></td>
            <td>{{ u.role === 'student' ? u.group_name : u.position }}</td>
            <td>
              <button class="btn btn-sm btn-outline-secondary" @click="openEditModal(u)">Изменить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Модалка создания/редактирования -->
    <div v-if="showModal" class="modal d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? 'Редактировать пользователя' : 'Новый пользователь' }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Роль <span class="text-danger">*</span></label>
              <select v-model="form.role" class="form-select">
                <option value="student">Студент</option>
                <option value="supervisor">Руководитель</option>
              </select>
            </div>
            
            <div class="mb-3">
              <label class="form-label">Логин <span class="text-danger">*</span></label>
              <input v-model="form.username" type="text" class="form-control" :disabled="isEditing">
            </div>

            <div class="mb-3">
              <label class="form-label">Пароль {{ isEditing ? '(оставьте пустым, чтобы не менять)' : '*' }}</label>
              <input v-model="form.password" type="password" class="form-control">
            </div>
            
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label">Фамилия</label>
                <input v-model="form.last_name" type="text" class="form-control">
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label">Имя</label>
                <input v-model="form.first_name" type="text" class="form-control">
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Email</label>
              <input v-model="form.email" type="email" class="form-control">
            </div>

            <!-- Поля, зависящие от роли -->
            <div v-if="form.role === 'student'" class="mb-3">
              <label class="form-label">Учебная группа</label>
              <input v-model="form.group_name" type="text" class="form-control" placeholder="Например: ИРИТ-РТФ-41">
            </div>
            
            <div v-if="form.role === 'supervisor'" class="mb-3">
              <label class="form-label">Должность</label>
              <input v-model="form.position" type="text" class="form-control" placeholder="Например: Доцент кафедры ИТ">
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

const users = ref([])
const loading = ref(true)

const showModal = ref(false)
const isEditing = ref(false)
const submitting = ref(false)
const error = ref('')

const form = ref({
  id: null,
  username: '',
  password: '',
  first_name: '',
  last_name: '',
  email: '',
  role: 'student',
  group_name: '',
  position: ''
})

const roleBadgeClass = (role) => {
  if (role === 'student') return 'bg-info text-dark'
  if (role === 'supervisor') return 'bg-primary'
  if (role === 'admin') return 'bg-danger'
  return 'bg-secondary'
}

const fetchUsers = async () => {
  loading.value = true
  try {
    const data = await api('/auth/users/')
    users.value = Array.isArray(data) ? data : (data.results || [])
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openCreateModal = () => {
  isEditing.value = false
  form.value = { id: null, username: '', password: '', first_name: '', last_name: '', email: '', role: 'student', group_name: '', position: '' }
  error.value = ''
  showModal.value = true
}

const openEditModal = (user) => {
  isEditing.value = true
  form.value = {
    id: user.id,
    username: user.username,
    password: '',
    first_name: user.first_name,
    last_name: user.last_name,
    email: user.email,
    role: user.role,
    group_name: user.group_name || '',
    position: user.position || ''
  }
  error.value = ''
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
}

const submitForm = async () => {
  if (!form.value.username || (!isEditing.value && !form.value.password)) {
    error.value = 'Заполните логин и пароль'
    return
  }

  submitting.value = true
  error.value = ''

  try {
    if (isEditing.value) {
      await api(`/auth/users/${form.value.id}/`, {
        method: 'PUT',
        body: JSON.stringify(form.value)
      })
    } else {
      await api('/auth/users/', {
        method: 'POST',
        body: JSON.stringify(form.value)
      })
    }
    closeModal()
    fetchUsers()
  } catch (err) {
    error.value = err.message
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchUsers()
})
</script>