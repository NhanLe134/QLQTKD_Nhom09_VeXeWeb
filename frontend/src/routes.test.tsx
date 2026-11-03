import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider from './context/AuthProvider'
import { routes } from './routes'

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  return render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  // Trang chủ gọi /health; giữ request treo để test route không phụ thuộc mạng
  vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(() => {})))
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('routes', () => {
  it('header có tên hệ thống và 3 mục menu', () => {
    renderAt('/')

    expect(screen.getByRole('link', { name: 'VeXe Nhóm 09' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('navigation', { name: 'Menu chính' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tìm chuyến' })).toHaveAttribute('href', '/tim-chuyen')
    expect(screen.getByRole('link', { name: 'Tra cứu vé' })).toHaveAttribute('href', '/tra-cuu-ve')
    expect(screen.getByRole('link', { name: 'Đăng nhập' })).toHaveAttribute('href', '/dang-nhap')
  })

  it('/tra-cuu-ve hiện trang tạm "Đang xây dựng"', () => {
    renderAt('/tra-cuu-ve')

    expect(screen.getByRole('heading', { name: 'Tra cứu vé' })).toBeInTheDocument()
    expect(screen.getByText('Đang xây dựng.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tra cứu vé' })).toHaveAttribute('aria-current', 'page')
  })

  it('/tim-chuyen hiện trang tìm chuyến', () => {
    renderAt('/tim-chuyen')

    expect(screen.getByRole('heading', { name: 'Tìm chuyến' })).toBeInTheDocument()
    expect(screen.getByRole('form', { name: 'Tìm chuyến' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tìm chuyến' })).toHaveAttribute('aria-current', 'page')
  })

  it('/chuyen/:id hiện trang chọn ghế', () => {
    renderAt('/chuyen/CX00000001')

    expect(screen.getByRole('heading', { name: 'Chọn ghế' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Đang tải sơ đồ ghế…')
  })

  it('/dat-ve/:maDon hiện trang đặt vé', () => {
    renderAt('/dat-ve/DH00100000')

    expect(screen.getByRole('heading', { name: 'Đặt vé' })).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Đang tải đơn…')
  })

  it.each([
    ['/dang-nhap', 'Đăng nhập'],
    ['/dang-ky', 'Đăng ký'],
  ])('%s mở được khi chưa đăng nhập', (path, title) => {
    renderAt(path)

    expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
  })

  it('đường dẫn lạ hiện trang 404', () => {
    renderAt('/khong-co-trang-nay')

    expect(screen.getByRole('heading', { name: /404/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toHaveAttribute('href', '/')
  })
})
