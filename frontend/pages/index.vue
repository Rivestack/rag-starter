<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { SourceChunk, Document as DocType } from '~/types'

const { documents, isUploading, uploadProgress, uploadError, fetchDocuments, uploadPdf, deleteDocument } = useDocuments()
const { messages, isLoading: chatLoading, sendMessage, clearMessages } = useChat()
const { pdfUrl, currentPage, totalPages, activeSourceId, loadDocument, highlightSource, clearHighlights } = usePdfViewer()

const activeDocumentId = ref<string | null>(null)
const showUpload = ref(false)
const headerFileInput = ref<HTMLInputElement>()

const activeDocument = computed<DocType | null>(() => {
  if (!activeDocumentId.value) return null
  return documents.value.find((d) => d.id === activeDocumentId.value) || null
})

onMounted(() => {
  fetchDocuments()
})

function selectDocument(id: string) {
  if (activeDocumentId.value === id) return
  activeDocumentId.value = id
  loadDocument(id)
  clearMessages()
  clearHighlights()
}

async function handleFileSelected(file: File) {
  const doc = await uploadPdf(file)
  if (doc) {
    selectDocument(doc.id)
  }
}

function handleSendMessage(message: string) {
  if (!activeDocumentId.value) return
  clearHighlights()
  sendMessage(activeDocumentId.value, message)
}

function handleSourceClick(source: SourceChunk) {
  highlightSource(source)
}

function handleUploadClick() {
  if (activeDocumentId.value) {
    headerFileInput.value?.click()
  } else {
    // Already on upload screen
  }
}

function handleHeaderFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    handleFileSelected(file)
    target.value = ''
  }
}

function handleDeleteDocument(id: string) {
  deleteDocument(id)
  if (activeDocumentId.value === id) {
    activeDocumentId.value = null
    clearMessages()
    clearHighlights()
  }
}

function handlePagesLoaded(count: number) {
  totalPages.value = count
}
</script>

<template>
  <div class="h-screen flex flex-col">
    <AppHeader
      :documents="documents"
      :active-document-id="activeDocumentId"
      :is-uploading="isUploading"
      @select-document="selectDocument"
      @upload-click="handleUploadClick"
      @delete-document="handleDeleteDocument"
    />

    <div class="flex-1 flex overflow-hidden">
      <!-- No document selected: show upload zone -->
      <div v-if="!activeDocumentId" class="flex-1">
        <UploadZone
          :is-uploading="isUploading"
          :progress="uploadProgress"
          :error="uploadError"
          @file-selected="handleFileSelected"
        />
      </div>

      <!-- Document selected: split view -->
      <template v-else>
        <!-- Left: PDF Viewer (55%) -->
        <div class="w-[55%] border-r">
          <PdfViewer
            :pdf-url="pdfUrl"
            :current-page="currentPage"
            :highlights="activeSourceId ? (messages.flatMap(m => m.sources || []).find(s => s.chunk_id === activeSourceId)?.bbox_data || []) : []"
            @update:current-page="currentPage = $event"
            @pages-loaded="handlePagesLoaded"
          />
        </div>

        <!-- Right: Chat Panel (45%) -->
        <div class="w-[45%] flex flex-col">
          <ChatPanel
            :messages="messages"
            :is-loading="chatLoading"
            :active-source-id="activeSourceId"
            :document-name="activeDocument?.filename || 'document'"
            @send-message="handleSendMessage"
            @source-click="handleSourceClick"
          />
          <PoweredByBadge />
        </div>
      </template>
    </div>

    <!-- Hidden file input for header upload button -->
    <input
      ref="headerFileInput"
      type="file"
      accept=".pdf"
      class="hidden"
      @change="handleHeaderFileInput"
    />

    <!-- Powered by badge when no doc is selected -->
    <PoweredByBadge v-if="!activeDocumentId" />
  </div>
</template>
