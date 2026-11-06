import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider from '../context/AuthProvider'
import type { Booking } from '../services/bookingService'
import { CONFIRMED_STORAGE_KEY } from '../utils/bookingStorage'
import { CANCEL_RECEIPT, CONFIRMED_BOOKING, jsonResponse, quoteTicket } from '../utils/testBookings'
import BookingPage from './BookingPage'

const fetchMock = vi.fn<typeof fetch>()
const ALL_CANCELLED: Booking = {
  ...CONFIRMED_BOOKING,
  ve: CONFIRMED_BOOKING.ve.map((ve) => ({ ...ve, trang_thai_ve: 'DA_HUY' })),
  tong_tien: 0,
  trang_thai_don: 'DA_HUY',
}
const ONE_LEFT: Booking = {
  ...CONFIRMED_BOOKING,
  ve: [{ ...CONFIRMED_BOOKING.ve[0], trang_thai_ve: 'DA_HUY' }, CONFIRMED_BOOKING.ve[1]],
}

function mockBackend(afterCancel: Booking) {
  let cancelled = false
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.endsWith('/cancel-quote')) {
      return jsonResponse(200, {
        ma_don: 'DH00100000',
        thoi_diem_hien_tai: '2026-12-13T20:00:00Z',
        ve: [quoteTicket({ can_tai_khoan_nhan: false })],
      })
    }
    if (url.endsWith('/cancel-tickets')) {
      cancelled = true
      return jsonResponse(200, CANCEL_RECEIPT)
    }
    if (url.endsWith('/DH00100000')) return jsonResponse(200, cancelled ? afterCancel : CONFIRMED_BOOKING)
    return new Promise<Response>(() => {})
  })
}

function bookingCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/DH00100000'))
}

function renderPage() {
  const router = createMemoryRouter([{ path: '/dat-ve/:maDon', element: <BookingPage /> }], {
    initialEntries: ['/dat-ve/DH00100000'],
  })
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
}

async function cancelFirstTicket() {
  const ticket = await screen.findByRole('listitem', { name: 'Vé VE00100001' })
  fireEvent.click(within(ticket).getByRole('button', { name: 'Hủy vé' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục hủy vé' }))
  fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Đồng ý hủy vé' }))
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
  // Tab có mã truy cập của đơn đã xác nhận
  sessionStorage.setItem(CONFIRMED_STORAGE_KEY, JSON.stringify({ DH00100000: 'ma-bi-mat' }))
})

afterEach(() => {
  fetchMock.mockReset()
  sessionStorage.clear()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('BookingPage: hủy vé đã xác nhận bằng mã truy cập', () => {
  it('hủy hết vé: vẫn hiện biên lai, không chuyển sang màn đặt vé thất bại', async () => {
    mockBackend(ALL_CANCELLED)
    renderPage()

    await cancelFirstTicket()

    expect(await screen.findByRole('heading', { name: 'Hủy vé thành công' })).toBeInTheDocument()
    expect(screen.getByRole('listitem', { name: 'Vé đã hủy VE00100001' })).toHaveTextContent('Chờ hoàn tiền')
    const [, init] = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/cancel-tickets')) ?? []
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
    // Đơn đọc lại là DA_HUY: vẫn ở biên lai, không còn vé để quay lại xem
    await waitFor(() => expect(bookingCalls()).toHaveLength(2))
    expect(screen.getByRole('heading', { name: 'Hủy vé thành công' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xem vé còn lại' })).not.toBeInTheDocument()
  })

  it('hủy một vé: quay lại thấy vé còn lại do backend trả', async () => {
    mockBackend(ONE_LEFT)
    renderPage()

    await cancelFirstTicket()

    fireEvent.click(await screen.findByRole('button', { name: 'Xem vé còn lại' }))
    expect(await screen.findByRole('heading', { name: 'Đặt vé thành công' })).toBeInTheDocument()
    expect(screen.queryByRole('listitem', { name: 'Vé VE00100001' })).not.toBeInTheDocument()
    expect(screen.getByRole('listitem', { name: 'Vé VE00100002' })).toBeInTheDocument()
  })
})
