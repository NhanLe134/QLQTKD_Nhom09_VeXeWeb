import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import type { Booking } from '../services/bookingService'
import { accessCodeFor, readStoredBooking, saveStoredBooking } from '../utils/bookingStorage'
import { CONFIRMED_BOOKING, jsonResponse, SAVED_BOOKING } from '../utils/testBookings'
import BookingPage from './BookingPage'

const fetchMock = vi.fn<typeof fetch>()

const EXPIRED: Booking = { ...SAVED_BOOKING, dang_giu_cho: false, trang_thai_don: 'HET_HAN' }

type Routes = { get: Booking[]; confirm?: Response }

/** GET đơn trả lần lượt `get` (phần tử cuối dùng cho các lần sau); POST confirm-cash trả `confirm`. */
function mockBackend({ get, confirm }: Routes) {
  let index = 0
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.endsWith('/confirm-cash')) return (confirm ?? jsonResponse(200, CONFIRMED_BOOKING)).clone()
    if (url.endsWith('/auth/me')) return new Promise<Response>(() => {})
    const body = get[Math.min(index, get.length - 1)]
    index += 1
    return jsonResponse(200, body)
  })
}

function confirmCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/confirm-cash'))
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

async function goToCashDialog() {
  fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục thanh toán' }))
  fireEvent.click(screen.getByRole('button', { name: /Tiền mặt khi lên xe/ }))
  return screen.getByRole('alertdialog')
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
})

