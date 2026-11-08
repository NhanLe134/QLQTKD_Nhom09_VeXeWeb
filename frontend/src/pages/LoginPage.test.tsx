import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider from '../context/AuthProvider'
import LoginPage from './LoginPage'

const fetchMock = vi.fn<typeof fetch>()

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function renderLogin(initialState?: { from: string }) {
  const router = createMemoryRouter(
    [
      { path: '/', element: <h1>Trang chủ</h1> },
      { path: '/dat-ve', element: <h1>Đặt vé</h1> },
      { path: '/dang-nhap', element: <LoginPage /> },
    ],
    { initialEntries: [{ pathname: '/dang-nhap', state: initialState }] },
  )
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
}

function fillAndSubmit(tenDangNhap: string, matKhau: string) {
  fireEvent.change(screen.getByLabelText('Tên đăng nhập'), { target: { value: tenDangNhap } })
  fireEvent.change(screen.getByLabelText('Mật khẩu'), { target: { value: matKhau } })
  fireEvent.click(screen.getByRole('button', { name: 'Đăng nhập' }))
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('LoginPage', () => {
  it('báo lỗi ô trống và không gọi API', () => {
    renderLogin()

    fillAndSubmit('  ', '')

    expect(screen.getByText('Vui lòng nhập tên đăng nhập')).toBeInTheDocument()
    expect(screen.getByText('Vui lòng nhập mật khẩu')).toBeInTheDocument()
    expect(screen.getByLabelText('Tên đăng nhập')).toHaveAttribute('aria-invalid', 'true')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('hiện nguyên văn lỗi từ backend khi sai tên hoặc mật khẩu', async () => {
    fetchMock.mockResolvedValue(jsonResponse(401, { detail: 'Sai tên đăng nhập hoặc mật khẩu' }))
    renderLogin()

    fillAndSubmit('an_nguyen', 'sai-mat-khau')

    expect(await screen.findByRole('alert')).toHaveTextContent('Sai tên đăng nhập hoặc mật khẩu')
    expect(screen.getByRole('button', { name: 'Đăng nhập' })).toBeEnabled()
  })

  it('đăng nhập đúng: gửi tên đã bỏ khoảng trắng và về trang chủ', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(200, { access_token: 't', token_type: 'bearer', vai_tro: 'KHACH', ho_ten: 'An' }),
    )
    renderLogin()

    fillAndSubmit(' an_nguyen ', 'matkhau123')

    expect(await screen.findByRole('heading', { name: 'Trang chủ' })).toBeInTheDocument()
    expect(fetchMock.mock.calls[0][1]?.body).toBe('{"ten_dang_nhap":"an_nguyen","mat_khau":"matkhau123"}')
  })

  it('đăng nhập đúng: quay về trang trước đó nếu có', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(200, { access_token: 't', token_type: 'bearer', vai_tro: 'KHACH', ho_ten: 'An' }),
    )
    renderLogin({ from: '/dat-ve' })

    fillAndSubmit('an_nguyen', 'matkhau123')

    expect(await screen.findByRole('heading', { name: 'Đặt vé' })).toBeInTheDocument()
  })

  it('có liên kết sang trang đăng ký', () => {
    renderLogin()

    expect(screen.getByRole('link', { name: 'Đăng ký' })).toHaveAttribute('href', '/dang-ky')
  })
})
