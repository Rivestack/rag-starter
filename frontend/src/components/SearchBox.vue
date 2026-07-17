<script setup lang="ts">
import { Loader2, CornerDownLeft } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'

const query = defineModel<string>({ required: true })

defineProps<{
  isSearching: boolean
}>()

const emit = defineEmits<{
  search: []
}>()

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    emit('search')
  }
}
</script>

<template>
  <div class="w-full">
    <div class="relative">
      <span
        class="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 select-none text-lg font-bold text-primary"
        aria-hidden="true"
      >$</span>
      <input
        v-model="query"
        type="text"
        placeholder="search hacker news… e.g. best programming languages 2026"
        class="w-full h-14 pl-10 pr-28 rounded-none border-2 border-border bg-card text-base transition-colors focus:outline-none focus:border-primary placeholder:text-muted-foreground/60"
        @keydown="handleKeydown"
      />
      <Button
        class="absolute right-2 top-1/2 -translate-y-1/2 h-10"
        :disabled="!query.trim() || isSearching"
        @click="emit('search')"
      >
        <Loader2 v-if="isSearching" class="h-4 w-4 animate-spin mr-1.5" />
        <CornerDownLeft v-else class="h-4 w-4 mr-1.5" />
        Search
      </Button>
    </div>
  </div>
</template>
