import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Booking } from '../services/bookingService'
import { readStoredBooking, saveStoredBooking } from '../utils/bookingStorage'
import { HELD_BOOKING, jsonResponse, SAVED_BOOKING } from '../utils/testBookings'
import BookingPage from './BookingPage'

const fetchMock = vi.fn<typeof fetch>()

const BOOKING: Booking = HELD_BOOKING

const CANCELLED: Booking = {
  ...BOOKING,
  ve: BOOKING.ve.map((ve) => ({ ...ve, trang_thai_ve: 'DA_HUY' })),
  tong_tien: 0,
  han_giu_cho: null,
  dang_giu_cho: false,
  trang_thai_don: 'DA_HUY',
}

/** GET đơn trả `booking`, POST hủy trả `cancelled`; mỗi lần gọi một Response mới. */
function mockBackend(booking: Booking, cancelled: Booking = CANCELLED) {
  fetchMock.mockImplementation(async (input) =>
    String(input).endsWith('/cancel') ? jsonResponse(200, cancelled) : jsonResponse(200, booking),
  )
}

/** GET đơn trả lần lượt `gets` (phần tử cuối dùng cho các lần sau), PUT details trả `putResponse`. */
function mockDetailsBackend(gets: Booking[], putResponse: Response | (() => Response)) {
  let getIndex = 0
  fetchMock.mockImplementation(async (input, init) => {
    if (String(input).endsWith('/details') && init?.method === 'PUT') {
      return typeof putResponse === 'function' ? putResponse() : putResponse.clone()
    }
    const body = gets[Math.min(getIndex, gets.length - 1)]
    getIndex += 1
    return jsonResponse(200, body)
  })
}

function putCalls() {
  return fetchMock.mock.calls.filter(([input, init]) => String(input).endsWith('/details') && init?.method === 'PUT')
}

function cancelCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/cancel'))
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
    await act(async () => {})
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

  it('đồng hồ về 0 thì hiện màn đặt vé thất bại vì hết giờ và xóa đơn khỏi tab', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(jsonResponse(200, BOOKING))

    renderPage()

    expect(await screen.findByRole('timer')).toHaveTextContent('05:00')
    await act(async () => {})
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
    expect(screen.getByRole('heading', { name: 'Đặt vé thất bại' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Hết thời gian giữ chỗ')
    expect(screen.getByRole('link', { name: 'Chọn lại ghế' })).toHaveAttribute('href', '/chuyen/CX00000001')
    expect(screen.getByRole('link', { name: 'Tìm chuyến khác' })).toHaveAttribute('href', '/tim-chuyen')
    expect(readStoredBooking()).toBeNull()
    // Không tải lại đơn: chỉ có lần gọi ban đầu
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it.each([
    ['HET_HAN', 'Hết thời gian giữ chỗ'],
    ['DA_HUY', 'Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ'],
  ] as const)('mở lại đơn %s: hiện màn thất bại theo trạng thái backend, xóa đơn khỏi tab', async (status, message) => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(
      jsonResponse(200, { ...(status === 'DA_HUY' ? CANCELLED : BOOKING), dang_giu_cho: false, trang_thai_don: status }),
    )

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Đặt vé thất bại' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(message)
    expect(screen.getByRole('link', { name: 'Chọn lại ghế' })).toHaveAttribute('href', '/chuyen/CX00000001')
    expect(screen.queryByRole('button', { name: 'Hủy đặt vé' })).not.toBeInTheDocument()
    // Xóa đơn khỏi tab chạy trong effect sau khi hiện màn thất bại (D-42)
    await vi.waitFor(() => expect(readStoredBooking()).toBeNull())
  })

  it('mở đơn không phải của tab thì không xóa đơn đang lưu', async () => {
    saveStoredBooking({ ma_don: 'DH00100001', ma_truy_cap: 'ma-khac' })
    fetchMock.mockResolvedValue(jsonResponse(200, CANCELLED))

    renderPage()

    expect(await screen.findByRole('heading', { name: 'Đặt vé thất bại' })).toBeInTheDocument()
    expect(readStoredBooking()).toEqual({ ma_don: 'DH00100001', ma_truy_cap: 'ma-khac' })
  })

  it('hủy đặt vé: xác nhận trong trang, gọi API hủy, xóa đơn và báo đã hủy', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockBackend(BOOKING)

    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Hủy đặt vé' }))
    expect(screen.getByRole('alertdialog')).toBeInTheDocument()
    expect(cancelCalls()).toHaveLength(0)
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý hủy' }))

    expect(await screen.findByRole('heading', { name: 'Đặt vé thất bại' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent('Bạn đã hủy đặt vé')
    expect(cancelCalls()).toHaveLength(1)
    expect(cancelCalls()[0][1]?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
    expect(readStoredBooking()).toBeNull()
  })

  it('bỏ qua hộp xác nhận thì vẫn giữ đơn', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockBackend(BOOKING)

    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Hủy đặt vé' }))
    fireEvent.click(screen.getByRole('button', { name: 'Không hủy' }))

    expect(screen.getByRole('timer')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Thông tin hành khách' })).toBeInTheDocument()
    expect(cancelCalls()).toHaveLength(0)
    expect(readStoredBooking()).not.toBeNull()
  })

  it('không có quyền xem thì hiện nguyên văn lỗi 404', async () => {
    fetchMock.mockResolvedValue(jsonResponse(404, { detail: 'Không tìm thấy đơn' }))

    renderPage('DH00999999')

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tìm thấy đơn')
    // Không có mã của đơn này thì không gửi header
    const [, init] = fetchMock.mock.calls[0]
    expect(init?.headers).not.toHaveProperty('X-Ma-Truy-Cap')
  })

  it('khối người đặt chỉ hiển thị, họ tên theo tên đã nhập lúc giữ ghế', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(
      jsonResponse(200, {
        ...BOOKING,
        nguoi_dat: { ho_ten: 'Tên Hồ Sơ Cũ', so_dien_thoai: '0905111222', email: 'binh@example.com' },
      }),
    )

    renderPage()

    const booker = await screen.findByRole('region', { name: 'Người đặt' })
    expect(booker).toHaveTextContent('Trần Thị Bình')
    expect(booker).not.toHaveTextContent('Tên Hồ Sơ Cũ')
    expect(booker).toHaveTextContent('0905111222')
    expect(booker).toHaveTextContent('binh@example.com')
    expect(within(booker).queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('backend không xác định được tên lúc giữ ghế thì hiển thị theo nguoi_dat', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(
      jsonResponse(200, {
        ...BOOKING,
        nguoi_dat: { ho_ten: 'Tên Hồ Sơ', so_dien_thoai: '0905111222', email: null },
        nguoi_dat_luc_giu: null,
      }),
    )

    renderPage()

    expect(await screen.findByRole('region', { name: 'Người đặt' })).toHaveTextContent('Tên Hồ Sơ')
  })

  it('lưu thành công: hiện tóm tắt theo chuỗi backend, nút thanh toán mở, bấm Sửa để nhập lại', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockDetailsBackend([BOOKING], jsonResponse(200, SAVED_BOOKING))

    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Lưu thông tin' }))

    const summary = await screen.findByRole('region', { name: 'Tóm tắt thông tin' })
    expect(putCalls()).toHaveLength(1)
    expect(putCalls()[0][1]?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
    expect(screen.getByTestId('tom-tat-diem-don')).toHaveTextContent('Lăng Cô – 12 Lê Lợi')
    expect(screen.getByTestId('tom-tat-diem-tra')).toHaveTextContent('Huế')
    // Mỗi ghế một dòng; nhãn "Ghế A01:" và thông tin khách nằm ở 2 phần tử riêng
    const passengers = within(within(summary).getByRole('list', { name: 'Hành khách' })).getAllByRole('listitem')
    expect(passengers[0]).toHaveTextContent(/^Ghế A01:\s*Trần Thị Bình · 0905111222$/)
    expect(screen.getByRole('button', { name: 'Tiếp tục thanh toán' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Hủy đặt vé' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Sửa' }))
    expect(screen.getByLabelText('Điểm đón')).toHaveValue('Lăng Cô')
    expect(screen.getByLabelText('Địa chỉ cụ thể (không bắt buộc)', { selector: '#diem-don-dia-chi' })).toHaveValue('12 Lê Lợi')
  })

  it('mở lại đơn đã nhập thông tin thì hiện tóm tắt', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    fetchMock.mockResolvedValue(jsonResponse(200, SAVED_BOOKING))

    renderPage()

    expect(await screen.findByRole('region', { name: 'Tóm tắt thông tin' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu thông tin' })).not.toBeInTheDocument()
  })

  it.each([
    ['HET_HAN', 'Hết thời gian giữ chỗ'],
    ['DA_HUY', 'Đơn đặt vé đã bị hủy hoặc hết thời gian giữ chỗ'],
  ] as const)('lưu nhận 410 thì tải lại đơn và hiện màn thất bại %s', async (status, message) => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    const reloaded = { ...(status === 'DA_HUY' ? CANCELLED : BOOKING), dang_giu_cho: false, trang_thai_don: status }
    mockDetailsBackend([BOOKING, reloaded], jsonResponse(410, { detail: 'Giữ chỗ đã hết hạn' }))

    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Lưu thông tin' }))

    expect(await screen.findByRole('heading', { name: 'Đặt vé thất bại' })).toBeInTheDocument()
    expect(screen.getByRole('alert')).toHaveTextContent(message)
    // Xóa đơn khỏi tab chạy trong effect sau khi hiện màn thất bại
    await vi.waitFor(() => expect(readStoredBooking()).toBeNull())
  })

  it('lỗi từ backend hiện dưới đúng trường và đồng hồ không reset', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockDetailsBackend(
      [BOOKING],
      jsonResponse(400, { detail: 'Điểm đón không thuộc tuyến', truong: 'diem_don.khu_vuc' }),
    )

    renderPage()

    expect(await screen.findByRole('timer')).toHaveTextContent('05:00')
    // Chạy hết effect để setInterval của đồng hồ đã được đăng ký trước khi tua giờ
    await act(async () => {})
    act(() => {
      vi.advanceTimersByTime(60000)
    })
    expect(screen.getByRole('timer')).toHaveTextContent('04:00')
    fireEvent.click(screen.getByRole('button', { name: 'Lưu thông tin' }))

    expect(await screen.findByText('Điểm đón không thuộc tuyến')).toBeInTheDocument()
    expect(screen.getByLabelText('Điểm đón')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('timer')).toHaveTextContent('04:00')
    act(() => {
      vi.advanceTimersByTime(1000)
    })
    expect(screen.getByRole('timer')).toHaveTextContent('03:59')
    // Không tải lại đơn sau lỗi
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
