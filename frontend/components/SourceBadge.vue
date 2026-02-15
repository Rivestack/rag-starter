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
    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium transition-all cursor-pointer"
    :class="
      isActive
        ? 'bg-yellow-100 text-yellow-800 border border-yellow-300 shadow-sm'
        : 'bg-muted text-muted-foreground hover:bg-yellow-50 hover:text-yellow-700 border border-transparent'
    "
    :title="source.content"
    @click="emit('click')"
  >
    <FileText class="w-3 h-3" />
    Page {{ source.page_number }}
  </button>
</template>
