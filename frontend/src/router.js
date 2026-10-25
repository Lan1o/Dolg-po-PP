import { createRouter, createWebHistory } from 'vue-router'
import { auth } from './api'

import Login from './views/Login.vue'
import Catalog from './views/Catalog.vue'
import MyApplications from './views/MyApplications.vue'
import Workspace from './views/Workspace.vue'

const routes = [
  { path: '/', redirect: '/catalog' },
  { path: '/login', component: Login, meta: { guest: true } },
  { path: '/catalog', component: Catalog, meta: { requiresAuth: true } },
  { path: '/my-applications', component: MyApplications, meta: { requiresAuth: true } },
  { path: '/workspace', component: Workspace, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const isAuth = auth.isAuthenticated()
  
  if (to.meta.requiresAuth && !isAuth) {
    next('/login')
  } else if (to.meta.guest && isAuth) {
    next('/catalog')
  } else {
    next()
  }
})

export default router