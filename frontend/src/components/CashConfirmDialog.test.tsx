import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Booking } from '../services/bookingService'
import { accessCodeFor, readStoredBooking, saveStoredBooking } from '../utils/bookingStorage'
import { jsonResponse, SAVED_BOOKING } from '../utils/testBookings'
import CashConfirmDialog from './CashConfirmDialog'

const fetchMock = vi.fn<typeof fetch>()

const CONFIRMED: Booking = {
  ...SAVED_BOOKING,
  ve: SAVED_BOOKING.ve.map((ve) => ({ ...ve, trang_thai_ve: 'DA_XAC_NHAN', trang_thai_thanh_toan: 'CHO_THU_TIEN_MAT' })),
  han_giu_cho: null,
  dang_giu_cho: false,
  trang_thai_don: 'DA_XAC_NHAN',
}

function renderDialog(overrides: Partial<Parameters<typeof CashConfirmDialog>[0]> = {}) {
  const props = {
    maDon: 'DH00100000',
    tongTien: 390000,
    onConfirmed: vi.fn(),
    onGone: vi.fn(),
    onFieldError: vi.fn(),
    onCancel: vi.fn(),
    ...overrides,
  }
  render(<CashConfirmDialog {...props} />)
  return props
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
  saveStoredBooking({ ma_don: 'DH00100000', ma_truy_cap: 'ma-bi-mat' })
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('CashConfirmDialog', () => {
  it('hiện số tiền phải trả theo backend', () => {
    renderDialog()

    expect(screen.getByRole('alertdialog')).toHaveTextContent('Bạn sẽ trả 390.000 đ cho tài xế khi lên xe')
  })

  it('đồng ý: gọi confirm-cash kèm mã truy cập, chuyển mã sang kho đơn đã xác nhận', async () => {
    fetchMock.mockResolvedValue(jsonResponse(200, CONFIRMED))
    const props = renderDialog()

    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))

    await waitFor(() => expect(props.onConfirmed).toHaveBeenCalledWith(CONFIRMED))
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toBe('http://api.test/api/v1/bookings/DH00100000/confirm-cash')
    expect(init?.method).toBe('POST')
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
    expect(readStoredBooking()).toBeNull()
    expect(accessCodeFor('DH00100000')).toBe('ma-bi-mat')
  })

  it('bỏ qua: không gọi backend', () => {
    const props = renderDialog()

    fireEvent.click(screen.getByRole('button', { name: 'Quay lại' }))

    expect(props.onCancel).toHaveBeenCalledOnce()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('bấm liên tiếp chỉ gửi một lần; nút vô hiệu khi đang gửi', async () => {
    let resolve: (response: Response) => void = () => {}
    fetchMock.mockImplementation(() => new Promise<Response>((r) => (resolve = r)))
    const props = renderDialog()

    const button = screen.getByRole('button', { name: 'Đồng ý' })
    fireEvent.click(button)
    fireEvent.click(button)
    fireEvent.click(button)

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(await screen.findByRole('button', { name: 'Đang xác nhận…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Quay lại' })).toBeDisabled()
    resolve(jsonResponse(200, CONFIRMED))
    await waitFor(() => expect(props.onConfirmed).toHaveBeenCalledOnce())
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('410: báo onGone', async () => {
    fetchMock.mockResolvedValue(jsonResponse(410, { detail: 'Giữ chỗ đã hết hạn' }))
    const props = renderDialog()

    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))

    await waitFor(() => expect(props.onGone).toHaveBeenCalledOnce())
    expect(props.onConfirmed).not.toHaveBeenCalled()
  })

  it('400 kèm truong: chuyển lỗi về đúng trường', async () => {
    fetchMock.mockResolvedValue(jsonResponse(400, { detail: 'Chưa nhập điểm đón/trả', truong: 'diem_don.khu_vuc' }))
    const props = renderDialog()

    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))

    await waitFor(() => expect(props.onFieldError).toHaveBeenCalledWith('diem_don.khu_vuc', 'Chưa nhập điểm đón/trả'))
  })

  it('400 không có truong: hiện nguyên văn, bấm lại được', async () => {
    fetchMock.mockResolvedValue(jsonResponse(400, { detail: 'Chuyến xe đã khởi hành hoặc ngừng bán', truong: null }))
    renderDialog()

    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Chuyến xe đã khởi hành hoặc ngừng bán')
    expect(screen.getByRole('button', { name: 'Đồng ý' })).toBeEnabled()
  })
})
