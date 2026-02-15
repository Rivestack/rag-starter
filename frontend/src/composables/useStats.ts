import { ref } from 'vue'
import type { DbStats } from '@/types'

const API_BASE = (window as any).env?.VITE_API_BASE || import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export function useStats() {
  const stats = ref<DbStats | null>(null)

  async function fetchStats() {
    try {
      const response = await fetch(`${API_BASE}/api/stats`)
      if (response.ok) {
        stats.value = await response.json()
      }
    } catch {
      // Stats are non-critical
    }
  }

  return { stats, fetchStats }
}
