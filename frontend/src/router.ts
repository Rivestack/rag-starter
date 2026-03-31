import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/pages/HomePage.vue'
import StoryPage from '@/pages/StoryPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomePage },
    { path: '/story/:slug', name: 'story', component: StoryPage },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
