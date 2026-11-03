import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider from '../context/AuthProvider'
import type { Booking } from '../services/bookingService'
import { accessCodeFor, readStoredBooking, saveStoredBooking } from '../utils/bookingStorage'
import { CONFIRMED_BOOKING, jsonResponse, SAVED_BOOKING } from '../utils/testBookings'
import BookingPage from './BookingPage'

const fetchMock = vi.fn<typeof fetch>()

const QR_SE_PAY = {
  ma_don: 'DH00100000',
  so_tien: 390000,
  noi_dung: 'THANH TOAN VE DH00100000',
  qr_url: 'https://img.vietqr.io/image/qr.png',
  thoi_gian_cho_giay: 300,
}

/** GET đơn trả lần lượt `get`; POST pay-sepay trả `qr`. */
function mockBackend({ get, qr }: { get: Booking[]; qr?: Response }) {
  let index = 0
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.endsWith('/pay-sepay')) return (qr ?? jsonResponse(200, QR_SE_PAY)).clone()
    if (url.endsWith('/auth/me')) return new Promise<Response>(() => {})
    const body = get[Math.min(index, get.length - 1)]
    index += 1
    return jsonResponse(200, body)
  })
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

async function goToTransfer() {
  fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục thanh toán' }))
  fireEvent.click(screen.getByRole('button', { name: /Chuyển khoản SePay/ }))
  return screen.findByTestId('qr-se-pay-panel')
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
  vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] })
  vi.setSystemTime(new Date('2026-12-01T03:15:00Z'))
  saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
})

afterEach(() => {
  vi.useRealTimers()
  fetchMock.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  sessionStorage.clear()
  cleanup()
})

describe('BookingPage — thanh toán chuyển khoản SePay', () => {
  it('chọn chuyển khoản: hiện QR đúng tiền, nội dung và đồng hồ 5 phút', async () => {
    mockBackend({ get: [SAVED_BOOKING] })
    renderPage()

    await goToTransfer()

    expect(screen.getByTestId('qr-se-pay-so-tien')).toHaveTextContent('390.000 đ')
    expect(screen.getByTestId('qr-se-pay-noi-dung')).toHaveTextContent('THANH TOAN VE DH00100000')
    expect(screen.getByTestId('qr-se-pay-hinh')).toHaveAttribute('src', QR_SE_PAY.qr_url)
    expect(
      screen.getByRole('timer', { name: 'Thời gian chuyển khoản còn lại' }),
    ).toHaveTextContent('05:00')
    // Gọi đúng endpoint với mã truy cập của khách vãng lai
    const [, init] = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/pay-sepay')) ?? []
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
  })

  it('webhook xác nhận ở backend: trang tự chuyển "Đặt vé thành công" (US-BUS-05 AC2)', async () => {
    // GET lần 1: tải đơn; lần 2: tải lại sau khi tạo QR (ghế được gia hạn);
    // lần 3 (poll 2s): đơn đã xác nhận nhờ webhook
    mockBackend({ get: [SAVED_BOOKING, SAVED_BOOKING, CONFIRMED_BOOKING] })
    renderPage()

    await goToTransfer()
    await vi.advanceTimersByTimeAsync(3000)

    expect(await screen.findByRole('heading', { name: 'Đặt vé thành công' })).toBeInTheDocument()
    // Mã truy cập chuyển sang kho đơn đã xác nhận để tải lại trang vẫn xem được vé
    expect(readStoredBooking()).toBeNull()
    expect(accessCodeFor('DH00100000')).toBe('ma-bi-mat')
  })

  it('hết 5 phút: cảnh báo quá thời gian chuyển khoản, đơn vẫn đang giữ', async () => {
    // Giữ chỗ 10 phút: hết 5 phút chuyển khoản thì ghế vẫn còn giữ
    const booking = { ...SAVED_BOOKING, han_giu_cho: '2026-12-01T03:25:00Z' }
    mockBackend({ get: [booking] })
    renderPage()

    await goToTransfer()
    await vi.advanceTimersByTimeAsync(5 * 60 * 1000)

    expect(screen.getByRole('alert')).toHaveTextContent('Quá thời gian chuyển khoản')
    // Đơn vẫn đang giữ: đồng hồ giữ chỗ còn hiển thị
    expect(screen.getByRole('timer', { name: 'Thời gian giữ chỗ còn lại' })).toBeInTheDocument()
  })

  it('pay-sepay lỗi backend: hiện thông báo, không có QR', async () => {
    mockBackend({
      get: [SAVED_BOOKING],
      qr: jsonResponse(503, { detail: 'Chưa cấu hình thanh toán SePay' }),
    })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục thanh toán' }))
    fireEvent.click(screen.getByRole('button', { name: /Chuyển khoản SePay/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Chưa cấu hình thanh toán SePay')
    expect(screen.queryByTestId('qr-se-pay-panel')).not.toBeInTheDocument()
  })
})
