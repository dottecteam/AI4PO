const BASE_URL = process.env.NEXT_PUBLIC_API_URL;

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${path}`, {
        ...options,
        headers: { "Content-Type": "application/json", ...options?.headers, },
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        throw new Error(
            errorBody ? JSON.stringify(errorBody) : `Erro ${response.status} ao acessar ${path}`
        );
    }

    if (response.status === 204) {
        return undefined as T;
    }

    return response.json();
}

export const api = {
    get: <T>(path: string) => apiFetch<T>(path),

    post: <T>(path: string, body: unknown) =>
        apiFetch<T>(path, {
            method: "POST",
            body: JSON.stringify(body),
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
};