import { ref } from 'vue'
import type { SearchResultItem, PerformanceStats, SearchResponse } from '@/types'

const API_BASE = (window as any).env?.VITE_API_BASE || import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export function useSearch() {
  const query = ref('')
  const results = ref<SearchResultItem[]>([])
  const performance = ref<PerformanceStats | null>(null)
  const isSearching = ref(false)
  const error = ref<string | null>(null)

  async function search() {
    const q = query.value.trim()
    if (!q) return

    isSearching.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      })

      if (!response.ok) {
        // The API sends a reason in `detail` (e.g. embedding quota exhausted).
        // Prefer it over a generic string so the page can explain the failure.
        let detail = ''
        try {
          detail = (await response.json())?.detail ?? ''
        } catch {
          // Non-JSON body (e.g. a proxy error page); fall back to the status.
        }
        throw new Error(detail || `Search failed (HTTP ${response.status})`)
      }

      const data: SearchResponse = await response.json()
      results.value = data.results
      performance.value = data.performance
    } catch (e: any) {
      error.value = e.message || 'Search failed'
      results.value = []
      performance.value = null
    } finally {
      isSearching.value = false
    }
  }

  return { query, results, performance, isSearching, error, search }
}
