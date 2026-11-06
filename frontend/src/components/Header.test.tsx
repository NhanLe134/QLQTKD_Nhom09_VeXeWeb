import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import Header from './Header'

function renderHeader() {
  render(
    <AuthProvider>
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    </AuthProvider>,
  )
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  // /me khi khởi động: giữ treo, test này chỉ kiểm tra giao diện
  vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => {})))
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('Header', () => {
  it('chưa đăng nhập: hiện "Đăng nhập"', () => {
    renderHeader()

    // Bản điện thoại và bản máy tính đều có nút "Đăng nhập"
    const loginLinks = screen.getAllByRole('link', { name: 'Đăng nhập' })
    expect(loginLinks).toHaveLength(2)
    for (const link of loginLinks) expect(link).toHaveAttribute('href', '/dang-nhap')
    expect(screen.queryByRole('button', { name: 'Đăng xuất' })).not.toBeInTheDocument()
  })

  it('đã đăng nhập: hiện họ tên và "Đăng xuất"; bấm đăng xuất thì quay lại "Đăng nhập"', () => {
    sessionStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({ token: 't', vai_tro: 'KHACH', ho_ten: 'Nguyễn Văn An' }),
    )
    renderHeader()

    // Bản điện thoại và bản máy tính đều hiện họ tên và nút "Đăng xuất"
    expect(screen.getAllByText('Nguyễn Văn An')).toHaveLength(2)
    expect(screen.queryByRole('link', { name: 'Đăng nhập' })).not.toBeInTheDocument()
    const logoutButtons = screen.getAllByRole('button', { name: 'Đăng xuất' })
    expect(logoutButtons).toHaveLength(2)

    fireEvent.click(logoutButtons[0])

    expect(screen.getAllByRole('link', { name: 'Đăng nhập' })).toHaveLength(2)
    expect(screen.queryByRole('button', { name: 'Đăng xuất' })).not.toBeInTheDocument()
    expect(screen.queryByText('Nguyễn Văn An')).not.toBeInTheDocument()
    expect(sessionStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
  })

  it('khách đã đăng nhập thấy "Vé của tôi"; chưa đăng nhập hoặc vai trò khác thì không', () => {
    renderHeader()
    expect(screen.queryByRole('link', { name: 'Vé của tôi' })).not.toBeInTheDocument()
    cleanup()

    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 't', vai_tro: 'TAI_XE', ho_ten: 'Tài Xế' }))
    renderHeader()
    expect(screen.queryByRole('link', { name: 'Vé của tôi' })).not.toBeInTheDocument()
    cleanup()

    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 't', vai_tro: 'KHACH', ho_ten: 'An' }))
    renderHeader()
    expect(screen.getByRole('link', { name: 'Vé của tôi' })).toHaveAttribute('href', '/ve-cua-toi')
    expect(screen.queryByRole('link', { name: 'Tra cứu vé' })).not.toBeInTheDocument()
  })
})
