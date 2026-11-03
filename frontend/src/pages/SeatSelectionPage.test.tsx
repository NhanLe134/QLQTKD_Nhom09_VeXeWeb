import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import type { Seat, SeatMap, SeatStatus } from '../services/tripService'
import { readStoredBooking, saveStoredBooking } from '../utils/bookingStorage'
import SeatSelectionPage from './SeatSelectionPage'

const fetchMock = vi.fn<typeof fetch>()

function seats(...statuses: SeatStatus[]): Seat[] {
  return statuses.map((trang_thai, index) => ({
    ghe_id: `GH0000000${index + 1}`,
    so_ghe: `A0${index + 1}`,
    trang_thai,
  }))
}

function seatMap(ghe: Seat[], overrides: Partial<SeatMap['chuyen']> = {}, coTheDat = true): SeatMap {
  return {
    chuyen: {
      chuyen_xe_id: 'CX00000001',
      ten_tuyen: 'Đà Nẵng - Huế',
      diem_di: 'Đà Nẵng',
      diem_den: 'Huế',
      diem_trung_gian: 'Lăng Cô',
      ngay_khoi_hanh: '2026-12-15',
      gio_di: '2026-12-14T23:00:00Z',
      gio_den: '2026-12-15T01:30:00Z',
      ten_loai_xe: 'Xe 4 chỗ',
      so_cho: 4,
      gia_ve: 200000,
      ...overrides,
    },
    co_the_dat: coTheDat,
    ghe,
    thoi_diem_hien_tai: '2026-12-01T03:15:00Z',
  }
}

const HOLD_RESPONSE = {
  ma_don: 'DH00100000',
  ma_truy_cap: 'ma-bi-mat',
  han_giu_cho: '2026-12-01T03:20:00Z',
  thoi_diem_hien_tai: '2026-12-01T03:15:00Z',
  ghe: [],
  tong_tien: 400000,
}

const ME = {
  user_id: 'TK00000001',
  ten_dang_nhap: 'khach_mau',
  vai_tro: 'KHACH',
  so_dien_thoai: '0900000001',
  khach_hang: {
    khach_hang_id: 'KH00000001',
    ho_ten: 'Khách Mẫu',
    email: null,
    so_dien_thoai: '0900000001',
    ngay_dang_ky: '2026-11-01T00:00:00Z',
  },
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

type Handlers = {
  seatMaps: SeatMap[]
  hold?: () => Response
  booking?: () => Response
  cancel?: () => Response
}

/** Giả lập backend; sơ đồ ghế trả lần lượt theo `seatMaps` (lần cuối lặp lại). */
function mockBackend({ seatMaps, hold, booking, cancel }: Handlers) {
  let seatCalls = 0
  fetchMock.mockImplementation(async (input) => {
    const url = new URL(String(input))
    if (url.pathname.endsWith('/seats')) {
      const data = seatMaps[Math.min(seatCalls, seatMaps.length - 1)]
      seatCalls += 1
      return jsonResponse(200, data)
    }
    if (url.pathname === '/api/v1/bookings/hold') {
      return hold ? hold() : jsonResponse(201, HOLD_RESPONSE)
    }
    if (url.pathname.endsWith('/cancel')) {
      return cancel ? cancel() : jsonResponse(404, { detail: 'Không tìm thấy đơn' })
    }
    if (url.pathname.startsWith('/api/v1/bookings/')) {
      return booking ? booking() : jsonResponse(404, { detail: 'Không tìm thấy đơn' })
    }
    if (url.pathname === '/api/v1/auth/me') {
      return jsonResponse(200, ME)
    }
    return jsonResponse(404, { detail: 'Không tìm thấy' })
  })
}

function renderPage() {
  const router = createMemoryRouter(
    [
      { path: '/chuyen/:id', element: <SeatSelectionPage /> },
      { path: '/dat-ve/:maDon', element: <h1>Trang đặt vé</h1> },
    ],
    { initialEntries: ['/chuyen/CX00000001'] },
  )
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
  return router
}

function seatButton(code: string) {
  return screen.getByRole('button', { name: new RegExp(`^Ghế ${code} `) })
}

function holdCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/bookings/hold'))
}

function holdBody(): unknown {
  const [, init] = holdCalls()[0]
  return JSON.parse(String(init?.body))
}

