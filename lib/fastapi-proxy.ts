const FASTAPI_BASE = process.env.FASTAPI_BASE_URL ?? "http://localhost:8001";

export type FastApiJson<T = Record<string, unknown>> = {
  ok: boolean;
  status: number;
  data: T;
};

export type FastApiBinary = {
  ok: boolean;
  status: number;
  data: ArrayBuffer | null;
  contentType: string | null;
  contentDisposition: string | null;
  errorDetail: string | null;
};

/** Call FastAPI and always return JSON (never throw on non-JSON error bodies). */
export async function fetchFastApi<T = Record<string, unknown>>(
  path: string,
  init?: RequestInit,
): Promise<FastApiJson<T>> {
  const url = `${FASTAPI_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  try {
    const res = await fetch(url, { cache: "no-store", ...init });
    const text = await res.text();
    let data: T;
    try {
      data = text ? (JSON.parse(text) as T) : ({} as T);
    } catch {
      data = {
        detail: text || res.statusText || "Non-JSON response from FastAPI",
      } as T;
    }
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    return {
      ok: false,
      status: 502,
      data: {
        detail: `Could not reach FastAPI: ${(err as Error).message}`,
      } as T,
    };
  }
}

/** Call FastAPI expecting a binary body (e.g. .pptx download). */
export async function fetchFastApiBinary(
  path: string,
  init?: RequestInit,
): Promise<FastApiBinary> {
  const url = `${FASTAPI_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  try {
    const res = await fetch(url, { cache: "no-store", ...init });
    if (!res.ok) {
      const text = await res.text();
      let errorDetail = text || res.statusText;
      try {
        const parsed = JSON.parse(text) as { detail?: string };
        if (typeof parsed.detail === "string") {
          errorDetail = parsed.detail;
        }
      } catch {
        /* keep raw text */
      }
      return {
        ok: false,
        status: res.status,
        data: null,
        contentType: res.headers.get("content-type"),
        contentDisposition: res.headers.get("content-disposition"),
        errorDetail,
      };
    }
    return {
      ok: true,
      status: res.status,
      data: await res.arrayBuffer(),
      contentType: res.headers.get("content-type"),
      contentDisposition: res.headers.get("content-disposition"),
      errorDetail: null,
    };
  } catch (err) {
    return {
      ok: false,
      status: 502,
      data: null,
      contentType: null,
      contentDisposition: null,
      errorDetail: `Could not reach FastAPI: ${(err as Error).message}`,
    };
  }
}
