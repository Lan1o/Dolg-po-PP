<template>
  <div>
    <nav v-if="isAuth" class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
      <div class="container">
        <router-link class="navbar-brand" to="/">CampusThesis</router-link>
        
        <!-- Кнопка-бургер для мобильных -->
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>

        <!-- Сворачиваемое меню -->
        <div class="collapse navbar-collapse" id="navbarNav">
          <div class="navbar-nav ms-auto align-items-lg-center">
            <!-- Ссылки для студента -->
            <template v-if="userRole === 'student'">
              <router-link class="nav-link text-light me-lg-3" to="/catalog">Каталог тем</router-link>
              <router-link class="nav-link text-light me-lg-3" to="/my-applications">Мои заявки</router-link>
              <router-link class="nav-link text-light me-lg-3" to="/workspace">Моя ВКР</router-link>
            </template>

            <!-- Ссылки для руководителя -->
            <template v-if="userRole === 'supervisor'">
              <router-link class="nav-link text-light me-lg-3" to="/supervisor/inbox">Инбокс</router-link>
            </template>

            <!-- Ссылки для админа -->
            <template v-if="userRole === 'admin'">
              <router-link class="nav-link text-light me-lg-3" to="/catalog">Каталог тем</router-link>
              <a class="nav-link text-light me-lg-3" href="http://localhost:8000/admin/" target="_blank">Админка</a>
            </template>

            <!-- Колокольчик уведомлений -->
            <router-link to="/notifications" class="nav-link text-light position-relative me-lg-3 mt-2 mt-lg-0">
              <span class="fs-5">🔔</span>
              <span 
                v-if="unreadCount > 0" 
                class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
              >
                {{ unreadCount }}
              </span>
            </router-link>
            
            <button @click="handleLogout" class="btn btn-outline-light btn-sm mt-3 mt-lg-0 ms-lg-3">Выйти</button>
          </div>
        </div>
      </div>
    </nav>

    <div class="container pb-5">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { auth, api } from './api'

const router = useRouter()
const isAuth = ref(false)
const userRole = ref('')
const unreadCount = ref(0)

const fetchUnreadCount = async () => {
  if (!isAuth.value) return
  try {
    const data = await api('/notifications/unread_count/')
    unreadCount.value = data.count
  } catch (error) {
    console.error('Не удалось получить счетчик', error)
  }
}

const handleUpdateEvent = () => {
  fetchUnreadCount()
}

onMounted(async () => {
  isAuth.value = auth.isAuthenticated()
  if (isAuth.value) {
    try {
      const user = await api('/auth/me')
      userRole.value = user.role
      await fetchUnreadCount()
    } catch (error) {
      console.error(error)
    }
  }
  window.addEventListener('update-unread-count', handleUpdateEvent)
})

onUnmounted(() => {
  window.removeEventListener('update-unread-count', handleUpdateEvent)
})

const handleLogout = () => {
  auth.logout()
}
</script>