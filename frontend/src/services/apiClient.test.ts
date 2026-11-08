import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, get, post, put, setAuthToken, setUnauthorizedHandler } from './apiClient'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test/')
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('get', () => {
  it('ghép VITE_API_URL với đường dẫn và trả dữ liệu JSON', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { status: 'ok' }))

    await expect(get('/health')).resolves.toEqual({ status: 'ok' })
    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/health',
      expect.objectContaining({ method: 'GET' }),
    )
  })

  it('ném ApiError mang nguyên văn detail từ backend', async () => {
    fetchMock.mockResolvedValue(jsonResponse(409, { detail: 'Ghế đã được giữ' }))

    const error = await get('/x').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 409, detail: 'Ghế đã được giữ', message: 'Ghế đã được giữ' })
  })

  it('dùng thông báo tiếng Việt khi lỗi 422 có detail là mảng', async () => {
    fetchMock.mockResolvedValue(jsonResponse(422, { detail: [{ msg: 'Field required' }] }))

    await expect(get('/x')).rejects.toMatchObject({ status: 422, detail: 'Dữ liệu gửi lên không hợp lệ.' })
  })

  it('dùng thông báo chung khi body lỗi không phải JSON', async () => {
    fetchMock.mockResolvedValue(new Response('Internal Server Error', { status: 500 }))

    await expect(get('/x')).rejects.toMatchObject({ status: 500, detail: 'Đã có lỗi xảy ra. Vui lòng thử lại.' })
  })

  it('ném ApiError status 0 khi không kết nối được', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(get('/health')).rejects.toMatchObject({
      status: 0,
      detail: 'Không kết nối được máy chủ. Vui lòng thử lại.',
    })
  })

  it('báo lỗi khi chưa cấu hình VITE_API_URL', async () => {
    vi.stubEnv('VITE_API_URL', '')

    await expect(get('/health')).rejects.toThrow('Chưa cấu hình VITE_API_URL')
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('post', () => {
  it('gửi body dạng JSON', async () => {
    fetchMock.mockResolvedValue(jsonResponse(201, { id: 'VE00000001' }))

    await expect(post('/api/v1/x', { a: 1 })).resolves.toEqual({ id: 'VE00000001' })
    const [, init] = fetchMock.mock.calls[0]
    expect(init).toMatchObject({
      method: 'POST',
      body: '{"a":1}',
      headers: { 'Content-Type': 'application/json' },
    })
  })
})

describe('put', () => {
  it('gửi PUT với body JSON và header thêm', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { ok: true }))

    await expect(put('/api/v1/x', { a: 1 }, { 'X-Ma-Truy-Cap': 'ma' })).resolves.toEqual({ ok: true })

    const [, init] = fetchMock.mock.calls[0]
    expect(init?.method).toBe('PUT')
    expect(init?.body).toBe(JSON.stringify({ a: 1 }))
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma', 'Content-Type': 'application/json' })
  })
})

describe('lỗi kèm tên trường', () => {
  it('đọc khóa truong vào ApiError.field', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(422, { detail: 'Số điện thoại không hợp lệ', truong: 'hanh_khach[1].so_dien_thoai' }),
    )

    const error = await get('/api/v1/x').catch((caught: unknown) => caught)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 422, detail: 'Số điện thoại không hợp lệ', field: 'hanh_khach[1].so_dien_thoai' })
  })

  it('không có truong thì field là null', async () => {
    fetchMock.mockResolvedValue(jsonResponse(400, { detail: 'Lỗi', truong: null }))

    await expect(get('/api/v1/x')).rejects.toMatchObject({ detail: 'Lỗi', field: null })
  })
})

describe('token đăng nhập', () => {
  it('không gửi Authorization khi chưa đăng nhập', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, {}))

    await get('/x')

    const [, init] = fetchMock.mock.calls[0]
    expect(init?.headers).not.toHaveProperty('Authorization')
  })

  it('gắn Bearer token vào mọi request', async () => {
    setAuthToken('abc.def.ghi')
    fetchMock.mockImplementation(async () => jsonResponse(200, {}))

    await get('/x')
    await post('/y', { a: 1 })

    for (const [, init] of fetchMock.mock.calls) {
      expect(init?.headers).toMatchObject({ Authorization: 'Bearer abc.def.ghi' })
    }
  })

  it('gọi handler khi request có token nhận 401', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    setAuthToken('het-han')
    fetchMock.mockResolvedValue(jsonResponse(401, { detail: 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn' }))

    await expect(get('/x')).rejects.toMatchObject({ status: 401 })
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
  })

  it('không gọi handler khi request không có token nhận 401 (đăng nhập sai)', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    fetchMock.mockResolvedValue(jsonResponse(401, { detail: 'Sai tên đăng nhập hoặc mật khẩu' }))

    await expect(post('/login', {})).rejects.toMatchObject({ detail: 'Sai tên đăng nhập hoặc mật khẩu' })
    expect(onUnauthorized).not.toHaveBeenCalled()
  })

  it('không gọi handler khi token đã đổi trong lúc chờ phản hồi', async () => {
    const onUnauthorized = vi.fn()
    setUnauthorizedHandler(onUnauthorized)
    setAuthToken('token-cu')
    fetchMock.mockImplementation(async () => {
      setAuthToken('token-moi')
      return jsonResponse(401, { detail: 'x' })
    })

    await expect(get('/x')).rejects.toMatchObject({ status: 401 })
    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})

describe('header thêm', () => {
  it('gửi header thêm cùng token, không ghi đè Accept', async () => {
    setAuthToken('abc')
    fetchMock.mockImplementation(async () => jsonResponse(200, {}))

    await get('/bookings/DH1', { 'X-Ma-Truy-Cap': 'ma-bi-mat', Accept: 'text/plain' })
    await post('/bookings/hold', { a: 1 }, { 'X-Ma-Truy-Cap': 'ma-2' })

    const [, getInit] = fetchMock.mock.calls[0]
    expect(getInit?.headers).toEqual({
      'X-Ma-Truy-Cap': 'ma-bi-mat',
      Accept: 'application/json',
      Authorization: 'Bearer abc',
    })
    const [, postInit] = fetchMock.mock.calls[1]
    expect(postInit?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-2', 'Content-Type': 'application/json' })
  })
})
