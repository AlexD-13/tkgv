export const useApiFetch = <T>(path: string, options: Record<string, unknown> = {}) => {
  const config = useRuntimeConfig()
  return useFetch<T>(`${config.public.apiBase}${path}`, {
    lazy: true,
    // timeout: 15000,
    credentials: 'include',
    headers: useRequestHeaders(['cookie']) as Record<string, string>,
    ...options
  })
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  const defaults = {
    credentials: 'include' as RequestCredentials
  }

  return {
    get: <T>(path: string) => $fetch<T>(`${base}${path}`, defaults),
    post: <T>(path: string, body: Record<string, unknown>) =>
      $fetch<T>(`${base}${path}`, { ...defaults, method: 'POST', body }),
    put: <T>(path: string, body: Record<string, unknown>) =>
      $fetch<T>(`${base}${path}`, { ...defaults, method: 'PUT', body }),
    del: <T>(path: string) => $fetch<T>(`${base}${path}`, { ...defaults, method: 'DELETE' })
  }
}
