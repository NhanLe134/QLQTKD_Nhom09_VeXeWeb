import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { CancelQuoteTicket } from '../services/bookingService'
import { CONFIRMED_STORAGE_KEY } from '../utils/bookingStorage'
import { CANCEL_RECEIPT, CONFIRMED_BOOKING, jsonResponse, quoteTicket } from '../utils/testBookings'
import CancelTicketPanel from './CancelTicketPanel'

const fetchMock = vi.fn<typeof fetch>()
const TICKET = CONFIRMED_BOOKING.ve[0]

function mockBackend(quotes: CancelQuoteTicket[][], cancel: Response = jsonResponse(200, CANCEL_RECEIPT)) {
  let index = 0
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.endsWith('/cancel-tickets')) return cancel.clone()
    const ve = quotes[Math.min(index, quotes.length - 1)]
    index += 1
    return jsonResponse(200, { ma_don: 'DH00100000', thoi_diem_hien_tai: '2026-12-13T20:00:00Z', ve })
  })
}

function cancelCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/cancel-tickets'))
}

function quoteCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/cancel-quote'))
}

function renderPanel() {
  const onCancelled = vi.fn()
  const onClose = vi.fn()
  render(<CancelTicketPanel maDon="DH00100000" ticket={TICKET} onCancelled={onCancelled} onClose={onClose} />)
  return { onCancelled, onClose }
}

function fillAccount(bank: string, account: string) {
  fireEvent.change(screen.getByLabelText('Ngân hàng nhận tiền'), { target: { value: bank } })
  fireEvent.change(screen.getByLabelText('Số tài khoản'), { target: { value: account } })
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
  sessionStorage.setItem(CONFIRMED_STORAGE_KEY, JSON.stringify({ DH00100000: 'ma-bi-mat' }))
})

