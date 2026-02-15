<script setup lang="ts">
import { Search, Loader2 } from 'lucide-vue-next'
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
      <Search class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
      <input
        v-model="query"
        type="text"
        placeholder="Search Hacker News... e.g. 'best programming languages 2025'"
        class="w-full h-14 pl-12 pr-28 rounded-xl border bg-card text-base shadow-sm transition-colors focus:outline-none focus:ring-2 focus:ring-ring placeholder:text-muted-foreground/60"
        @keydown="handleKeydown"
      />
      <Button
        class="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg"
        :disabled="!query.trim() || isSearching"
        @click="emit('search')"
      >
        <Loader2 v-if="isSearching" class="h-4 w-4 animate-spin mr-2" />
        <Search v-else class="h-4 w-4 mr-2" />
        Search
      </Button>
    </div>
  </div>
</template>
