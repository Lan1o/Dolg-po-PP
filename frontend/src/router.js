import { createRouter, createWebHistory } from 'vue-router'
import { auth } from './api'

import Login from './views/Login.vue'
import Catalog from './views/Catalog.vue'
import MyApplications from './views/MyApplications.vue'
import Workspace from './views/Workspace.vue'
import SupervisorInbox from './views/SupervisorInbox.vue'
import ReviewStage from './views/ReviewStage.vue'
import Notifications from './views/Notifications.vue'
import SupervisorTopics from './views/SupervisorTopics.vue'
import AdminUsers from './views/AdminUsers.vue'
import SupervisorStudents from './views/SupervisorStudents.vue'
import SupervisorStudentDetail from './views/SupervisorStudentDetail.vue'

const routes = [
  { path: '/', redirect: '/catalog' },
  { path: '/login', component: Login, meta: { guest: true } },
  { path: '/catalog', component: Catalog, meta: { requiresAuth: true } },
  { path: '/my-applications', component: MyApplications, meta: { requiresAuth: true } },
  { path: '/workspace', component: Workspace, meta: { requiresAuth: true } },
  { path: '/supervisor/inbox', component: SupervisorInbox, meta: { requiresAuth: true } },
  { path: '/supervisor/stage/:id', component: ReviewStage, meta: { requiresAuth: true } },
  { path: '/supervisor/topics', component: SupervisorTopics, meta: { requiresAuth: true } },
  { path: '/supervisor/students', component: SupervisorStudents, meta: { requiresAuth: true } },
  { path: '/supervisor/student/:id', component: SupervisorStudentDetail, meta: { requiresAuth: true } },
  { path: '/admin/users', component: AdminUsers, meta: { requiresAuth: true } },
  { path: '/notifications', component: Notifications, meta: { requiresAuth: true } },
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