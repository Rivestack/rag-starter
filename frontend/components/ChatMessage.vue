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
  <div class="flex gap-3 px-5 py-4" :class="message.role === 'assistant' ? 'bg-muted/30' : ''">
    <!-- Avatar -->
    <div
      class="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 mt-0.5"
      :class="
        message.role === 'user'
          ? 'bg-foreground text-background'
          : 'bg-gradient-to-br from-primary/10 to-purple-100 text-primary'
      "
    >
      <User v-if="message.role === 'user'" class="w-4 h-4" />
      <Bot v-else class="w-4 h-4" />
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0 pt-0.5">
      <p class="text-sm leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>

      <!-- Source badges -->
      <div v-if="message.sources?.length" class="flex flex-wrap gap-1.5 mt-3">
        <span class="text-[10px] text-muted-foreground font-medium uppercase tracking-wider mr-1 self-center">Sources</span>
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
