/** Toàn bộ test giao diện (Vitest + React Testing Library) gộp một file.

Thứ tự theo luồng nghiệp vụ: tra cứu (form + trang) → chọn ghế → đặt vé
→ đếm ngược giữ chỗ → QR SePay → vé của tôi.
Mỗi nhóm `describe` tự quản hook timer/mock riêng để không ảnh hưởng chéo.
 */
import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import { routes } from '../routes'
import type { Booking, MyBooking, QrSePay } from '../services/bookingService'
import type { Seat, SeatMap, SeatStatus, Trip, TripSearchQuery, TripSearchResult } from '../services/tripService'
import { CONFIRMED_BOOKING, HELD_BOOKING, SAVED_BOOKING, jsonResponse } from '../utils/testBookings'
import { saveStoredBooking } from '../utils/bookingStorage'
import BookingPage from '../pages/BookingPage'
import HoldCountdown from '../components/HoldCountdown'
import QrSePayPanel from '../components/QrSePayPanel'
import SeatSelectionPage from '../pages/SeatSelectionPage'
import TripSearchForm from '../components/TripSearchForm'
import TripSearchPage from '../pages/TripSearchPage'

const fetchMock = vi.fn<typeof fetch>()

const LOCATIONS = {
  diem_di: ['Đà Nẵng', 'Hội An', 'Huế'],
  diem_den: ['Đà Nẵng', 'Hội An', 'Huế'],
}

const EMPTY_QUERY: TripSearchQuery = { diemDi: '', diemDen: '', ngay: '' }

const QR: QrSePay = {
  ma_don: 'DH00100000',
  so_tien: 390000,
  noi_dung: 'THANH TOAN VE DH00100000',
  qr_url: 'https://img.vietqr.io/image/qr.png',
  thoi_gian_cho_giay: 300,
}

const BOOKING: Booking = HELD_BOOKING

// ---------------- Tra cứu: form ----------------

function renderForm(initialValues: TripSearchQuery = EMPTY_QUERY, locations = LOCATIONS) {
  const onSearch = vi.fn()
  render(<TripSearchForm locations={locations} initialValues={initialValues} onSearch={onSearch} />)
  return onSearch
}

function dienForm(diemDi: string, diemDen: string, ngay: string) {
  fireEvent.change(screen.getByLabelText('Điểm đi'), { target: { value: diemDi } })
  fireEvent.change(screen.getByLabelText('Điểm đến'), { target: { value: diemDen } })
  fireEvent.change(screen.getByLabelText('Ngày đi'), { target: { value: ngay } })
  fireEvent.click(screen.getByRole('button', { name: 'Tìm chuyến' }))
}

