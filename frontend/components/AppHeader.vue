<script setup lang="ts">
import { FileText, Upload, Trash2 } from 'lucide-vue-next'
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
  <header class="h-14 border-b bg-white flex items-center px-4 gap-3 shrink-0">
    <!-- Logo -->
    <div class="flex items-center gap-2">
      <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
        <FileText class="w-4 h-4 text-white" />
      </div>
      <h1 class="text-lg font-semibold tracking-tight">DocChat</h1>
    </div>

    <div class="h-6 w-px bg-border mx-1" />

    <!-- Document tabs -->
    <div class="flex items-center gap-1.5 flex-1 overflow-x-auto">
      <button
        v-for="doc in documents"
        :key="doc.id"
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors whitespace-nowrap group"
        :class="
          activeDocumentId === doc.id
            ? 'bg-primary/10 text-primary font-medium'
            : 'text-muted-foreground hover:bg-muted'
        "
        @click="emit('selectDocument', doc.id)"
      >
        <FileText class="w-3.5 h-3.5 shrink-0" />
        <span class="max-w-[150px] truncate">{{ doc.filename }}</span>
        <span class="text-[10px] text-muted-foreground">{{ formatFileSize(doc.file_size) }}</span>
        <button
          class="ml-1 opacity-0 group-hover:opacity-100 hover:text-destructive transition-opacity"
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
      @click="emit('uploadClick')"
    >
      <Upload class="w-4 h-4" />
      Upload PDF
    </Button>
  </header>
</template>
