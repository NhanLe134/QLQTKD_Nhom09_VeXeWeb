import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { readStoredBooking, saveStoredBooking } from '../utils/bookingStorage'
import CancelBookingButton from './CancelBookingButton'

const fetchMock = vi.fn<typeof fetch>()

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
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
  vi.restoreAllMocks()
})

describe('CancelBookingButton', () => {
  it('bấm hủy thì hiện hộp xác nhận trong trang, chưa gọi API, không dùng window.confirm', () => {
    const confirmSpy = vi.spyOn(window, 'confirm')
    render(<CancelBookingButton maDon="DH00100000" onCancelled={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: 'Hủy đặt vé' }))

    expect(screen.getByRole('alertdialog', { name: 'Hủy đơn DH00100000?' })).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
    expect(confirmSpy).not.toHaveBeenCalled()
  })

  it('bỏ qua thì đóng hộp xác nhận, không hủy và giữ đơn trong tab', () => {
    const onCancelled = vi.fn()
    render(<CancelBookingButton maDon="DH00100000" onCancelled={onCancelled} />)

    fireEvent.click(screen.getByRole('button', { name: 'Hủy đặt vé' }))
    fireEvent.click(screen.getByRole('button', { name: 'Không hủy' }))

    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Hủy đặt vé' })).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
    expect(onCancelled).not.toHaveBeenCalled()
    expect(readStoredBooking()).not.toBeNull()
  })

  it('đồng ý thì gọi API hủy kèm mã truy cập, xóa đơn khỏi tab', async () => {
    const cancelled = { ma_don: 'DH00100000', trang_thai_don: 'DA_HUY' }
    fetchMock.mockResolvedValue(jsonResponse(200, cancelled))
    const onCancelled = vi.fn()
    render(<CancelBookingButton maDon="DH00100000" label="Hủy đơn cũ" onCancelled={onCancelled} />)

    fireEvent.click(screen.getByRole('button', { name: 'Hủy đơn cũ' }))
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý hủy' }))

    await waitFor(() => expect(onCancelled).toHaveBeenCalledWith(cancelled))
    const [url, init] = fetchMock.mock.calls[0]
    expect(String(url)).toBe('http://api.test/api/v1/bookings/DH00100000/cancel')
    expect(init?.method).toBe('POST')
    expect(init?.headers).toMatchObject({ 'X-Ma-Truy-Cap': 'ma-bi-mat' })
    expect(readStoredBooking()).toBeNull()
  })

  it('backend từ chối thì hiện nguyên văn lỗi và giữ đơn trong tab', async () => {
    fetchMock.mockResolvedValue(jsonResponse(400, { detail: 'Đơn đã xác nhận, không thể hủy ở bước này' }))
    const onCancelled = vi.fn()
    render(<CancelBookingButton maDon="DH00100000" onCancelled={onCancelled} />)

    fireEvent.click(screen.getByRole('button', { name: 'Hủy đặt vé' }))
    fireEvent.click(screen.getByRole('button', { name: 'Đồng ý hủy' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Đơn đã xác nhận, không thể hủy ở bước này')
    expect(onCancelled).not.toHaveBeenCalled()
    expect(readStoredBooking()).not.toBeNull()
    expect(screen.getByRole('button', { name: 'Đồng ý hủy' })).toBeEnabled()
  })
})
