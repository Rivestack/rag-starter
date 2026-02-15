<script setup lang="ts">
import { Bot, User } from 'lucide-vue-next'
import type { ChatMessage, SourceChunk } from '~/types'

const props = defineProps<{
  message: ChatMessage
  activeSourceId: string | null
}>()

const emit = defineEmits<{
  sourceClick: [source: SourceChunk]
}>()
</script>

<template>
  <div
    class="flex gap-3 px-4 py-3"
    :class="message.role === 'user' ? '' : 'bg-muted/40'"
  >
    <!-- Avatar -->
    <div
      class="w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5"
      :class="
        message.role === 'user'
          ? 'bg-primary text-primary-foreground'
          : 'bg-secondary text-secondary-foreground'
      "
    >
      <User v-if="message.role === 'user'" class="w-3.5 h-3.5" />
      <Bot v-else class="w-3.5 h-3.5" />
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0">
      <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>

      <!-- Source badges -->
      <div v-if="message.sources?.length" class="flex flex-wrap gap-1.5 mt-2">
        <SourceBadge
          v-for="source in message.sources"
          :key="source.chunk_id"
          :source="source"
          :is-active="activeSourceId === source.chunk_id"
          @click="emit('sourceClick', source)"
        />
      </div>
    </div>
  </div>
</template>
