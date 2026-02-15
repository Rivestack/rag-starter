<script setup lang="ts">
import { ref } from 'vue'
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-vue-next'
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
  parsing: 'Extracting text...',
  chunking: 'Creating chunks...',
  embedding: 'Generating embeddings...',
  storing: 'Storing in Rivestack...',
}
</script>

<template>
  <div class="flex flex-col items-center justify-center h-full p-8">
    <div class="w-full max-w-lg">
      <!-- Upload area -->
      <div
        v-if="!isUploading && !error"
        class="border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-200"
        :class="isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-border hover:border-primary/50 hover:bg-muted/50'"
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
        <div class="flex flex-col items-center gap-4">
          <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Upload class="w-8 h-8 text-primary" />
          </div>
          <div>
            <p class="text-lg font-medium">Drop your PDF here</p>
            <p class="text-sm text-muted-foreground mt-1">or click to browse files</p>
          </div>
          <p class="text-xs text-muted-foreground">PDF files up to 50MB</p>
        </div>
      </div>

      <!-- Progress state -->
      <div
        v-else-if="isUploading && progress"
        class="border rounded-2xl p-8 text-center"
      >
        <div class="flex flex-col items-center gap-4">
          <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
            <Loader2 class="w-8 h-8 text-primary animate-spin" />
          </div>
          <div>
            <p class="text-lg font-medium">Processing your PDF</p>
            <p class="text-sm text-muted-foreground mt-1">{{ progress.message }}</p>
          </div>
          <div class="w-full">
            <Progress :model-value="progress.percent" class="h-2" />
            <p class="text-xs text-muted-foreground mt-2">{{ progress.percent }}%</p>
          </div>
        </div>
      </div>

      <!-- Error state -->
      <div
        v-else-if="error"
        class="border border-destructive/50 rounded-2xl p-8 text-center"
      >
        <div class="flex flex-col items-center gap-4">
          <div class="w-16 h-16 rounded-2xl bg-destructive/10 flex items-center justify-center">
            <AlertCircle class="w-8 h-8 text-destructive" />
          </div>
          <div>
            <p class="text-lg font-medium">Upload failed</p>
            <p class="text-sm text-muted-foreground mt-1">{{ error }}</p>
          </div>
          <Button variant="outline" size="sm" @click="openFilePicker">
            Try again
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