function fillGuest() {
  fireEvent.change(screen.getByLabelText('Họ tên'), { target: { value: 'Trần Thị Bình' } })
  fireEvent.change(screen.getByLabelText('Số điện thoại'), { target: { value: '0905111222' } })
  fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))
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

describe('SeatSelectionPage', () => {
  it('hiện thông tin chuyến, giá mỗi ghế và sơ đồ ghế, không tự tính tổng tiền', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'GIU_CHO', 'DA_BAN', 'TRONG'))] })

    renderPage()

    expect(await screen.findByText('Đà Nẵng - Huế')).toBeInTheDocument()
    expect(screen.getByText('200.000 đ')).toBeInTheDocument()
    expect(screen.getByText(/Xe 4 chỗ/)).toBeInTheDocument()
    expect(seatButton('A02')).toBeDisabled()
    expect(seatButton('A03')).toBeDisabled()
    expect(screen.queryByText(/Tổng/)).not.toBeInTheDocument()
  })

  it('chọn và bỏ chọn ghế, hiện số ghế đã chọn', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))] })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    fireEvent.click(seatButton('A03'))
    fireEvent.click(seatButton('A01'))
    expect(seatButton('A01')).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText(/Đã chọn/)).toHaveTextContent('Đã chọn: 2 ghế (A01, A03)')

    fireEvent.click(seatButton('A01'))
    expect(seatButton('A01')).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByText(/Đã chọn/)).toHaveTextContent('Đã chọn: 1 ghế (A03)')
  })

  it('không cho chọn quá số chỗ của xe', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG'), { so_cho: 2 })] })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    fireEvent.click(seatButton('A01'))
    fireEvent.click(seatButton('A02'))
    fireEvent.click(seatButton('A03'))

    expect(screen.getByRole('alert')).toHaveTextContent('Chỉ chọn được tối đa 2 ghế.')
    expect(seatButton('A03')).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByText(/Đã chọn/)).toHaveTextContent('Đã chọn: 2 ghế')
  })

  it('nút Giữ ghế khóa khi chưa chọn ghế', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))] })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    expect(screen.getByRole('button', { name: 'Giữ ghế' })).toBeDisabled()
    fireEvent.click(seatButton('A01'))
    expect(screen.getByRole('button', { name: 'Giữ ghế' })).toBeEnabled()
  })

  it('"Đặt cả xe" bị khóa khi đã có 1 ghế bị giữ', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'GIU_CHO', 'TRONG', 'TRONG'))] })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    expect(screen.getByRole('button', { name: 'Đặt cả xe' })).toBeDisabled()
  })

  it('chuyến không còn nhận đặt thì khóa giữ ghế và đặt cả xe', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'), {}, false)] })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    expect(screen.getByText('Chuyến này hiện không nhận đặt vé.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Đặt cả xe' })).toBeDisabled()
    expect(seatButton('A01')).toBeDisabled()
  })

  it('đặt cả xe: gửi dat_ca_xe, lưu mã truy cập và chuyển sang trang đặt vé', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))] })
    const router = renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    fireEvent.click(screen.getByRole('button', { name: 'Đặt cả xe' }))
    expect(screen.getByRole('heading', { name: 'Đặt cả xe (4 ghế)' })).toBeInTheDocument()
    fillGuest()

    expect(await screen.findByRole('heading', { name: 'Trang đặt vé' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/dat-ve/DH00100000')
    expect(holdBody()).toEqual({
      chuyen_xe_id: 'CX00000001',
      dat_ca_xe: true,
      nguoi_dat: { ho_ten: 'Trần Thị Bình', so_dien_thoai: '0905111222', email: null },
    })
    expect(readStoredBooking()).toEqual({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
  })

  it('khách vãng lai giữ ghế đã chọn với thông tin người đặt', async () => {
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))] })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    fireEvent.click(seatButton('A02'))
    fireEvent.click(seatButton('A04'))
    fireEvent.click(screen.getByRole('button', { name: 'Giữ ghế' }))
    fillGuest()

    expect(await screen.findByRole('heading', { name: 'Trang đặt vé' })).toBeInTheDocument()
    expect(holdBody()).toEqual({
      chuyen_xe_id: 'CX00000001',
      ghe_ids: ['GH00000002', 'GH00000004'],
      nguoi_dat: { ho_ten: 'Trần Thị Bình', so_dien_thoai: '0905111222', email: null },
    })
  })

  it('khách đã đăng nhập chỉ xác nhận, không gửi nguoi_dat', async () => {
    sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', ho_ten: 'Khách Mẫu', vai_tro: 'KHACH' }))
    mockBackend({ seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))] })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    fireEvent.click(seatButton('A01'))
    fireEvent.click(screen.getByRole('button', { name: 'Giữ ghế' }))
    expect(await screen.findByText('Khách Mẫu')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))

    expect(await screen.findByRole('heading', { name: 'Trang đặt vé' })).toBeInTheDocument()
    expect(holdBody()).toEqual({ chuyen_xe_id: 'CX00000001', ghe_ids: ['GH00000001'] })
  })

  it('409: hiện nguyên văn lỗi, tải lại sơ đồ ghế và bỏ chọn ghế đã bị giữ', async () => {
    mockBackend({
      seatMaps: [
        seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG')),
        seatMap(seats('GIU_CHO', 'TRONG', 'TRONG', 'TRONG')),
      ],
      hold: () => jsonResponse(409, { detail: 'Ghế đã được giữ' }),
    })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    fireEvent.click(seatButton('A01'))
    fireEvent.click(seatButton('A02'))
    fireEvent.click(screen.getByRole('button', { name: 'Giữ ghế' }))
    fillGuest()

    expect(await screen.findByRole('alert')).toHaveTextContent('Ghế đã được giữ')
    await waitFor(() => expect(seatButton('A01')).toHaveAccessibleName('Ghế A01 (đang giữ)'))
    expect(seatButton('A01')).toBeDisabled()
    expect(screen.getByText(/Đã chọn/)).toHaveTextContent('Đã chọn: 1 ghế (A02)')
    expect(readStoredBooking()).toBeNull()
  })

  it('đang có đơn giữ ghế trong tab: nhắc, cho mở lại đơn và khóa giữ ghế mới', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockBackend({
      seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))],
      booking: () => jsonResponse(200, { ma_don: 'DH00100000', dang_giu_cho: true }),
    })
    renderPage()

    expect(await screen.findByRole('link', { name: 'Mở lại đơn DH00100000' })).toHaveAttribute(
      'href',
      '/dat-ve/DH00100000',
    )
    expect(screen.getByRole('button', { name: 'Đặt cả xe' })).toBeDisabled()
    expect(seatButton('A01')).toBeDisabled()
    const bookingCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/bookings/DH00100000'))
    expect(bookingCall?.[1]?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
  })

  it('"Hủy đơn cũ": xác nhận, gọi API hủy, xóa đơn khỏi tab và cho giữ ghế mới', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockBackend({
      seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))],
      booking: () => jsonResponse(200, { ma_don: 'DH00100000', dang_giu_cho: true }),
      cancel: () => jsonResponse(200, { ma_don: 'DH00100000', trang_thai_don: 'DA_HUY' }),
    })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Hủy đơn cũ' }))
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý hủy' }))

    await waitFor(() => expect(screen.queryByRole('link', { name: /Mở lại đơn/ })).not.toBeInTheDocument())
    const cancelCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/bookings/DH00100000/cancel'))
    expect(cancelCall?.[1]?.method).toBe('POST')
    expect(cancelCall?.[1]?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
    expect(readStoredBooking()).toBeNull()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Đặt cả xe' })).toBeEnabled())
    expect(seatButton('A01')).toBeEnabled()
  })

  it('bỏ qua "Hủy đơn cũ" thì vẫn giữ đơn cũ', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockBackend({
      seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))],
      booking: () => jsonResponse(200, { ma_don: 'DH00100000', dang_giu_cho: true }),
    })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Hủy đơn cũ' }))
    fireEvent.click(screen.getByRole('button', { name: 'Không hủy' }))

    expect(screen.getByRole('link', { name: 'Mở lại đơn DH00100000' })).toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/cancel'))).toBe(false)
    expect(readStoredBooking()).not.toBeNull()
  })

  it('đơn đã lưu hết hạn giữ thì xóa khỏi tab và cho giữ ghế mới', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockBackend({
      seatMaps: [seatMap(seats('TRONG', 'TRONG', 'TRONG', 'TRONG'))],
      booking: () => jsonResponse(200, { ma_don: 'DH00100000', dang_giu_cho: false }),
    })
    renderPage()
    await screen.findByText('Đà Nẵng - Huế')

    await waitFor(() => expect(readStoredBooking()).toBeNull())
    expect(screen.queryByRole('link', { name: /Mở lại đơn/ })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Đặt cả xe' })).toBeEnabled()
  })
})
