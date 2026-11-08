import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'

import AuthProvider from '../context/AuthProvider'
import HomePage from './HomePage'

const fetchMock = vi.fn<typeof fetch>()

function renderHome() {
  return render(
    // Trang chủ đọc tài khoản (nút "Vé của tôi"/"Tra cứu vé đã đặt") nên cần AuthProvider
    <AuthProvider>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </AuthProvider>,
  )
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

it('hiện "đang kiểm tra" khi chưa có phản hồi', () => {
  fetchMock.mockReturnValue(new Promise<Response>(() => {}))

  renderHome()

  expect(screen.getByRole('status')).toHaveTextContent('Đang kiểm tra kết nối backend…')
})

it('hiện "đã kết nối" khi /health trả ok', async () => {
  fetchMock.mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }), { status: 200 }))

  renderHome()

  expect(await screen.findByText('Đã kết nối backend.')).toBeInTheDocument()
  expect(fetchMock).toHaveBeenCalledWith('http://api.test/health', expect.anything())
})

it('hiện lỗi khi không kết nối được backend', async () => {
  fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

  renderHome()

  expect(
    await screen.findByText('Không kết nối được backend: Không kết nối được máy chủ. Vui lòng thử lại.'),
  ).toBeInTheDocument()
})
