<script setup lang="ts">
import { FileText, Upload, Trash2, Sparkles } from 'lucide-vue-next'
import type { Document } from '~/types'

const props = defineProps<{
  documents: Document[]
  activeDocumentId: string | null
  isUploading: boolean
}>()

const emit = defineEmits<{
  selectDocument: [id: string]
  uploadClick: []
  deleteDocument: [id: string]
}>()

function formatFileSize(bytes: number) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<template>
  <header class="h-16 border-b bg-white/80 backdrop-blur-sm flex items-center px-5 gap-4 shrink-0">
    <!-- Logo -->
    <div class="flex items-center gap-2.5">
      <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-purple-400 flex items-center justify-center shadow-sm shadow-primary/25">
        <Sparkles class="w-4.5 h-4.5 text-white" />
      </div>
      <div>
        <h1 class="text-base font-bold tracking-tight leading-none">DocChat</h1>
        <p class="text-[10px] text-muted-foreground font-medium">by Rivestack</p>
      </div>
    </div>

    <div class="h-8 w-px bg-border mx-1" />

    <!-- Document tabs -->
    <div class="flex items-center gap-1.5 flex-1 overflow-x-auto">
      <button
        v-for="doc in documents"
        :key="doc.id"
        class="flex items-center gap-2 px-3 py-2 rounded-xl text-sm transition-all duration-200 whitespace-nowrap group"
        :class="
          activeDocumentId === doc.id
            ? 'bg-primary/10 text-primary font-semibold ring-1 ring-primary/20'
            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
        "
        @click="emit('selectDocument', doc.id)"
      >
        <FileText class="w-3.5 h-3.5 shrink-0" />
        <span class="max-w-[160px] truncate">{{ doc.filename }}</span>
        <span class="text-[10px] opacity-60">{{ formatFileSize(doc.file_size) }}</span>
        <button
          class="ml-0.5 opacity-0 group-hover:opacity-100 hover:text-destructive transition-all duration-200"
          @click.stop="emit('deleteDocument', doc.id)"
        >
          <Trash2 class="w-3 h-3" />
        </button>
      </button>
    </div>

    <!-- Upload button -->
    <Button
      size="sm"
      :disabled="isUploading"
      class="rounded-xl shadow-sm shadow-primary/25"
      @click="emit('uploadClick')"
    >
      <Upload class="w-4 h-4" />
      Upload PDF
    </Button>
  </header>
</template>
