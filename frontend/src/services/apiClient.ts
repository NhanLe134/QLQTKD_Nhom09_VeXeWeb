const NETWORK_ERROR_MESSAGE = 'Không kết nối được máy chủ. Vui lòng thử lại.'
const GENERIC_ERROR_MESSAGE = 'Đã có lỗi xảy ra. Vui lòng thử lại.'
const VALIDATION_ERROR_MESSAGE = 'Dữ liệu gửi lên không hợp lệ.'

/**
 * Lỗi từ API; `detail` là thông báo hiển thị nguyên văn cho người dùng.
 * `field` là khóa `truong` (endpoint từ task #9), ví dụ `hanh_khach[1].so_dien_thoai`.
 */
export class ApiError extends Error {
  readonly status: number
  readonly detail: string
  readonly field: string | null

  constructor(status: number, detail: string, field: string | null = null) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.field = field
  }
}

let authToken: string | null = null
let unauthorizedHandler: (() => void) | null = null

/** Token gắn vào header Authorization của mọi request; null là khách vãng lai. */
export function setAuthToken(token: string | null): void {
  authToken = token
}

/** Gọi khi request có gửi token nhận 401 (token sai hoặc hết hạn). */
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

function getBaseUrl(): string {
  const baseUrl = import.meta.env.VITE_API_URL
  if (!baseUrl) {
    throw new Error('Chưa cấu hình VITE_API_URL (xem frontend/.env.example).')
  }
  return baseUrl.replace(/\/+$/, '')
}

async function readError(response: Response): Promise<ApiError> {
  let body: unknown
  try {
    body = await response.json()
  } catch {
    return new ApiError(response.status, GENERIC_ERROR_MESSAGE)
  }

  const { detail, truong } = (body ?? {}) as { detail?: unknown; truong?: unknown }
  if (typeof detail === 'string' && detail.trim() !== '') {
    return new ApiError(response.status, detail, typeof truong === 'string' ? truong : null)
  }
  // FastAPI trả 422 với detail là mảng lỗi kiểm tra dữ liệu (tiếng Anh), không hiển thị nguyên văn
  if (response.status === 422) {
    return new ApiError(response.status, VALIDATION_ERROR_MESSAGE)
  }
  return new ApiError(response.status, GENERIC_ERROR_MESSAGE)
}

/** Header thêm cho một request, ví dụ `X-Ma-Truy-Cap` của đơn đặt vé. */
export type RequestHeaders = Record<string, string>

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  extraHeaders?: RequestHeaders,
): Promise<T> {
  const url = `${getBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`
  const sentToken = authToken
  const headers: Record<string, string> = { ...extraHeaders, Accept: 'application/json' }
  if (sentToken) {
    headers.Authorization = `Bearer ${sentToken}`
  }
  const init: RequestInit = { method, headers }
  if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    init.body = JSON.stringify(body)
  }

  let response: Response
  try {
    response = await fetch(url, init)
  } catch {
    throw new ApiError(0, NETWORK_ERROR_MESSAGE)
  }

  // Chỉ xử lý 401 của request có gửi token: đăng nhập sai (không gửi token) không phải phiên hết hạn.
  // Bỏ qua nếu token đã đổi trong lúc chờ (người dùng vừa đăng nhập lại).
  if (response.status === 401 && sentToken && sentToken === authToken) {
    unauthorizedHandler?.()
  }
  if (!response.ok) {
    throw await readError(response)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export function get<T>(path: string, headers?: RequestHeaders): Promise<T> {
  return request<T>('GET', path, undefined, headers)
}

export function post<T>(path: string, body?: unknown, headers?: RequestHeaders): Promise<T> {
  return request<T>('POST', path, body, headers)
}

export function put<T>(path: string, body?: unknown, headers?: RequestHeaders): Promise<T> {
  return request<T>('PUT', path, body, headers)
}
