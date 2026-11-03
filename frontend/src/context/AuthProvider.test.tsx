import { act, render, screen, waitFor } from '@testing-library/react'
import { useEffect } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuth } from '../hooks/useAuth'
import { get } from '../services/apiClient'
import AuthProvider, { AUTH_STORAGE_KEY } from './AuthProvider'

const fetchMock = vi.fn<typeof fetch>()

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const LOGIN_RESPONSE = {
  access_token: 'token-dang-nhap',
  token_type: 'bearer',
  vai_tro: 'KHACH',
  ho_ten: 'Nguyễn Văn An',
}

let auth: ReturnType<typeof useAuth>

function Probe() {
  const value = useAuth()
  // Đưa giá trị context ra ngoài để test gọi login/logout
  useEffect(() => {
    auth = value
  })
  return <p data-testid="user">{value.user ? value.user.ho_ten : 'khách vãng lai'}</p>
}

function renderProvider() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  )
}

function storeSession(token = 'token-luu-san') {
  sessionStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({ token, vai_tro: 'KHACH', ho_ten: 'Nguyễn Văn An' }),
  )
}

function authorizationOf(call: number): unknown {
  const init = fetchMock.mock.calls[call][1]
  return (init?.headers as Record<string, string> | undefined)?.Authorization
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('AuthProvider', () => {
  it('mặc định là khách vãng lai và không gọi API', () => {
    renderProvider()

    expect(screen.getByTestId('user')).toHaveTextContent('khách vãng lai')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('đăng nhập: lưu phiên vào sessionStorage và gắn token cho request sau', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, LOGIN_RESPONSE))
    renderProvider()

    await act(() => auth.login('an_nguyen', 'matkhau123'))

    expect(screen.getByTestId('user')).toHaveTextContent('Nguyễn Văn An')
    expect(fetchMock).toHaveBeenCalledWith(
      'http://api.test/api/v1/auth/login',
      expect.objectContaining({ body: '{"ten_dang_nhap":"an_nguyen","mat_khau":"matkhau123"}' }),
    )
    const stored = JSON.parse(sessionStorage.getItem(AUTH_STORAGE_KEY) ?? '{}')
    expect(stored).toEqual({ token: 'token-dang-nhap', vai_tro: 'KHACH', ho_ten: 'Nguyễn Văn An' })
    expect(JSON.stringify(stored)).not.toContain('matkhau123')

    fetchMock.mockResolvedValueOnce(jsonResponse(200, {}))
    await get('/x')
    expect(authorizationOf(1)).toBe('Bearer token-dang-nhap')
  })

  it('đăng nhập sai: ném lỗi với thông báo backend, vẫn là khách vãng lai', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(401, { detail: 'Sai tên đăng nhập hoặc mật khẩu' }))
    renderProvider()

    await expect(act(() => auth.login('an_nguyen', 'sai'))).rejects.toThrow('Sai tên đăng nhập hoặc mật khẩu')
    expect(screen.getByTestId('user')).toHaveTextContent('khách vãng lai')
    expect(sessionStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
  })

  it('đăng xuất: xóa phiên và không gửi token nữa', async () => {
    storeSession()
    fetchMock.mockImplementation(async () => jsonResponse(200, {}))
    renderProvider()

    act(() => auth.logout())

    expect(screen.getByTestId('user')).toHaveTextContent('khách vãng lai')
    expect(sessionStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
    fetchMock.mockClear()
    await get('/x')
    expect(authorizationOf(0)).toBeUndefined()
  })

  it('khởi động với phiên đã lưu: hiện người dùng ngay và kiểm tra lại bằng /me', async () => {
    storeSession()
    fetchMock.mockResolvedValue(jsonResponse(200, { user_id: 'TK00100000' }))

    renderProvider()

    expect(screen.getByTestId('user')).toHaveTextContent('Nguyễn Văn An')
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(fetchMock.mock.calls[0][0]).toBe('http://api.test/api/v1/auth/me')
    expect(authorizationOf(0)).toBe('Bearer token-luu-san')
    expect(screen.getByTestId('user')).toHaveTextContent('Nguyễn Văn An')
  })

  it('khởi động với token hết hạn: /me trả 401 thì tự đăng xuất', async () => {
    storeSession('token-het-han')
    fetchMock.mockResolvedValue(
      jsonResponse(401, { detail: 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn' }),
    )

    renderProvider()

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('khách vãng lai'))
    expect(sessionStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
  })

  it('bất kỳ request nào có token nhận 401 thì tự đăng xuất', async () => {
    storeSession()
    fetchMock.mockResolvedValueOnce(jsonResponse(200, {}))
    renderProvider()
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))

    fetchMock.mockResolvedValueOnce(jsonResponse(401, { detail: 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn' }))
    await act(() => get('/api/v1/ve-cua-toi').catch(() => {}))

    expect(screen.getByTestId('user')).toHaveTextContent('khách vãng lai')
    expect(sessionStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
  })

  it('bỏ qua dữ liệu hỏng trong sessionStorage', () => {
    sessionStorage.setItem(AUTH_STORAGE_KEY, '{không phải json')

    renderProvider()

    expect(screen.getByTestId('user')).toHaveTextContent('khách vãng lai')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('useAuth báo lỗi khi dùng ngoài AuthProvider', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => render(<Probe />)).toThrow('useAuth phải dùng bên trong <AuthProvider>.')
  })
})
