const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export function apiUrl(path: string) {
  return `${base}${path}`
}

export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  let response: Response
  try {
    response = await fetch(apiUrl(path), options)
  } catch {
    throw new Error(
      'The API could not be reached. Check that the backend is running.',
    )
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(
      body?.error?.message ||
        `Request failed (${response.status}). Check the backend and database.`,
    )
  }
  return response.json() as Promise<T>
}
