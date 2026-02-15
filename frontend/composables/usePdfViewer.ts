import { ref } from 'vue'
import type { BboxRect, SourceChunk } from '~/types'

export function usePdfViewer() {
  const pdfUrl = ref<string | null>(null)
  const currentPage = ref(1)
  const totalPages = ref(0)
  const activeHighlights = ref<BboxRect[]>([])
  const activeSourceId = ref<string | null>(null)

  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase as string

  function loadDocument(documentId: string) {
    pdfUrl.value = `${apiBase}/api/documents/${documentId}/pdf`
    currentPage.value = 1
    clearHighlights()
  }

  function highlightSource(source: SourceChunk) {
    activeHighlights.value = source.bbox_data
    activeSourceId.value = source.chunk_id
    if (source.page_number) {
      currentPage.value = source.page_number
    }
  }

  function clearHighlights() {
    activeHighlights.value = []
    activeSourceId.value = null
  }

  function getPageHighlights(pageNumber: number): BboxRect[] {
    return activeHighlights.value.filter((h) => h.page === pageNumber)
  }

  return {
    pdfUrl,
    currentPage,
    totalPages,
    activeHighlights,
    activeSourceId,
    loadDocument,
    highlightSource,
    clearHighlights,
    getPageHighlights,
  }
}
