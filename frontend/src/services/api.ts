export async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, options)
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
