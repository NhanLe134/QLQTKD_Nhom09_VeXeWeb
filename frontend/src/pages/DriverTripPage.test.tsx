import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import { routes } from '../routes'
import type { DriverTripDetail, Passenger } from '../services/driverService'
import type { CashDeposit } from '../services/operatorService'
import { CONFIRMED_BOOKING, jsonResponse } from '../utils/testBookings'

const fetchMock = vi.fn<typeof fetch>()
const TRIP_URL = 'http://api.test/api/v1/driver/trips/CX00000001'

function passenger(overrides: Partial<Passenger> = {}): Passenger {
  return {
    ve_id: 'VE00100001',
    ma_don: 'DH00100000',
    so_ghe: 'A01',
    ho_ten: 'Trần Thị Bình',
    so_dien_thoai: '0905111222',
    diem_don: 'Đà Nẵng',
    diem_tra: 'Huế',
    trang_thai_thanh_toan: 'CHO_THU_TIEN_MAT',
    so_tien_can_thu: 200000,
    co_the_thu_tien: true,
    ...overrides,
  }
}

const DEPOSIT: CashDeposit = {
  nop_tien_id: 'NT00100000',
  tai_xe_id: 'TX00000001',
  ten_tai_xe: 'Tài Xế Mẫu',
  chuyen: CONFIRMED_BOOKING.chuyen,
  so_tien: 200000,
  ngay_nop: '2026-12-15T03:00:00Z',
  trang_thai: 'CHO_XAC_NHAN',
  ngay_xac_nhan: null,
}

// Số tiền là giá trị riêng của backend (không khớp tổng vé) để chắc trang không tự cộng
const DETAIL: DriverTripDetail = {
  chuyen: CONFIRMED_BOOKING.chuyen,
  trang_thai: 'MO_BAN',
  khach: [
    passenger(),
    passenger({
      ve_id: 'VE00100002',
      so_ghe: 'A02',
      ho_ten: 'Lê Văn Cường',
      trang_thai_thanh_toan: 'DA_THANH_TOAN',
      so_tien_can_thu: 0,
      co_the_thu_tien: false,
    }),
  ],
  tien_mat: { tong_da_thu: 123000, tong_chua_thu: 456000, da_nop: 0, dang_cho: 0, co_the_nop: 123000 },
  co_the_nop_tien: true,
  co_the_ket_thuc: false,
  khoan_nop: [],
  thoi_diem_hien_tai: '2026-12-14T20:00:00Z',
}

const COLLECTED: DriverTripDetail = {
  ...DETAIL,
  khach: [
    passenger({ trang_thai_thanh_toan: 'DA_THANH_TOAN', so_tien_can_thu: 0, co_the_thu_tien: false }),
    DETAIL.khach[1],
  ],
  tien_mat: { ...DETAIL.tien_mat, tong_da_thu: 323000, tong_chua_thu: 256000, co_the_nop: 323000 },
}

type Overrides = { detail?: DriverTripDetail[]; collect?: Response; deposit?: Response; complete?: Response }

function mockBackend({ detail = [DETAIL], collect, deposit, complete }: Overrides = {}) {
  let detailIndex = 0
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url === TRIP_URL) return jsonResponse(200, detail[Math.min(detailIndex++, detail.length - 1)])
    if (url.endsWith('/collect-cash')) return (collect ?? jsonResponse(200, COLLECTED)).clone()
    if (url.endsWith('/cash-deposits')) return (deposit ?? jsonResponse(201, DEPOSIT)).clone()
    if (url.endsWith('/complete')) return (complete ?? jsonResponse(200, DETAIL)).clone()
    return new Promise<Response>(() => {})
  })
}

function calls(suffix: string) {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith(suffix))
}

function login(vaiTro: string) {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', vai_tro: vaiTro, ho_ten: 'Tài Xế' }))
}

