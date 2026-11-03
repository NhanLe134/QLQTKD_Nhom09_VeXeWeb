import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, get, post } from './apiClient'

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
