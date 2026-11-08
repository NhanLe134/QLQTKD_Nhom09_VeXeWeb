import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import { routes } from '../routes'
import type { Refund } from '../services/refundService'
import { CONFIRMED_BOOKING, jsonResponse } from '../utils/testBookings'

const fetchMock = vi.fn<typeof fetch>()

const REFUND: Refund = {
  thanh_toan_id: 'TT00100005',
  yeu_cau_id: 'YC00100000',
  ma_don: 'DH00100000',
  ve_id: 'VE00100001',
  so_ghe: 'A01',
  chuyen: CONFIRMED_BOOKING.chuyen,
  gia_ve: 200000,
  so_tien: 100000,
  ngay_huy: '2026-12-13T20:00:00Z',
  ngan_hang_nhan: 'Vietcombank',
  so_tai_khoan_nhan: '0123456789',
  trang_thai_thanh_toan: 'CHO_THANH_TOAN',
  ngay_thanh_toan: null,
  ma_giao_dich: null,
}

function login(vaiTro: string) {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', vai_tro: vaiTro, ho_ten: 'Nhà Xe' }))
}

function mockBackend(complete: Response = jsonResponse(200, { ...REFUND, trang_thai_thanh_toan: 'DA_THANH_TOAN' })) {
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.endsWith('/api/v1/refunds')) return jsonResponse(200, [REFUND])
    if (url.endsWith('/complete')) return complete.clone()
    return new Promise<Response>(() => {})
  })
}

function completeCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/complete'))
}

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>,
  )
  return router
}

async function enterCode(code: string) {
  const item = await screen.findByRole('listitem', { name: 'Khoản hoàn TT00100005' })
  fireEvent.click(within(item).getByRole('button', { name: 'Đã hoàn' }))
  fireEvent.change(within(item).getByLabelText('Mã giao dịch ngân hàng'), { target: { value: code } })
  fireEvent.click(within(item).getByRole('button', { name: 'Tiếp tục' }))
  return item
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

describe('RefundsPage (/nha-xe/hoan-tien)', () => {
  it('chưa đăng nhập: chuyển tới trang đăng nhập, không gọi API', () => {
    mockBackend()
    const router = renderAt('/nha-xe/hoan-tien')

    expect(router.state.location.pathname).toBe('/dang-nhap')
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/refunds'))).toBe(false)
  })

  it.each(['KHACH', 'TAI_XE'])('vai trò %s: báo trang chỉ dành cho nhà xe, không có mục menu', (vaiTro) => {
    login(vaiTro)
    mockBackend()
    renderAt('/nha-xe/hoan-tien')

    expect(screen.getByRole('alert')).toHaveTextContent('Trang này chỉ dành cho tài khoản nhà xe.')
    expect(screen.queryByRole('link', { name: 'Hoàn tiền' })).not.toBeInTheDocument()
    expect(fetchMock.mock.calls.some(([input]) => String(input).endsWith('/refunds'))).toBe(false)
  })

  it('nhà xe: menu có "Hoàn tiền", danh sách đủ vé, chuyến, tài khoản nhận và số tiền', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/hoan-tien')

    const item = await screen.findByRole('listitem', { name: 'Khoản hoàn TT00100005' })
    expect(item).toHaveTextContent('DH00100000 / VE00100001')
    expect(item).toHaveTextContent(CONFIRMED_BOOKING.chuyen.ten_tuyen)
    expect(item).toHaveTextContent('Vietcombank')
    expect(item).toHaveTextContent('0123456789')
    expect(item).toHaveTextContent('100.000 đ')
    expect(screen.getByRole('link', { name: 'Hoàn tiền' })).toHaveAttribute('aria-current', 'page')
    const [, init] = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/refunds')) ?? []
    expect(init?.headers).toMatchObject({ Authorization: 'Bearer tok' })
  })

  it('đánh dấu đã hoàn: hộp xác nhận trong trang rồi mới gửi mã giao dịch', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/hoan-tien')

    const item = await enterCode(' FT26121500 ')
    const dialog = within(item).getByRole('alertdialog', { name: 'Xác nhận đã hoàn tiền' })
    expect(dialog).toHaveTextContent('FT26121500')
    expect(completeCalls()).toHaveLength(0)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Đồng ý' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Đã đánh dấu hoàn 100.000 đ cho vé VE00100001')
    expect(screen.getByText('Không có khoản hoàn nào đang chờ.')).toBeInTheDocument()
    const [url, init] = completeCalls()[0]
    expect(String(url)).toBe('http://api.test/api/v1/refunds/TT00100005/complete')
    expect(JSON.parse(String(init?.body))).toEqual({ ma_giao_dich: 'FT26121500' })
  })

  it('bỏ trống mã giao dịch: báo lỗi, không gửi', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/hoan-tien')

    const item = await enterCode('  ')

    expect(within(item).getByText('Vui lòng nhập mã giao dịch ngân hàng')).toBeInTheDocument()
    expect(within(item).queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(completeCalls()).toHaveLength(0)
  })

  it('409 mã giao dịch trùng: hiện lỗi dưới ô, khoản hoàn vẫn trong danh sách', async () => {
    login('NHA_XE')
    mockBackend(jsonResponse(409, { detail: 'Mã giao dịch đã được dùng cho giao dịch khác', truong: 'ma_giao_dich' }))
    renderAt('/nha-xe/hoan-tien')

    const item = await enterCode('FT1')
    fireEvent.click(within(item).getByRole('button', { name: 'Đồng ý' }))

    expect(await within(item).findByText('Mã giao dịch đã được dùng cho giao dịch khác')).toBeInTheDocument()
    expect(within(item).getByLabelText('Mã giao dịch ngân hàng')).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('listitem', { name: 'Khoản hoàn TT00100005' })).toBeInTheDocument()
  })
})
