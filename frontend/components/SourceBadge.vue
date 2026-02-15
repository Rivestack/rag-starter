<script setup lang="ts">
import { FileText } from 'lucide-vue-next'
import type { SourceChunk } from '~/types'

const props = defineProps<{
  source: SourceChunk
  isActive: boolean
}>()

const emit = defineEmits<{
  click: []
}>()
</script>

<template>
  <button
    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer"
    :class="
      isActive
        ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/25'
        : 'bg-primary/10 text-primary hover:bg-primary/20'
    "
    :title="source.content"
    @click="emit('click')"
  >
    <FileText class="w-3 h-3" />
    Page {{ source.page_number }}
  </button>
</template>
