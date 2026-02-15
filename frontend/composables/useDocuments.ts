import { ref } from 'vue'
import type { Document, UploadProgress } from '~/types'

export function useDocuments() {
  const documents = ref<Document[]>([])
  const isLoading = ref(false)
  const isUploading = ref(false)
  const uploadProgress = ref<UploadProgress | null>(null)
  const uploadError = ref<string | null>(null)

  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  async function fetchDocuments() {
    isLoading.value = true
    try {
      const data = await $fetch<{ documents: Document[] }>(`${apiBase}/api/documents`)
      documents.value = data.documents
    } catch (e: any) {
      console.error('Failed to fetch documents:', e)
    } finally {
      isLoading.value = false
    }
  }

  async function uploadPdf(file: File): Promise<Document | null> {
    isUploading.value = true
    uploadProgress.value = { stage: 'parsing', percent: 0, message: 'Starting upload...' }
    uploadError.value = null

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${apiBase}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      })

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let completedDoc: Document | null = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (currentEvent === 'complete' || data.document_id) {
                completedDoc = {
                  id: data.document_id,
                  filename: data.filename,
                  file_size: data.file_size || 0,
                  page_count: data.page_count,
                  upload_status: 'ready',
                  created_at: new Date().toISOString(),
                }
              } else if (currentEvent === 'error') {
                uploadError.value = data.message
              } else if (data.percent !== undefined) {
                uploadProgress.value = data as UploadProgress
              }
            } catch {
              // Skip malformed JSON
            }
            currentEvent = ''
          }
        }
      }

      if (completedDoc) {
        documents.value.unshift(completedDoc)
      }
      return completedDoc
    } catch (e: any) {
      uploadError.value = e.message
      return null
    } finally {
      isUploading.value = false
      uploadProgress.value = null
    }
  }

  async function deleteDocument(id: string) {
    try {
      await $fetch(`${apiBase}/api/documents/${id}`, { method: 'DELETE' })
      documents.value = documents.value.filter((d) => d.id !== id)
    } catch (e: any) {
      console.error('Failed to delete document:', e)
    }
  }

  return {
    documents,
    isLoading,
    isUploading,
    uploadProgress,
    uploadError,
    fetchDocuments,
    uploadPdf,
    deleteDocument,
  }
}
