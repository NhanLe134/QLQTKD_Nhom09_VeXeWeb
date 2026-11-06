import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import { routes } from '../routes'
import type { CashDeposit } from '../services/operatorService'
import { CONFIRMED_BOOKING, jsonResponse } from '../utils/testBookings'

const fetchMock = vi.fn<typeof fetch>()

const DEPOSIT: CashDeposit = {
  nop_tien_id: 'NT00100000',
  tai_xe_id: 'TX00000001',
  ten_tai_xe: 'Tài Xế Mẫu',
  chuyen: CONFIRMED_BOOKING.chuyen,
  so_tien: 400000,
  ngay_nop: '2026-12-15T03:00:00Z',
  trang_thai: 'CHO_XAC_NHAN',
  ngay_xac_nhan: null,
}

function login(vaiTro: string) {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', vai_tro: vaiTro, ho_ten: 'Nhà Xe' }))
}

function mockBackend(decided?: Response) {
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.includes('/cash-deposits?')) return jsonResponse(200, [DEPOSIT])
    if (url.endsWith('/confirm')) return (decided ?? jsonResponse(200, { ...DEPOSIT, trang_thai: 'DA_XAC_NHAN' })).clone()
    if (url.endsWith('/reject')) return (decided ?? jsonResponse(200, { ...DEPOSIT, trang_thai: 'TU_CHOI' })).clone()
    return new Promise<Response>(() => {})
  })
}

function decisionCalls() {
  return fetchMock.mock.calls.filter(([input]) => /\/(confirm|reject)$/.test(String(input)))
}

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(
    <AuthProvider>
      <RouterProvider router={router} />
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

describe('CashDepositsPage (/nha-xe/doi-soat-tien-mat)', () => {
  it.each(['KHACH', 'TAI_XE'])('vai trò %s: báo trang chỉ dành cho nhà xe', (vaiTro) => {
    login(vaiTro)
    mockBackend()
    renderAt('/nha-xe/doi-soat-tien-mat')

    expect(screen.getByRole('alert')).toHaveTextContent('Trang này chỉ dành cho tài khoản nhà xe.')
    expect(fetchMock.mock.calls.some(([input]) => String(input).includes('/cash-deposits'))).toBe(false)
  })

  it('hiện khoản chờ xác nhận: tài xế, chuyến, số tiền, ngày nộp', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/doi-soat-tien-mat')

    const item = await screen.findByRole('listitem', { name: 'Khoản nộp NT00100000' })
    expect(item).toHaveTextContent('Tài Xế Mẫu')
    expect(item).toHaveTextContent('Đà Nẵng - Huế')
    expect(item).toHaveTextContent('CX00000001')
    expect(item).toHaveTextContent('400.000 đ')
    expect(item).toHaveTextContent('15/12/2026 10:00')
    expect(String(fetchMock.mock.calls.find(([i]) => String(i).includes('/cash-deposits?'))?.[0])).toContain(
      'trang_thai=CHO_XAC_NHAN',
    )
  })

  it('Xác nhận: hộp xác nhận trong trang rồi mới gửi; xong thì bỏ khỏi danh sách', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/doi-soat-tien-mat')

    const item = await screen.findByRole('listitem', { name: 'Khoản nộp NT00100000' })
    fireEvent.click(within(item).getByRole('button', { name: 'Xác nhận' }))
    const dialog = within(item).getByRole('alertdialog', { name: 'Xác nhận đã nhận tiền' })
    expect(dialog).toHaveTextContent('400.000 đ')
    expect(decisionCalls()).toHaveLength(0)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Xác nhận' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Đã xác nhận khoản nộp 400.000 đ của Tài Xế Mẫu.')
    expect(screen.getByText('Không có khoản nộp nào đang chờ xác nhận.')).toBeInTheDocument()
    const [url, init] = decisionCalls()[0]
    expect(String(url)).toBe('http://api.test/api/v1/operator/cash-deposits/NT00100000/confirm')
    expect(init?.method).toBe('POST')
  })

  it('Từ chối: bấm "Quay lại" thì không gửi; đồng ý thì gửi reject', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/doi-soat-tien-mat')

    const item = await screen.findByRole('listitem', { name: 'Khoản nộp NT00100000' })
    fireEvent.click(within(item).getByRole('button', { name: 'Từ chối' }))
    fireEvent.click(within(item).getByRole('button', { name: 'Quay lại' }))
    expect(decisionCalls()).toHaveLength(0)

    fireEvent.click(within(item).getByRole('button', { name: 'Từ chối' }))
    const dialog = within(item).getByRole('alertdialog', { name: 'Từ chối khoản nộp' })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Từ chối' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Đã từ chối khoản nộp')
    expect(String(decisionCalls()[0][0])).toMatch(/\/NT00100000\/reject$/)
  })

  it('409 đã được xử lý: hiện lỗi của backend trong thẻ', async () => {
    login('NHA_XE')
    mockBackend(jsonResponse(409, { detail: 'Khoản nộp đã được xử lý trước đó', truong: null }))
    renderAt('/nha-xe/doi-soat-tien-mat')

    const item = await screen.findByRole('listitem', { name: 'Khoản nộp NT00100000' })
    fireEvent.click(within(item).getByRole('button', { name: 'Xác nhận' }))
    fireEvent.click(within(within(item).getByRole('alertdialog')).getByRole('button', { name: 'Xác nhận' }))

    expect(await within(item).findByRole('alert')).toHaveTextContent('Khoản nộp đã được xử lý trước đó')
    expect(within(item).getByRole('button', { name: 'Xác nhận' })).toBeInTheDocument()
  })
})
