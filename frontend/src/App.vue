<template>
  <div>
    <nav v-if="isAuth" class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
      <div class="container">
        <router-link class="navbar-brand" to="/">CampusThesis</router-link>
        
        <div class="d-flex align-items-center">
          <!-- Ссылки для студента -->
          <template v-if="userRole === 'student'">
            <router-link class="nav-link text-light me-3" to="/catalog">Каталог тем</router-link>
            <router-link class="nav-link text-light me-3" to="/my-applications">Мои заявки</router-link>
            <router-link class="nav-link text-light me-3" to="/workspace">Моя ВКР</router-link>
          </template>

          <!-- Ссылки для руководителя -->
          <template v-if="userRole === 'supervisor'">
            <router-link class="nav-link text-light me-3" to="/supervisor/inbox">Инбокс (заявки и проверки)</router-link>
          </template>

          <!-- Ссылки для админа -->
          <template v-if="userRole === 'admin'">
            <router-link class="nav-link text-light me-3" to="/catalog">Каталог тем</router-link>
            <a class="nav-link text-light me-3" href="http://localhost:8000/admin/" target="_blank">Админка Django</a>
          </template>
          
          <button @click="handleLogout" class="btn btn-outline-light btn-sm ms-3">Выйти</button>
        </div>
      </div>
    </nav>

    <div class="container pb-5">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { auth, api } from './api'

const router = useRouter()
const isAuth = ref(false)
const userRole = ref('')

onMounted(async () => {
  isAuth.value = auth.isAuthenticated()
  if (isAuth.value) {
    try {
      // Получаем профиль пользователя, чтобы узнать его роль
      const user = await api('/auth/me')
      userRole.value = user.role
    } catch (error) {
      console.error('Не удалось загрузить профиль', error)
    }
  }
})

const handleLogout = () => {
  auth.logout()
}
</script>