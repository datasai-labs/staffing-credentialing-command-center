export type ApiError = {
  status: number;
  message: string;
  request_id?: string;
};

async function parseError(res: Response): Promise<ApiError> {
  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      const body = (await res.json()) as any;
      return {
        status: res.status,
        message: body?.detail ?? body?.message ?? `Request failed (${res.status})`,
        request_id: body?.request_id
      };
    } catch {
      // fall through
    }
  }
  const text = await res.text().catch(() => "");
  return { status: res.status, message: text || `Request failed (${res.status})` };
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "PATCH",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw await parseError(res);
  return (await res.json()) as T;
}

export function toQuery(params: Record<string, unknown>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === "") continue;
    sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

