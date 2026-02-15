<script setup lang="ts">
import { Database } from 'lucide-vue-next'
</script>

<template>
  <div class="flex items-center justify-center gap-1.5 py-2 text-xs text-muted-foreground">
    <Database class="w-3 h-3" />
    <span>Powered by</span>
    <a
      href="https://rivestack.com"
      target="_blank"
      class="font-semibold text-primary hover:underline"
    >
      Rivestack
    </a>
    <span>— pgvector on PostgreSQL</span>
  </div>
</template>
