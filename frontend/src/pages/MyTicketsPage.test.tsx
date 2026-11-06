import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import { routes } from '../routes'
import type { MyBooking } from '../services/bookingService'
import { CANCEL_RECEIPT, CONFIRMED_BOOKING, jsonResponse, quoteTicket } from '../utils/testBookings'

const fetchMock = vi.fn<typeof fetch>()

const ORDERS: MyBooking[] = [
  {
    ma_don: 'DH00100002',
    chuyen: CONFIRMED_BOOKING.chuyen,
    ngay_dat: '2026-12-01T04:00:00Z',
    tong_tien: 200000,
    trang_thai_don: 'DA_XAC_NHAN',
    ve: [CONFIRMED_BOOKING.ve[0]],
  },
  {
    ma_don: 'DH00100001',
    chuyen: CONFIRMED_BOOKING.chuyen,
    ngay_dat: '2026-12-01T03:00:00Z',
    tong_tien: 390000,
    trang_thai_don: 'DA_XAC_NHAN',
    ve: CONFIRMED_BOOKING.ve,
  },
]

function login(vaiTro = 'KHACH') {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', vai_tro: vaiTro, ho_ten: 'Khách Mẫu' }))
}

function mockTickets(response: Response) {
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.endsWith('/me/tickets')) return response.clone()
    // /auth/me khi khôi phục phiên, /health ở trang chủ: giữ treo
    return new Promise<Response>(() => {})
  })
}

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
  return router
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

describe('MyTicketsPage (/ve-cua-toi)', () => {
  it('chưa đăng nhập: chuyển tới trang đăng nhập, không gọi API vé', () => {
    mockTickets(jsonResponse(200, []))
    const router = renderAt('/ve-cua-toi')

    expect(router.state.location.pathname).toBe('/dang-nhap')
    expect(router.state.location.state).toEqual({ from: '/ve-cua-toi' })
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/me/tickets'))).toBe(false)
  })

  it('đăng nhập KHACH: hiện các đơn theo thứ tự backend, vé gom theo mã đơn', async () => {
    login()
    mockTickets(jsonResponse(200, ORDERS))
    renderAt('/ve-cua-toi')

    const list = await screen.findByRole('list', { name: 'Đơn đặt vé' })
    const orders = within(list).getAllByRole('listitem', { name: /^Đơn / })
    expect(orders.map((item) => item.getAttribute('aria-label'))).toEqual(['Đơn DH00100002', 'Đơn DH00100001'])
    const older = within(orders[1]).getByRole('list', { name: 'Vé của đơn DH00100001' })
    expect(within(older).getAllByRole('listitem')).toHaveLength(2)
    expect(orders[1]).toHaveTextContent('Mã vé: VE00100001')
    expect(orders[1]).toHaveTextContent('Chờ thu tiền mặt')
    expect(orders[1]).toHaveTextContent('390.000 đ')
    const [, init] = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/me/tickets')) ?? []
    expect(init?.headers).toMatchObject({ Authorization: 'Bearer tok' })
    expect(screen.getByRole('link', { name: 'Vé của tôi' })).toHaveAttribute('aria-current', 'page')
  })

  it('chưa có vé: hiện thông báo trống', async () => {
    login()
    mockTickets(jsonResponse(200, []))
    renderAt('/ve-cua-toi')

    expect(await screen.findByText('Bạn chưa có vé nào.')).toBeInTheDocument()
  })

  it('lỗi backend: hiện nguyên văn', async () => {
    login()
    mockTickets(jsonResponse(403, { detail: 'Bạn không có quyền thực hiện thao tác này' }))
    renderAt('/ve-cua-toi')

    expect(await screen.findByRole('alert')).toHaveTextContent('Bạn không có quyền thực hiện thao tác này')
  })

  it('vai trò khác: không gọi API, báo trang chỉ dành cho khách', () => {
    login('NHA_XE')
    mockTickets(jsonResponse(200, []))
    renderAt('/ve-cua-toi')

    expect(screen.getByRole('alert')).toHaveTextContent('Trang này chỉ dành cho tài khoản khách hàng.')
    expect(screen.queryByRole('link', { name: 'Vé của tôi' })).not.toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/me/tickets'))).toBe(false)
  })

  it('hủy vé: mức hoàn từ backend, xác nhận trong trang, hiện biên lai và tải lại vé', async () => {
    login()
    fetchMock.mockImplementation(async (input) => {
      const url = String(input)
      if (url.endsWith('/me/tickets')) return jsonResponse(200, ORDERS)
      if (url.endsWith('/DH00100002/cancel-quote')) {
        return jsonResponse(200, {
          ma_don: 'DH00100002',
          thoi_diem_hien_tai: '2026-12-13T20:00:00Z',
          ve: [quoteTicket({ can_tai_khoan_nhan: false, muc_hoan: 0, trang_thai_thanh_toan: 'CHO_THU_TIEN_MAT' })],
        })
      }
      if (url.endsWith('/DH00100002/cancel-tickets')) {
        return jsonResponse(200, {
          ...CANCEL_RECEIPT,
          ma_don: 'DH00100002',
          ve: [{ ...CANCEL_RECEIPT.ve[0], muc_hoan: 0, trang_thai_hoan: 'KHONG_HOAN_TIEN' }],
          tong_hoan: 0,
          ngan_hang_nhan: null,
          so_tai_khoan_nhan: null,
        })
      }
      return new Promise<Response>(() => {})
    })
    renderAt('/ve-cua-toi')

    const order = await screen.findByRole('listitem', { name: 'Đơn DH00100002' })
    fireEvent.click(within(order).getByRole('button', { name: 'Hủy vé' }))
    fireEvent.click(await within(order).findByRole('button', { name: 'Tiếp tục hủy vé' }))
    fireEvent.click(within(order).getByRole('button', { name: 'Đồng ý hủy vé' }))

    expect(await screen.findByRole('heading', { name: 'Hủy vé thành công' })).toBeInTheDocument()
    expect(screen.getByRole('listitem', { name: 'Vé đã hủy VE00100001' })).toHaveTextContent('Không hoàn tiền')
    const [, init] = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/cancel-tickets')) ?? []
    expect(init?.headers).toMatchObject({ Authorization: 'Bearer tok' })
    await waitFor(() =>
      expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/me/tickets'))).toHaveLength(2),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Xem vé còn lại' }))
    expect(await screen.findByRole('list', { name: 'Đơn đặt vé' })).toBeInTheDocument()
  })
})
