export default defineNuxtConfig({
  modules: ['shadcn-nuxt', '@nuxtjs/tailwindcss'],
  shadcn: {
    prefix: '',
    componentDir: './components/ui',
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
    },
  },
  ssr: false,
  devtools: { enabled: false },
  compatibilityDate: '2025-01-01',
})