afterEach(() => {
  fetchMock.mockReset()
  sessionStorage.clear()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

describe('CancelTicketPanel', () => {
  it('hiện mức hoàn đúng như backend trả, gửi mã truy cập', async () => {
    mockBackend([[quoteTicket({ ve_id: 'VE00100002', muc_hoan: 1 }), quoteTicket()]])
    renderPanel()

    expect(await screen.findByTestId('muc-hoan')).toHaveTextContent('99.000 đ')
    expect(screen.getByText('50%')).toBeInTheDocument()
    const [url, init] = quoteCalls()[0]
    expect(String(url)).toBe('http://api.test/api/v1/bookings/DH00100000/cancel-quote')
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
  })

  it('không được hủy: hiện lý do của backend, không có nút hủy', async () => {
    const lyDo = 'Không thể hủy vé khi còn dưới 12 giờ trước giờ khởi hành'
    mockBackend([[quoteTicket({ duoc_huy: false, ly_do: lyDo, muc_hoan: 0, ti_le_hoan: 0, can_tai_khoan_nhan: false })]])
    renderPanel()

    expect(await screen.findByRole('alert')).toHaveTextContent(lyDo)
    expect(screen.queryByRole('button', { name: 'Tiếp tục hủy vé' })).not.toBeInTheDocument()
  })

  it('vé đã chuyển khoản: thiếu tài khoản báo lỗi đúng ô, không gọi API hủy', async () => {
    mockBackend([[quoteTicket()]])
    renderPanel()

    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục hủy vé' }))

    expect(screen.getByText('Vui lòng nhập ngân hàng nhận tiền hoàn')).toBeInTheDocument()
    expect(screen.getByText('Vui lòng nhập số tài khoản nhận tiền hoàn')).toBeInTheDocument()
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(cancelCalls()).toHaveLength(0)
  })

  it('xác nhận trong trang rồi gửi vé, tài khoản, mức hoàn đã xem; trả biên lai', async () => {
    mockBackend([[quoteTicket()]])
    const { onCancelled } = renderPanel()

    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục hủy vé' }))
    fillAccount('Vietcombank', '0123456789')
    fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục hủy vé' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Xác nhận hủy vé' })
    expect(dialog).toHaveTextContent('99.000 đ')
    expect(cancelCalls()).toHaveLength(0)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Đồng ý hủy vé' }))

    await waitFor(() => expect(onCancelled).toHaveBeenCalledWith(CANCEL_RECEIPT))
    const [, init] = cancelCalls()[0]
    expect(init?.method).toBe('POST')
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
    expect(JSON.parse(String(init?.body))).toEqual({
      ve_ids: ['VE00100001'],
      muc_hoan_xac_nhan: 99000,
      ngan_hang_nhan: 'Vietcombank',
      so_tai_khoan_nhan: '0123456789',
    })
  })

  it('bấm "Quay lại" trong hộp xác nhận: không hủy', async () => {
    mockBackend([[quoteTicket({ can_tai_khoan_nhan: false })]])
    renderPanel()

    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục hủy vé' }))
    fireEvent.click(within(screen.getByRole('alertdialog')).getByRole('button', { name: 'Quay lại' }))

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(cancelCalls()).toHaveLength(0)
  })

  it('vé tiền mặt chưa thu: không hỏi tài khoản, hiện ghi chú, không gửi tài khoản', async () => {
    const ghiChu = 'Vé trả tiền mặt khi lên xe chưa thu tiền nên không phát sinh hoàn tiền'
    mockBackend([
      [quoteTicket({ trang_thai_thanh_toan: 'CHO_THU_TIEN_MAT', muc_hoan: 0, ghi_chu: ghiChu, can_tai_khoan_nhan: false })],
    ])
    const { onCancelled } = renderPanel()

    expect(await screen.findByText(ghiChu)).toBeInTheDocument()
    expect(screen.queryByLabelText('Số tài khoản')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục hủy vé' }))
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý hủy vé' }))

    await waitFor(() => expect(onCancelled).toHaveBeenCalled())
    expect(JSON.parse(String(cancelCalls()[0][1]?.body))).toEqual({ ve_ids: ['VE00100001'], muc_hoan_xac_nhan: 0 })
  })

  it('422 kèm truong: hiện lỗi dưới đúng ô', async () => {
    mockBackend(
      [[quoteTicket()]],
      jsonResponse(422, { detail: 'Số tài khoản chỉ gồm chữ số, từ 6 đến 20 số', truong: 'so_tai_khoan_nhan' }),
    )
    const { onCancelled } = renderPanel()

    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục hủy vé' }))
    fillAccount('ACB', '12-34')
    fireEvent.click(screen.getByRole('button', { name: 'Tiếp tục hủy vé' }))
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý hủy vé' }))

    expect(await screen.findByText('Số tài khoản chỉ gồm chữ số, từ 6 đến 20 số')).toBeInTheDocument()
    expect(screen.getByLabelText('Số tài khoản')).toHaveAttribute('aria-invalid', 'true')
    expect(onCancelled).not.toHaveBeenCalled()
  })

  it('409 mức hoàn đã đổi: hiện nguyên văn và tải lại mức hoàn mới', async () => {
    const detail = 'Mức hoàn đã thay đổi thành 100.000 đ, vui lòng xem lại trước khi hủy'
    mockBackend(
      [[quoteTicket({ muc_hoan: 200000, ti_le_hoan: 100, can_tai_khoan_nhan: false })], [quoteTicket({ muc_hoan: 100000, can_tai_khoan_nhan: false })]],
      jsonResponse(409, { detail, truong: null }),
    )
    renderPanel()

    fireEvent.click(await screen.findByRole('button', { name: 'Tiếp tục hủy vé' }))
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý hủy vé' }))

    expect(await screen.findByText(detail)).toBeInTheDocument()
    await waitFor(() => expect(screen.getByTestId('muc-hoan')).toHaveTextContent('100.000 đ'))
    expect(quoteCalls()).toHaveLength(2)
  })
})
