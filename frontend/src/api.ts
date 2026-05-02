// Тонкий клиент над fetch, единое место для обработки ошибок API.

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let detail = response.statusText || "Ошибка запроса";
  try {
    const data = await response.json();
    if (data && typeof data.detail === "string") {
      detail = data.detail;
    } else if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
      // pydantic-валидация
      detail = data.detail.map((e: { msg: string }) => e.msg).join("; ");
    }
  } catch {
    /* nothing — оставим statusText */
  }
  return new ApiError(response.status, detail);
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  json?: unknown;
  body?: BodyInit;
  headers?: Record<string, string>;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json", ...(opts.headers ?? {}) };
  let body: BodyInit | undefined = opts.body;
  if (opts.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.json);
  }
  const response = await fetch(path, {
    method: opts.method ?? (opts.json !== undefined || opts.body !== undefined ? "POST" : "GET"),
    credentials: "include",
    headers,
    body,
  });
  if (!response.ok) {
    throw await parseError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, json?: unknown) => request<T>(path, { method: "POST", json }),
  postForm: <T>(path: string, form: FormData) => request<T>(path, { method: "POST", body: form }),
};
