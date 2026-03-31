<script setup lang="ts">
import { useRouter } from 'vue-router'
import ThemeToggle from '@/components/ThemeToggle.vue'
import AppFooter from '@/components/AppFooter.vue'

const router = useRouter()

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Header -->
    <header class="flex items-center justify-between px-6 py-4">
      <button class="flex items-center gap-3 cursor-pointer" @click="goHome">
        <div class="flex items-center justify-center h-9 w-9 rounded-lg bg-primary/10">
          <img src="/logo.svg" alt="Rivestack" class="h-5 w-5" />
        </div>
        <div class="text-left">
          <h1 class="text-lg font-bold tracking-tight leading-none">Ask HN</h1>
          <p class="text-[11px] text-muted-foreground font-medium">Semantic Search</p>
        </div>
      </button>
      <ThemeToggle />
    </header>

    <!-- Main -->
    <main class="flex-1 flex flex-col items-center px-4 pt-6 pb-16 gap-5 max-w-3xl mx-auto w-full">
      <router-view />
    </main>

    <AppFooter />
  </div>
</template>
