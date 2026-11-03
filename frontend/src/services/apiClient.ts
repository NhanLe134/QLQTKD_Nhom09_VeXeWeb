const NETWORK_ERROR_MESSAGE = 'Không kết nối được máy chủ. Vui lòng thử lại.'
const GENERIC_ERROR_MESSAGE = 'Đã có lỗi xảy ra. Vui lòng thử lại.'
const VALIDATION_ERROR_MESSAGE = 'Dữ liệu gửi lên không hợp lệ.'

/** Lỗi từ API; `detail` là thông báo hiển thị nguyên văn cho người dùng. */
export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function getBaseUrl(): string {
  const baseUrl = import.meta.env.VITE_API_URL
  if (!baseUrl) {
    throw new Error('Chưa cấu hình VITE_API_URL (xem frontend/.env.example).')
  }
  return baseUrl.replace(/\/+$/, '')
}

async function readDetail(response: Response): Promise<string> {
  let body: unknown
  try {
    body = await response.json()
  } catch {
    return GENERIC_ERROR_MESSAGE
  }

  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string' && detail.trim() !== '') {
    return detail
  }
  // FastAPI trả 422 với detail là mảng lỗi kiểm tra dữ liệu (tiếng Anh), không hiển thị nguyên văn
  if (response.status === 422) {
    return VALIDATION_ERROR_MESSAGE
  }
  return GENERIC_ERROR_MESSAGE
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const url = `${getBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`
  const init: RequestInit = { method, headers: { Accept: 'application/json' } }
  if (body !== undefined) {
    init.headers = { ...init.headers, 'Content-Type': 'application/json' }
    init.body = JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(url, init)
  } catch {
    throw new ApiError(0, NETWORK_ERROR_MESSAGE)
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response))
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export function get<T>(path: string): Promise<T> {
  return request<T>('GET', path)
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>('POST', path, body)
}