describe('TripSearchForm', () => {
  beforeEach(() => {
    // 01/12/2026 10:00 giờ Việt Nam
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-12-01T03:00:00Z'))
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('gửi tiêu chí hợp lệ', () => {
    const onSearch = renderForm()

    dienForm('Đà Nẵng', 'Huế', '2026-12-15')

    expect(onSearch).toHaveBeenCalledWith({ diemDi: 'Đà Nẵng', diemDen: 'Huế', ngay: '2026-12-15' })
  })
})

// ---------------- Tra cứu: trang kết quả ----------------

function taoChuyen(overrides: Partial<Trip>): Trip {
  return {
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
    so_ghe_trong: 4,
    ...overrides,
  }
}

const KET_QUA_TIM: TripSearchResult = {
  chuyen: [
    taoChuyen({}),
    taoChuyen({
      chuyen_xe_id: 'CX00000007',
      gio_di: '2026-12-15T00:00:00Z',
      gio_den: '2026-12-15T02:30:00Z',
      ten_loai_xe: 'Xe 7 chỗ',
      so_cho: 7,
      gia_ve: 150000,
      so_ghe_trong: 0,
    }),
  ],
  goi_y: [],
}

/** Giả lập backend: /locations luôn thành công, /trips trả theo hàm `trips`. */
function mockTimChuyen(trips: (url: URL) => Response | Promise<Response>) {
  fetchMock.mockImplementation(async (input) => {
    const url = new URL(String(input))
    if (url.pathname === '/api/v1/locations') {
      return jsonResponse(200, LOCATIONS)
    }
    return trips(url)
  })
}

function renderTimChuyen(path: string) {
  const router = createMemoryRouter(
    [
      { path: '/tim-chuyen', element: <TripSearchPage /> },
      { path: '/chuyen/:id', element: <h1>Trang chuyến</h1> },
    ],
    { initialEntries: [path] },
  )
  render(<RouterProvider router={router} />)
  return router
}

describe('TripSearchPage', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://api.test')
    vi.stubGlobal('fetch', fetchMock)
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-12-01T03:00:00Z'))
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.useRealTimers()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it('submit form ghi tiêu chí lên URL và tìm chuyến', async () => {
    mockTimChuyen(() => jsonResponse(200, KET_QUA_TIM))
    const router = renderTimChuyen('/tim-chuyen')
    await screen.findAllByRole('option', { name: 'Huế' })

    fireEvent.change(screen.getByLabelText('Điểm đi'), { target: { value: 'Đà Nẵng' } })
    fireEvent.change(screen.getByLabelText('Điểm đến'), { target: { value: 'Huế' } })
    fireEvent.change(screen.getByLabelText('Ngày đi'), { target: { value: '2026-12-15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Tìm chuyến' }))

    const card = await screen.findByRole('article', { name: /^Chuyến 06:00/ })
    expect(within(card).getByText('08:30')).toBeInTheDocument()
    const params = new URLSearchParams(router.state.location.search)
    expect(Object.fromEntries(params)).toEqual({ di: 'Đà Nẵng', den: 'Huế', ngay: '2026-12-15' })
  })
})

// ---------------- Chọn ghế & giữ ghế ----------------

function taoGhe(...trangThai: SeatStatus[]): Seat[] {
  return trangThai.map((status, index) => ({
    ghe_id: `GH0000000${index + 1}`,
    so_ghe: `A0${index + 1}`,
    trang_thai: status,
  }))
}

function soDoGhe(ghe: Seat[], overrides: Partial<SeatMap['chuyen']> = {}, coTheDat = true): SeatMap {
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

const DON_GIU_RESPONSE = {
  ma_don: 'DH00100000',
  ma_truy_cap: 'ma-bi-mat',
  han_giu_cho: '2026-12-01T03:20:00Z',
  thoi_diem_hien_tai: '2026-12-01T03:15:00Z',
  ghe: [],
  tong_tien: 400000,
}

const THONG_TIN_DA_DANG_NHAP = {
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

/** Giả lập backend; sơ đồ ghế trả lần lượt theo `seatMaps` (lần cuối lặp lại). */
function mockChonGhe({ seatMaps, hold, booking, cancel }: {
  seatMaps: SeatMap[]
  hold?: () => Response
  booking?: () => Response
  cancel?: () => Response
}) {
  let seatCalls = 0
  fetchMock.mockImplementation(async (input) => {
    const url = new URL(String(input))
    if (url.pathname.endsWith('/seats')) {
      const data = seatMaps[Math.min(seatCalls, seatMaps.length - 1)]
      seatCalls += 1
      return jsonResponse(200, data)
    }
    if (url.pathname === '/api/v1/bookings/hold') {
      return hold ? hold() : jsonResponse(201, DON_GIU_RESPONSE)
    }
    if (url.pathname.endsWith('/cancel')) {
      return cancel ? cancel() : jsonResponse(404, { detail: 'Không tìm thấy đơn' })
    }
    if (url.pathname.startsWith('/api/v1/bookings/')) {
      return booking ? booking() : jsonResponse(404, { detail: 'Không tìm thấy đơn' })
    }
    if (url.pathname === '/api/v1/auth/me') {
      return jsonResponse(200, THONG_TIN_DA_DANG_NHAP)
    }
    return jsonResponse(404, { detail: 'Không tìm thấy' })
  })
}

function renderChonGhe() {
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

function nutGhe(code: string) {
  return screen.getByRole('button', { name: new RegExp(`^Ghế ${code} `) })
}

function noiDungGiuGhe(): unknown {
  const [, init] = fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/bookings/hold'))[0]
  return JSON.parse(String(init?.body))
}

function dienThongTinNguoiDat() {
  fireEvent.change(screen.getByLabelText('Họ tên'), { target: { value: 'Trần Thị Bình' } })
  fireEvent.change(screen.getByLabelText('Số điện thoại'), { target: { value: '0905111222' } })
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'binh@example.com' } })
  fireEvent.click(screen.getByRole('button', { name: 'Xác nhận giữ ghế' }))
}

describe('SeatSelectionPage', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://api.test')
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it('khách vãng lai giữ ghế đã chọn với thông tin người đặt', async () => {
    mockChonGhe({ seatMaps: [soDoGhe(taoGhe('TRONG', 'TRONG', 'TRONG', 'TRONG'))] })
    renderChonGhe()
    await screen.findByText('Đà Nẵng - Huế')

    fireEvent.click(nutGhe('A02'))
    fireEvent.click(nutGhe('A04'))
    fireEvent.click(screen.getByRole('button', { name: 'Giữ ghế' }))
    dienThongTinNguoiDat()

    expect(await screen.findByRole('heading', { name: 'Trang đặt vé' })).toBeInTheDocument()
    expect(noiDungGiuGhe()).toEqual({
      chuyen_xe_id: 'CX00000001',
      ghe_ids: ['GH00000002', 'GH00000004'],
      nguoi_dat: { ho_ten: 'Trần Thị Bình', so_dien_thoai: '0905111222', email: 'binh@example.com' },
    })
  })
})

