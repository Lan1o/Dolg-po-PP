<template>
  <div>
    <nav v-if="isAuth" class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
      <div class="container">
        <router-link class="navbar-brand" to="/catalog">CampusThesis</router-link>
        
        <div class="d-flex">
          <router-link class="nav-link text-light me-3" to="/catalog">Каталог тем</router-link>
          <router-link class="nav-link text-light me-3" to="/my-applications">Мои заявки</router-link>
          <router-link class="nav-link text-light me-3" to="/workspace">Моя ВКР</router-link>
          
          <button @click="handleLogout" class="btn btn-outline-light btn-sm">Выйти</button>
        </div>
      </div>
    </nav>

    <div class="container">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { auth } from './api'

const router = useRouter()
const isAuth = ref(false)

onMounted(() => {
  isAuth.value = auth.isAuthenticated()
})

const handleLogout = () => {
  auth.logout()
}
</script>