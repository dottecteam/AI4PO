const BASE_URL = process.env.NEXT_PUBLIC_API_URL

const METODOS_SEGUROS = ["GET", "HEAD", "OPTIONS"]

function getCookie(name: string) {
  if (typeof document === "undefined") return undefined
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="))
    ?.split("=")[1]
}

// O Django só exige CSRF em métodos não seguros (POST, PATCH, PUT, DELETE)
function getCsrfHeader(metodo?: string): Record<string, string> {
  const m = (metodo ?? "GET").toUpperCase()
  if (METODOS_SEGUROS.includes(m)) return {}
  const token = getCookie("csrftoken")
  return token ? { "X-CSRFToken": token } : {}
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      // Com FormData não definimos Content-Type: o navegador gera o boundary correto
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...getCsrfHeader(options?.method),
      ...options?.headers,
    },
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null)
    throw new Error(
      errorBody
        ? JSON.stringify(errorBody)
        : `Erro ${response.status} ao acessar ${path}`,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

async function apiFetchBlob(
  path: string,
  options?: RequestInit,
): Promise<Blob> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "include", // envia o cookie JWT
    headers: {
      ...getCsrfHeader(options?.method),
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`Erro ${response.status} ao acessar ${path}`)
  }

  return response.blob()
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),

  post: <T>(path: string, body: unknown, options?: Pick<RequestInit, "signal">) =>
    apiFetch<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
      signal: options?.signal,
    }),

  postForm: <T>(path: string, formData: FormData) =>
    apiFetch<T>(path, {
      method: "POST",
      body: formData,
    }),

  patch: <T>(path: string, body: unknown) =>
    apiFetch<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  delete: <T>(path: string) =>
    apiFetch<T>(path, {
      method: "DELETE",
    }),

  getBlob: (path: string) => apiFetchBlob(path),
}
