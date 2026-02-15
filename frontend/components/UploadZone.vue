<script setup lang="ts">
import { ref } from 'vue'
import { Upload, Loader2, AlertCircle, Sparkles, FileUp } from 'lucide-vue-next'
import type { UploadProgress } from '~/types'

const props = defineProps<{
  isUploading: boolean
  progress: UploadProgress | null
  error: string | null
}>()

const emit = defineEmits<{
  fileSelected: [file: File]
}>()

const isDragging = ref(false)
const fileInput = ref<HTMLInputElement>()

function handleDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file && file.type === 'application/pdf') {
    emit('fileSelected', file)
  }
}

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    emit('fileSelected', file)
    target.value = ''
  }
}

function openFilePicker() {
  fileInput.value?.click()
}

const stageLabels: Record<string, string> = {
  parsing: 'Extracting text from PDF...',
  chunking: 'Splitting into smart chunks...',
  embedding: 'Generating vector embeddings...',
  storing: 'Storing in Rivestack pgvector...',
}
</script>

<template>
  <div class="flex flex-col items-center justify-center h-full p-8">
    <div class="w-full max-w-xl">
      <!-- Hero text -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-xs font-semibold mb-4">
          <Sparkles class="w-3 h-3" />
          Powered by Rivestack pgvector
        </div>
        <h2 class="text-3xl font-bold tracking-tight mb-2">Chat with any PDF</h2>
        <p class="text-muted-foreground text-sm max-w-sm mx-auto">
          Upload a document, ask questions in plain English, and get AI-powered answers with highlighted sources.
        </p>
      </div>

      <!-- Upload area -->
      <div
        v-if="!isUploading && !error"
        class="border-2 border-dashed rounded-2xl p-14 text-center cursor-pointer transition-all duration-300"
        :class="isDragging
          ? 'border-primary bg-primary/5 scale-[1.02] shadow-lg shadow-primary/10'
          : 'border-border hover:border-primary/40 hover:bg-primary/[0.02] hover:shadow-md'"
        @dragover.prevent="isDragging = true"
        @dragleave="isDragging = false"
        @drop.prevent="handleDrop"
        @click="openFilePicker"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          class="hidden"
          @change="handleFileInput"
        />
        <div class="flex flex-col items-center gap-5">
          <div class="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/10 to-purple-100 flex items-center justify-center">
            <FileUp class="w-9 h-9 text-primary" />
          </div>
          <div>
            <p class="text-lg font-semibold">Drop your PDF here</p>
            <p class="text-sm text-muted-foreground mt-1">or click to browse files</p>
          </div>
          <Badge variant="secondary" class="text-xs font-medium">
            PDF files up to 50MB
          </Badge>
        </div>
      </div>

      <!-- Progress state -->
      <div
        v-else-if="isUploading && progress"
        class="border rounded-2xl p-10 text-center bg-white shadow-lg shadow-primary/5"
      >
        <div class="flex flex-col items-center gap-5">
          <div class="w-20 h-20 rounded-3xl bg-gradient-to-br from-primary/10 to-purple-100 flex items-center justify-center">
            <Loader2 class="w-9 h-9 text-primary animate-spin" />
          </div>
          <div>
            <p class="text-lg font-semibold">Processing your PDF</p>
            <p class="text-sm text-muted-foreground mt-1">{{ stageLabels[progress.stage] || progress.message }}</p>
          </div>
          <div class="w-full max-w-xs">
            <Progress :model-value="progress.percent" class="h-2.5" />
            <p class="text-xs text-muted-foreground mt-2 font-medium">{{ progress.percent }}% complete</p>
          </div>
        </div>
      </div>

      <!-- Error state -->
      <div
        v-else-if="error"
        class="border border-destructive/30 rounded-2xl p-10 text-center bg-destructive/[0.02]"
      >
        <div class="flex flex-col items-center gap-5">
          <div class="w-20 h-20 rounded-3xl bg-destructive/10 flex items-center justify-center">
            <AlertCircle class="w-9 h-9 text-destructive" />
          </div>
          <div>
            <p class="text-lg font-semibold">Upload failed</p>
            <p class="text-sm text-muted-foreground mt-1">{{ error }}</p>
          </div>
          <Button variant="outline" size="sm" class="rounded-xl" @click="openFilePicker">
            Try again
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