// ---------------- Trang đặt vé ----------------

/** GET đơn trả lần lượt `gets` (phần tử cuối dùng cho các lần sau), PUT details trả `putResponse`. */
function mockChiTietDon(gets: Booking[], putResponse: Response | (() => Response)) {
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

function lenhPutChiTiet() {
  return fetchMock.mock.calls.filter(
    ([input, init]) => String(input).endsWith('/details') && init?.method === 'PUT',
  )
}

function renderDatVe(maDon = 'DH00100000') {
  const router = createMemoryRouter([{ path: '/dat-ve/:maDon', element: <BookingPage /> }], {
    initialEntries: [`/dat-ve/${maDon}`],
  })
  render(<RouterProvider router={router} />)
  return router
}

describe('BookingPage', () => {
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

  it('lưu thành công: hiện tóm tắt theo chuỗi backend, nút thanh toán mở, bấm Sửa để nhập lại', async () => {
    saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
    mockChiTietDon([BOOKING], jsonResponse(200, SAVED_BOOKING))

    renderDatVe()

    fireEvent.click(await screen.findByRole('button', { name: 'Lưu thông tin' }))

    const summary = await screen.findByRole('region', { name: 'Tóm tắt thông tin' })
    expect(lenhPutChiTiet()).toHaveLength(1)
    expect(lenhPutChiTiet()[0][1]?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
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
})

// ---------------- Đếm ngược giữ chỗ ----------------

describe('HoldCountdown', () => {
  it('hiện thời gian còn lại, chưa cảnh báo khi còn hơn 2 phút', () => {
    render(<HoldCountdown remainingMs={121000} />)

    expect(screen.getByRole('timer')).toHaveTextContent('02:01')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

// ---------------- QR SePay ----------------

describe('QrSePayPanel', () => {
  it('hiện ảnh QR, số tiền và nội dung phải chuyển đúng', () => {
    render(<QrSePayPanel qr={QR} conLaiMs={4 * 60 * 1000 + 1000} />)

    expect(screen.getByTestId('qr-se-pay-hinh')).toHaveAttribute('src', QR.qr_url)
    expect(screen.getByTestId('qr-se-pay-so-tien')).toHaveTextContent('390.000 đ')
    expect(screen.getByTestId('qr-se-pay-noi-dung')).toHaveTextContent('THANH TOAN VE DH00100000')
    expect(screen.getByRole('timer', { name: 'Thời gian chuyển khoản còn lại' })).toHaveTextContent('04:01')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})

// ---------------- Vé của tôi ----------------

const DON_VE: MyBooking[] = [
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

function dangNhap(vaiTro = 'KHACH') {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', vai_tro: vaiTro, ho_ten: 'Khách Mẫu' }))
}

function mockVeCuaToi(response: Response) {
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.endsWith('/me/tickets')) return response.clone()
    // /auth/me khi khôi phục phiên, /health ở trang chủ: giữ treo
    return new Promise<Response>(() => {})
  })
}

describe('MyTicketsPage (/ve-cua-toi)', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://api.test')
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it('đăng nhập KHACH: hiện các đơn theo thứ tự backend, vé gom theo mã đơn', async () => {
    dangNhap()
    mockVeCuaToi(jsonResponse(200, DON_VE))
    const router = createMemoryRouter(routes, { initialEntries: ['/ve-cua-toi'] })
    render(
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>,
    )

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
})