function renderPage() {
  render(
    <AuthProvider>
      <RouterProvider router={createMemoryRouter(routes, { initialEntries: ['/tai-xe/chuyen/CX00000001'] })} />
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

describe('DriverTripPage (/tai-xe/chuyen/:id)', () => {
  it('vai trò khác: báo trang chỉ dành cho tài xế', () => {
    login('NHA_XE')
    mockBackend()
    renderPage()

    expect(screen.getByRole('alert')).toHaveTextContent('Trang này chỉ dành cho tài khoản tài xế.')
    expect(calls('/CX00000001')).toHaveLength(0)
  })

  it('404 chuyến không phải của mình: hiện lỗi của backend', async () => {
    login('TAI_XE')
    fetchMock.mockImplementation(async () => jsonResponse(404, { detail: 'Không tìm thấy chuyến xe', truong: null }))
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Không tìm thấy chuyến xe')
  })

  it('hiện khách và số tiền backend tính; chỉ vé chờ thu tiền mặt có nút', async () => {
    login('TAI_XE')
    mockBackend()
    renderPage()

    const first = await screen.findByRole('listitem', { name: 'Ghế A01' })
    expect(first).toHaveTextContent('Trần Thị Bình')
    expect(within(first).getByRole('link', { name: '0905111222' })).toHaveAttribute('href', 'tel:0905111222')
    expect(first).toHaveTextContent('Chờ thu tiền mặt')
    expect(first).toHaveTextContent('200.000 đ')
    expect(within(first).getByRole('button', { name: 'Đã thu tiền mặt' })).toBeInTheDocument()
    const second = screen.getByRole('listitem', { name: 'Ghế A02' })
    expect(within(second).queryByRole('button')).not.toBeInTheDocument()

    const cash = screen.getByRole('region', { name: 'Tiền mặt' })
    expect(cash).toHaveTextContent('123.000 đ')
    expect(cash).toHaveTextContent('456.000 đ')
    expect(within(cash).getByRole('button', { name: 'Nộp tiền 123.000 đ' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Kết thúc chuyến' })).not.toBeInTheDocument()
  })

  it('Đã thu tiền mặt: hộp xác nhận rồi mới gửi; cập nhật theo kết quả backend', async () => {
    login('TAI_XE')
    mockBackend()
    renderPage()

    const first = await screen.findByRole('listitem', { name: 'Ghế A01' })
    fireEvent.click(within(first).getByRole('button', { name: 'Đã thu tiền mặt' }))
    const dialog = within(first).getByRole('alertdialog', { name: 'Xác nhận đã thu tiền' })
    expect(dialog).toHaveTextContent('200.000 đ')
    expect(calls('/collect-cash')).toHaveLength(0)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Đồng ý' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Đã ghi nhận thu tiền mặt ghế A01.')
    expect(within(first).queryByRole('button', { name: 'Đã thu tiền mặt' })).not.toBeInTheDocument()
    expect(first).toHaveTextContent('Đã thanh toán')
    expect(screen.getByRole('button', { name: 'Nộp tiền 323.000 đ' })).toBeInTheDocument()
    const [url, init] = calls('/collect-cash')[0]
    expect(String(url)).toBe(`${TRIP_URL}/tickets/VE00100001/collect-cash`)
    expect(init?.method).toBe('POST')
  })

  it('thu tiền lỗi (khách vừa hủy vé): hiện lỗi và tải lại chuyến', async () => {
    login('TAI_XE')
    mockBackend({
      detail: [DETAIL, { ...DETAIL, khach: [DETAIL.khach[1]] }],
      collect: jsonResponse(400, { detail: 'Vé đã bị hủy', truong: null }),
    })
    renderPage()

    const first = await screen.findByRole('listitem', { name: 'Ghế A01' })
    fireEvent.click(within(first).getByRole('button', { name: 'Đã thu tiền mặt' }))
    fireEvent.click(within(first).getByRole('button', { name: 'Đồng ý' }))

    expect(await screen.findByText('Vé đã bị hủy')).toBeInTheDocument()
    expect(await screen.findByText('Khách (1)')).toBeInTheDocument()
    expect(screen.queryByRole('listitem', { name: 'Ghế A01' })).not.toBeInTheDocument()
  })

  it('Nộp tiền: hộp xác nhận với số tiền backend tính, rồi hiện trạng thái khoản nộp', async () => {
    login('TAI_XE')
    const afterDeposit: DriverTripDetail = {
      ...DETAIL,
      tien_mat: { ...DETAIL.tien_mat, dang_cho: 123000, co_the_nop: 0 },
      co_the_nop_tien: false,
      khoan_nop: [
        { ...DEPOSIT, nop_tien_id: 'NT00099999', so_tien: 50000, trang_thai: 'TU_CHOI' },
        { ...DEPOSIT, so_tien: 123000 },
      ],
    }
    mockBackend({ detail: [DETAIL, afterDeposit], deposit: jsonResponse(201, { ...DEPOSIT, so_tien: 123000 }) })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Nộp tiền 123.000 đ' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Nộp tiền cho nhà xe' })
    expect(dialog).toHaveTextContent('123.000 đ')
    expect(calls('/cash-deposits')).toHaveLength(0)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Nộp tiền' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Đã nộp 123.000 đ, chờ nhà xe xác nhận.')
    const deposits = await screen.findByRole('list', { name: 'Khoản đã nộp' })
    expect(deposits).toHaveTextContent('Bị từ chối')
    expect(deposits).toHaveTextContent('Chờ xác nhận')
    expect(screen.queryByRole('button', { name: /^Nộp tiền/ })).not.toBeInTheDocument()
    expect(calls('/cash-deposits')[0][1]?.method).toBe('POST')
  })

  it('409 đã có khoản chờ: hiện lỗi của backend', async () => {
    login('TAI_XE')
    mockBackend({
      deposit: jsonResponse(409, { detail: 'Chuyến đã có khoản nộp đang chờ nhà xe xác nhận', truong: null }),
    })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Nộp tiền 123.000 đ' }))
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Nộp tiền' }))

    expect(await screen.findByText('Chuyến đã có khoản nộp đang chờ nhà xe xác nhận')).toBeInTheDocument()
  })

  it('Kết thúc chuyến khi backend cho phép, có hộp xác nhận', async () => {
    login('TAI_XE')
    mockBackend({
      detail: [{ ...DETAIL, co_the_ket_thuc: true }],
      complete: jsonResponse(200, { ...DETAIL, trang_thai: 'HOAN_THANH', co_the_ket_thuc: false }),
    })
    renderPage()

    fireEvent.click(await screen.findByRole('button', { name: 'Kết thúc chuyến' }))
    fireEvent.click(within(screen.getByRole('alertdialog', { name: 'Kết thúc chuyến' })).getByRole('button', { name: 'Kết thúc' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Đã kết thúc chuyến.')
    expect(screen.getByText(/Đã hoàn thành/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Kết thúc chuyến' })).not.toBeInTheDocument()
  })
})
