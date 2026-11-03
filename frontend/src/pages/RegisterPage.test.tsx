import { fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider from '../context/AuthProvider'
import RegisterPage from './RegisterPage'

const fetchMock = vi.fn<typeof fetch>()

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const VALID = {
  'Họ tên': 'Nguyễn Văn An',
  'Số điện thoại': '0905123456',
  'Email (không bắt buộc)': '',
  'Tên đăng nhập': 'an_nguyen',
  'Mật khẩu': 'matkhau123',
  'Nhập lại mật khẩu': 'matkhau123',
}

function renderRegister() {
  const router = createMemoryRouter(
    [
      { path: '/', element: <h1>Trang chủ</h1> },
      { path: '/dang-ky', element: <RegisterPage /> },
    ],
    { initialEntries: ['/dang-ky'] },
  )
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
}

function fillAndSubmit(overrides: Partial<typeof VALID> = {}) {
  for (const [label, value] of Object.entries({ ...VALID, ...overrides })) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } })
  }
  fireEvent.click(screen.getByRole('button', { name: 'Đăng ký' }))
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

describe('RegisterPage', () => {
  it('báo lỗi các ô bắt buộc để trống và không gọi API', () => {
    renderRegister()

    fireEvent.click(screen.getByRole('button', { name: 'Đăng ký' }))

    expect(screen.getByText('Vui lòng nhập họ tên')).toBeInTheDocument()
    expect(screen.getByText('Vui lòng nhập số điện thoại')).toBeInTheDocument()
    expect(screen.getByText('Vui lòng nhập tên đăng nhập')).toBeInTheDocument()
    expect(screen.getByText('Mật khẩu tối thiểu 8 ký tự')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it.each([
    [{ 'Số điện thoại': '090512345' }, 'Số điện thoại gồm 10 chữ số, bắt đầu bằng 0'],
    [{ 'Số điện thoại': '1905123456' }, 'Số điện thoại gồm 10 chữ số, bắt đầu bằng 0'],
    [{ 'Mật khẩu': '1234567', 'Nhập lại mật khẩu': '1234567' }, 'Mật khẩu tối thiểu 8 ký tự'],
    [{ 'Nhập lại mật khẩu': 'khac-nhau' }, 'Mật khẩu nhập lại không khớp'],
    [{ 'Email (không bắt buộc)': 'khong-phai-email' }, 'Email không hợp lệ'],
  ])('báo lỗi sớm %j', (overrides, message) => {
    renderRegister()

    fillAndSubmit(overrides)

    expect(screen.getByText(message)).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('hiện nguyên văn lỗi 409 từ backend', async () => {
    fetchMock.mockResolvedValue(jsonResponse(409, { detail: 'Số điện thoại đã được đăng ký' }))
    renderRegister()

    fillAndSubmit()

    expect(await screen.findByRole('alert')).toHaveTextContent('Số điện thoại đã được đăng ký')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('đăng ký thành công: gửi đúng dữ liệu, tự đăng nhập và về trang chủ', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse(201, { user_id: 'TK00100000' }))
      .mockResolvedValueOnce(
        jsonResponse(200, { access_token: 't', token_type: 'bearer', vai_tro: 'KHACH', ho_ten: 'Nguyễn Văn An' }),
      )
    renderRegister()

    fillAndSubmit({ 'Họ tên': '  Nguyễn Văn An ' })

    expect(await screen.findByRole('heading', { name: 'Trang chủ' })).toBeInTheDocument()
    const [registerUrl, registerInit] = fetchMock.mock.calls[0]
    expect(registerUrl).toBe('http://api.test/api/v1/auth/register')
    expect(JSON.parse(String(registerInit?.body))).toEqual({
      ten_dang_nhap: 'an_nguyen',
      mat_khau: 'matkhau123',
      ho_ten: 'Nguyễn Văn An',
      so_dien_thoai: '0905123456',
      email: null,
    })
    expect(fetchMock.mock.calls[1][0]).toBe('http://api.test/api/v1/auth/login')
  })
})
