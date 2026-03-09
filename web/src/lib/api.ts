const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (!isFormData) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(apiUrl(path), {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

/**
 * Fetch an SSE endpoint and call onEvent for each parsed `data:` line.
 * Returns when the stream closes.
 */
export async function apiFetchSSE(
  path: string,
  options: RequestInit = {},
  token: string | undefined,
  onEvent: (event: Record<string, unknown>) => void
): Promise<void> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `API error ${res.status}`);
  }

  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith("data: ")) {
        try {
          onEvent(JSON.parse(trimmed.slice(6)));
        } catch {
          // skip malformed JSON
        }
      }
    }
  }
}
