export const useAdmin = () => {
  const config = useRuntimeConfig()
  const base = config.public.apiBase
  const token = ref<string>('')

  onMounted(() => {
    token.value = localStorage.getItem('gestionplatos_admin_token') || ''
  })

  function setToken(value: string) {
    token.value = value
    if (value) localStorage.setItem('gestionplatos_admin_token', value)
    else localStorage.removeItem('gestionplatos_admin_token')
  }

  const headers = computed(() => (token.value ? { 'X-Admin-Token': token.value } : {}))

  async function get<T>(path: string) {
    return await $fetch<T>(`${base}${path}`, { headers: headers.value })
  }
  async function post<T>(path: string, body?: unknown) {
    return await $fetch<T>(`${base}${path}`, { method: 'POST', body, headers: headers.value })
  }
  async function patch<T>(path: string, body?: unknown) {
    return await $fetch<T>(`${base}${path}`, { method: 'PATCH', body, headers: headers.value })
  }
  async function del(path: string) {
    return await $fetch(`${base}${path}`, { method: 'DELETE', headers: headers.value })
  }

  const isAuthed = computed(() => !!token.value)

  return { token, setToken, isAuthed, get, post, patch, del }
}