describe('BookingPage — thanh toán tiền mặt', () => {
  it('bước chọn phương thức: tổng tiền từ backend, chuyển khoản vô hiệu, đồng hồ và nút hủy vẫn còn', async () => {
    mockBackend({ get: [SAVED_BOOKING] })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục thanh toán' }))

    expect(screen.getByRole('region', { name: 'Chọn phương thức thanh toán' })).toBeInTheDocument()
    expect(screen.getByTestId('tong-tien-thanh-toan')).toHaveTextContent('390.000 đ')
    expect(screen.getByRole('button', { name: /Chuyển khoản SePay/ })).toBeDisabled()
    expect(screen.getByRole('timer', { name: 'Thời gian giữ chỗ còn lại' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Hủy đặt vé' })).toBeInTheDocument()
  })

  it('hộp xác nhận: bỏ qua thì quay lại chọn phương thức, không gọi backend', async () => {
    mockBackend({ get: [SAVED_BOOKING] })
    renderPage()

    const dialog = await goToCashDialog()
    expect(dialog).toHaveTextContent('Bạn sẽ trả 390.000 đ cho tài xế khi lên xe')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Quay lại' }))

    expect(screen.getByRole('region', { name: 'Chọn phương thức thanh toán' })).toBeInTheDocument()
    expect(confirmCalls()).toHaveLength(0)
  })

  it('đồng ý: hiện "Đặt vé thành công" đủ vé, trạng thái và tổng tiền từ backend', async () => {
    mockBackend({ get: [SAVED_BOOKING] })
    renderPage()

    const dialog = await goToCashDialog()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Đồng ý' }))

    expect(await screen.findByRole('heading', { name: 'Đặt vé thành công' })).toBeInTheDocument()
    expect(confirmCalls()).toHaveLength(1)
    expect(screen.getByText('DH00100000')).toBeInTheDocument()
    const tickets = within(screen.getByRole('list', { name: 'Vé điện tử' })).getAllByRole('listitem')
    expect(tickets).toHaveLength(2)
    expect(tickets[0]).toHaveTextContent('Mã vé: VE00100001')
    expect(tickets[0]).toHaveTextContent('Ghế A01')
    expect(tickets[0]).toHaveTextContent('Trần Thị Bình')
    expect(tickets[0]).toHaveTextContent('Lăng Cô – 12 Lê Lợi')
    expect(tickets[0]).toHaveTextContent('Chờ thu tiền mặt')
    expect(tickets[1]).toHaveTextContent('Mã vé: VE00100002')
    expect(screen.getByTestId('tong-tien')).toHaveTextContent('390.000 đ')
    expect(screen.getByRole('link', { name: 'Về trang chủ' })).toHaveAttribute('href', '/')
    // Khách vãng lai: không có "Vé của tôi"
    expect(screen.queryByRole('link', { name: 'Vé của tôi' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Hủy đặt vé' })).not.toBeInTheDocument()
    // Mã truy cập vẫn giữ để tải lại trang xem được vé
    expect(readStoredBooking()).toBeNull()
    expect(accessCodeFor('DH00100000')).toBe('ma-bi-mat')
  })

  it('khách đã đăng nhập thấy nút "Vé của tôi"', async () => {
    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 't', vai_tro: 'KHACH', ho_ten: 'An' }))
    mockBackend({ get: [CONFIRMED_BOOKING] })
    renderPage()

    expect(await screen.findByRole('link', { name: 'Vé của tôi' })).toHaveAttribute('href', '/ve-cua-toi')
  })

  it('tải lại trang đơn DA_XAC_NHAN: hiện thẳng vé, gửi mã truy cập đã lưu', async () => {
    mockBackend({ get: [SAVED_BOOKING] })
    renderPage()
    fireEvent.click(within(await goToCashDialog()).getByRole('button', { name: 'Đồng ý' }))
    await screen.findByRole('heading', { name: 'Đặt vé thành công' })
    // Giả lập tải lại trang: dựng lại trang, backend trả đơn đã xác nhận
    fetchMock.mockReset()
    mockBackend({ get: [CONFIRMED_BOOKING] })
    cleanup()

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Đặt vé thành công' })).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    const [, init] = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/DH00100000')) ?? []
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
  })

  it('bấm "Đồng ý" liên tiếp chỉ gửi một lần', async () => {
    let resolve: (response: Response) => void = () => {}
    mockBackend({ get: [SAVED_BOOKING] })
    const base = fetchMock.getMockImplementation()
    fetchMock.mockImplementation((input, init) =>
      String(input).endsWith('/confirm-cash')
        ? new Promise<Response>((r) => (resolve = r))
        : (base as typeof fetch)(input, init),
    )
    renderPage()

    const dialog = await goToCashDialog()
    const button = within(dialog).getByRole('button', { name: 'Đồng ý' })
    fireEvent.click(button)
    fireEvent.click(button)

    expect(confirmCalls()).toHaveLength(1)
    resolve(jsonResponse(200, CONFIRMED_BOOKING))
    expect(await screen.findByRole('heading', { name: 'Đặt vé thành công' })).toBeInTheDocument()
    expect(confirmCalls()).toHaveLength(1)
  })

  it('410: tải lại đơn và hiện BookingFailed với lý do', async () => {
    mockBackend({
      get: [SAVED_BOOKING, EXPIRED],
      confirm: jsonResponse(410, { detail: 'Giữ chỗ đã hết hạn' }),
    })
    renderPage()

    fireEvent.click(within(await goToCashDialog()).getByRole('button', { name: 'Đồng ý' }))

    expect(await screen.findByRole('heading', { name: 'Đặt vé thất bại' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Hết thời gian giữ chỗ')
  })

  it('400 kèm truong: mở lại form, báo lỗi ngay dưới ô điểm đón', async () => {
    mockBackend({
      get: [SAVED_BOOKING],
      confirm: jsonResponse(400, { detail: 'Chưa nhập điểm đón/trả', truong: 'diem_don.khu_vuc' }),
    })
    renderPage()

    fireEvent.click(within(await goToCashDialog()).getByRole('button', { name: 'Đồng ý' }))

    await waitFor(() => expect(screen.getByLabelText('Điểm đón')).toHaveAccessibleDescription('Chưa nhập điểm đón/trả'))
    expect(screen.getByRole('button', { name: 'Lưu thông tin' })).toBeInTheDocument()
  })
})
