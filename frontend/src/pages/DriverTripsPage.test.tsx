import { render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import { routes } from '../routes'
import type { DriverTrip } from '../services/driverService'
import { CONFIRMED_BOOKING, jsonResponse } from '../utils/testBookings'

const fetchMock = vi.fn<typeof fetch>()

const TRIP: DriverTrip = { chuyen: CONFIRMED_BOOKING.chuyen, trang_thai: 'MO_BAN', so_khach: 3 }

function login(vaiTro: string) {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', vai_tro: vaiTro, ho_ten: 'Tài Xế' }))
}

function mockBackend(trips: DriverTrip[]) {
  fetchMock.mockImplementation(async (input) => {
    if (String(input).endsWith('/api/v1/driver/trips')) return jsonResponse(200, trips)
    return new Promise<Response>(() => {})
  })
}

function renderAt(path: string) {
  render(
    <AuthProvider>
      <RouterProvider router={createMemoryRouter(routes, { initialEntries: [path] })} />
    </AuthProvider>,
  )
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  sessionStorage.clear()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('DriverTripsPage (/tai-xe)', () => {
  it.each(['KHACH', 'NHA_XE'])('vai trò %s: báo trang chỉ dành cho tài xế, không gọi API', (vaiTro) => {
    login(vaiTro)
    mockBackend([TRIP])
    renderAt('/tai-xe')

    expect(screen.getByRole('alert')).toHaveTextContent('Trang này chỉ dành cho tài khoản tài xế.')
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/driver/'))).toBe(false)
  })

  it('tài xế: danh sách chuyến được phân công, mỗi chuyến dẫn tới trang chi tiết', async () => {
    login('TAI_XE')
    mockBackend([TRIP])
    renderAt('/tai-xe')

    const list = await screen.findByRole('list', { name: 'Chuyến được phân công' })
    const link = within(list).getByRole('link')
    expect(link).toHaveAttribute('href', '/tai-xe/chuyen/CX00000001')
    expect(link).toHaveTextContent('Đà Nẵng - Huế')
    expect(link).toHaveTextContent('06:00 ngày 15/12/2026')
    expect(link).toHaveTextContent('3 khách')
    expect(link).toHaveTextContent('Đang mở bán')
    expect(screen.getByRole('link', { name: 'Chuyến của tôi' })).toHaveAttribute('aria-current', 'page')
  })

  it('chưa có chuyến: hiện thông báo', async () => {
    login('TAI_XE')
    mockBackend([])
    renderAt('/tai-xe')

    expect(await screen.findByText('Bạn chưa được phân công chuyến nào.')).toBeInTheDocument()
  })
})
