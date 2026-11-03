import { render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { routes } from './routes'

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  return render(<RouterProvider router={router} />)
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

  it.each([
    ['/tim-chuyen', 'Tìm chuyến'],
    ['/tra-cuu-ve', 'Tra cứu vé'],
    ['/dang-nhap', 'Đăng nhập'],
  ])('%s hiện trang tạm "Đang xây dựng"', (path, title) => {
    renderAt(path)

    expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
    expect(screen.getByText('Đang xây dựng.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: title })).toHaveAttribute('aria-current', 'page')
  })

  it('đường dẫn lạ hiện trang 404', () => {
    renderAt('/khong-co-trang-nay')

    expect(screen.getByRole('heading', { name: /404/ })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toHaveAttribute('href', '/')
  })
})
