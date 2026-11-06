import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AuthProvider, { AUTH_STORAGE_KEY } from '../context/AuthProvider'
import { routes } from '../routes'
import type { Driver, OperatorTrip } from '../services/operatorService'
import { todayInVietnam } from '../utils/format'
import { CONFIRMED_BOOKING, jsonResponse } from '../utils/testBookings'

const fetchMock = vi.fn<typeof fetch>()

const DRIVERS: Driver[] = [
  { tai_xe_id: 'TX00000001', ho_ten: 'Tài Xế Mẫu' },
  { tai_xe_id: 'TX00000002', ho_ten: 'Tài Xế Hai' },
]

const TRIP: OperatorTrip = {
  chuyen: CONFIRMED_BOOKING.chuyen,
  trang_thai: 'MO_BAN',
  tai_xe: null,
}

function login(vaiTro: string) {
  sessionStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ token: 'tok', vai_tro: vaiTro, ho_ten: 'Nhà Xe' }))
}

function mockBackend(assign: Response = jsonResponse(200, { ...TRIP, tai_xe: DRIVERS[1] })) {
  fetchMock.mockImplementation(async (input) => {
    const url = String(input)
    if (url.includes('/operator/trips?')) return jsonResponse(200, [TRIP])
    if (url.includes('/operator/drivers?')) return jsonResponse(200, DRIVERS)
    if (url.endsWith('/driver')) return assign.clone()
    return new Promise<Response>(() => {})
  })
}

function calls(part: string) {
  return fetchMock.mock.calls.filter(([input]) => String(input).includes(part))
}

function assignCalls() {
  return fetchMock.mock.calls.filter(([input]) => String(input).endsWith('/driver'))
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

async function chooseDriver(taiXeId: string) {
  const item = await screen.findByRole('listitem', { name: 'Chuyến CX00000001' })
  fireEvent.change(within(item).getByLabelText('Chọn tài xế'), { target: { value: taiXeId } })
  fireEvent.click(within(item).getByRole('button', { name: 'Lưu' }))
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

describe('TripAssignmentPage (/nha-xe/phan-cong)', () => {
  it.each(['KHACH', 'TAI_XE'])('vai trò %s: báo trang chỉ dành cho nhà xe, không gọi API', (vaiTro) => {
    login(vaiTro)
    mockBackend()
    renderAt('/nha-xe/phan-cong')

    expect(screen.getByRole('alert')).toHaveTextContent('Trang này chỉ dành cho tài khoản nhà xe.')
    expect(calls('/operator/')).toHaveLength(0)
  })

  it('tải chuyến và tài xế theo ngày; đổi ngày thì tải lại', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/phan-cong')

    const item = await screen.findByRole('listitem', { name: 'Chuyến CX00000001' })
    expect(item).toHaveTextContent('Đà Nẵng - Huế')
    expect(item).toHaveTextContent('Chưa phân công')
    expect(within(item).getAllByRole('option').map((o) => o.textContent)).toEqual([
      '— Chọn tài xế —',
      'Tài Xế Mẫu (TX00000001)',
      'Tài Xế Hai (TX00000002)',
    ])
    expect(String(calls('/operator/trips?')[0][0])).toContain(`ngay=${todayInVietnam()}`)

    fireEvent.change(screen.getByLabelText('Ngày khởi hành'), { target: { value: '2026-12-15' } })

    await screen.findByRole('listitem', { name: 'Chuyến CX00000001' })
    expect(String(calls('/operator/trips?').at(-1)?.[0])).toContain('ngay=2026-12-15')
    expect(String(calls('/operator/drivers?').at(-1)?.[0])).toContain('ngay=2026-12-15')
  })

  it('Lưu: gửi PUT với tài xế đã chọn và cập nhật tài xế hiện tại', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/phan-cong')

    const item = await chooseDriver('TX00000002')

    expect(await within(item).findByRole('status')).toHaveTextContent('Đã phân công Tài Xế Hai (TX00000002).')
    expect(item).toHaveTextContent('Tài Xế Hai (TX00000002)')
    const [url, init] = assignCalls()[0]
    expect(String(url)).toBe('http://api.test/api/v1/operator/trips/CX00000001/driver')
    expect(init?.method).toBe('PUT')
    expect(JSON.parse(String(init?.body))).toEqual({ tai_xe_id: 'TX00000002' })
  })

  it('chưa chọn tài xế: báo lỗi, không gửi', async () => {
    login('NHA_XE')
    mockBackend()
    renderAt('/nha-xe/phan-cong')

    const item = await chooseDriver('')

    expect(within(item).getByRole('alert')).toHaveTextContent('Vui lòng chọn tài xế')
    expect(assignCalls()).toHaveLength(0)
  })

  it('400 trùng giờ (truong tai_xe_id): lỗi hiện ngay dưới ô chọn tài xế của đúng chuyến', async () => {
    login('NHA_XE')
    const detail = 'Tài xế đã được phân công chuyến CX00000007 trùng giờ'
    mockBackend(jsonResponse(400, { detail, truong: 'tai_xe_id' }))
    renderAt('/nha-xe/phan-cong')

    const item = await chooseDriver('TX00000001')

    const error = await within(item).findByRole('alert')
    expect(error).toHaveTextContent(detail)
    const select = within(item).getByLabelText('Chọn tài xế')
    expect(select).toHaveAttribute('aria-invalid', 'true')
    expect(select).toHaveAttribute('aria-describedby', error.id)
    expect(item).toHaveTextContent('Chưa phân công')
  })
})
