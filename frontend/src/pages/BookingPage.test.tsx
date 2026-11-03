import { act, render, screen } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Booking } from '../services/bookingService'
import { saveStoredBooking } from '../utils/bookingStorage'
import BookingPage from './BookingPage'

const fetchMock = vi.fn<typeof fetch>()

const BOOKING: Booking = {
  ma_don: 'DH00100000',
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
  },
  nguoi_dat: { ho_ten: 'Trần Thị Bình', so_dien_thoai: '0905111222', email: null },
  ve: [
    {
      ve_id: 'VE1',
      ghe_id: 'GH1',
      so_ghe: 'A01',
      gia_ve: 200000,
      trang_thai_ve: 'GIU_CHO',
      trang_thai_thanh_toan: 'CHO_THANH_TOAN',
      ho_ten: 'Trần Thị Bình',
      so_dien_thoai: '0905111222',
    },
    {
      ve_id: 'VE2',
      ghe_id: 'GH2',
      so_ghe: 'A02',
      gia_ve: 200000,
      trang_thai_ve: 'GIU_CHO',
      trang_thai_thanh_toan: 'CHO_THANH_TOAN',
      ho_ten: 'Trần Thị Bình',
      so_dien_thoai: '0905111222',
    },
  ],
  // Giá trị riêng của backend: trang chỉ hiển thị, không tự cộng
  tong_tien: 390000,
  han_giu_cho: '2026-12-01T03:20:00Z',
  dang_giu_cho: true,
  thoi_diem_hien_tai: '2026-12-01T03:15:00Z',
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

function renderPage(maDon = 'DH00100000') {
  const router = createMemoryRouter([{ path: '/dat-ve/:maDon', element: <BookingPage /> }], {
    initialEntries: [`/dat-ve/${maDon}`],
  })
  render(<RouterProvider router={router} />)
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
  // Chỉ giả lập đồng hồ và setInterval; setTimeout thật để findBy* chờ được
  vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] })
  vi.setSystemTime(new Date('2026-12-01T03:15:00Z'))
})

afterEach(() => {
  vi.useRealTimers()
  fetchMock.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('BookingPage', () => {
  it('gửi mã truy cập đã lưu và hiện ghế, tổng tiền từ backend', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(jsonResponse(200, BOOKING))

    renderPage()

    expect(await screen.findByText('DH00100000')).toBeInTheDocument()
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toBe('http://api.test/api/v1/bookings/DH00100000')
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })

    const seats = screen.getByRole('list', { name: 'Ghế đã giữ' })
    expect(seats).toHaveTextContent('Ghế A01')
    expect(seats).toHaveTextContent('Ghế A02')
    expect(screen.getByTestId('tong-tien')).toHaveTextContent('390.000 đ')
    expect(screen.getByRole('heading', { name: 'Thông tin hành khách' })).toBeInTheDocument()
  })

  it('đếm ngược theo giờ server, còn 2 phút thì cảnh báo, hết giờ thì báo hết', async () => {
    // Máy khách chậm hơn server 30 giây
    vi.setSystemTime(new Date('2026-12-01T03:14:30Z'))
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(jsonResponse(200, BOOKING))

    renderPage()

    expect(await screen.findByRole('timer')).toHaveTextContent('05:00')
    act(() => {
      vi.advanceTimersByTime(180000)
    })
    expect(screen.getByRole('timer')).toHaveTextContent('02:00')
    expect(screen.getByRole('alert')).toHaveTextContent('Sắp hết thời gian giữ chỗ')

    act(() => {
      vi.advanceTimersByTime(120000)
    })
    expect(screen.getByRole('alert')).toHaveTextContent('Hết thời gian giữ chỗ')
  })

  it('đồng hồ về 0 thì ẩn ngay thông tin hành khách, hiện hết giờ và nút chọn lại ghế', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(jsonResponse(200, BOOKING))

    renderPage()

    expect(await screen.findByRole('timer')).toHaveTextContent('05:00')
    act(() => {
      vi.advanceTimersByTime(299000)
    })
    expect(screen.getByRole('timer')).toHaveTextContent('00:01')
    expect(screen.getByRole('heading', { name: 'Thông tin hành khách' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Chọn lại ghế' })).not.toBeInTheDocument()

    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(screen.queryByRole('heading', { name: 'Thông tin hành khách' })).not.toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Hết thời gian giữ chỗ')
    expect(screen.getByRole('link', { name: 'Chọn lại ghế' })).toHaveAttribute('href', '/chuyen/CX00000001')
    // Không tải lại đơn: chỉ có lần gọi ban đầu
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('đơn đã hết hạn giữ thì báo hết và cho chọn lại ghế', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, { ...BOOKING, dang_giu_cho: false }))

    renderPage()

    expect(await screen.findByText('Hết thời gian giữ chỗ')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Chọn lại ghế' })).toHaveAttribute('href', '/chuyen/CX00000001')
  })

  it('không có quyền xem thì hiện nguyên văn lỗi 404', async () => {
    fetchMock.mockResolvedValue(jsonResponse(404, { detail: 'Không tìm thấy đơn' }))

    renderPage('DH00999999')

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tìm thấy đơn')
    // Không có mã của đơn này thì không gửi header
    const [, init] = fetchMock.mock.calls[0]
    expect(init?.headers).not.toHaveProperty('X-Ma-Truy-Cap')
  })
})
