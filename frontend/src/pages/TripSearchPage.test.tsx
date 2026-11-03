import { fireEvent, render, screen, within } from '@testing-library/react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Trip, TripSearchResult } from '../services/tripService'
import TripSearchPage from './TripSearchPage'

const fetchMock = vi.fn<typeof fetch>()

const LOCATIONS = {
  diem_di: ['Đà Nẵng', 'Hội An', 'Huế'],
  diem_den: ['Đà Nẵng', 'Hội An', 'Huế'],
}

function trip(overrides: Partial<Trip>): Trip {
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

const TRIPS: TripSearchResult = {
  chuyen: [
    trip({}),
    trip({
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

const NO_TRIP_WITH_SUGGESTIONS: TripSearchResult = {
  chuyen: [],
  goi_y: [
    trip({
      chuyen_xe_id: 'CX00000006',
      ten_tuyen: 'Đà Nẵng - Hội An',
      diem_den: 'Hội An',
      diem_trung_gian: null,
      ngay_khoi_hanh: '2026-12-16',
      gio_di: '2026-12-16T01:00:00Z',
      gio_den: '2026-12-16T02:00:00Z',
    }),
  ],
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Giả lập backend: /locations luôn thành công, /trips trả theo hàm `trips`. */
function mockBackend(trips: (url: URL) => Response | Promise<Response>) {
  fetchMock.mockImplementation(async (input) => {
    const url = new URL(String(input))
    if (url.pathname === '/api/v1/locations') {
      return jsonResponse(200, LOCATIONS)
    }
    return trips(url)
  })
}

function tripRequests(): URL[] {
  return fetchMock.mock.calls
    .map(([input]) => new URL(String(input)))
    .filter((url) => url.pathname === '/api/v1/trips')
}

function renderAt(path: string) {
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

const SEARCH_PATH = `/tim-chuyen?${new URLSearchParams({ di: 'Đà Nẵng', den: 'Huế', ngay: '2026-12-15' })}`

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

describe('TripSearchPage', () => {
  it('chưa có tiêu chí thì chỉ hiện form, không gọi tìm chuyến', async () => {
    mockBackend(() => jsonResponse(200, TRIPS))
    renderAt('/tim-chuyen')

    expect(await screen.findAllByRole('option', { name: 'Hội An' })).toHaveLength(2)
    expect(tripRequests()).toHaveLength(0)
  })

  it('submit form ghi tiêu chí lên URL và tìm chuyến', async () => {
    mockBackend(() => jsonResponse(200, TRIPS))
    const router = renderAt('/tim-chuyen')
    await screen.findAllByRole('option', { name: 'Huế' })

    fireEvent.change(screen.getByLabelText('Điểm đi'), { target: { value: 'Đà Nẵng' } })
    fireEvent.change(screen.getByLabelText('Điểm đến'), { target: { value: 'Huế' } })
    fireEvent.change(screen.getByLabelText('Ngày đi'), { target: { value: '2026-12-15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Tìm chuyến' }))

    expect(await screen.findByText('06:00 → 08:30')).toBeInTheDocument()
    const params = new URLSearchParams(router.state.location.search)
    expect(Object.fromEntries(params)).toEqual({ di: 'Đà Nẵng', den: 'Huế', ngay: '2026-12-15' })
  })

  it('đọc tiêu chí từ URL (tải lại trang vẫn giữ kết quả) và hiện danh sách thẻ', async () => {
    mockBackend(() => jsonResponse(200, TRIPS))
    renderAt(SEARCH_PATH)

    expect(screen.getByRole('status')).toHaveTextContent('Đang tìm chuyến…')
    const cards = await screen.findAllByRole('article')
    expect(cards).toHaveLength(2)

    const [request] = tripRequests()
    expect(Object.fromEntries(request.searchParams)).toEqual({
      diem_di: 'Đà Nẵng',
      diem_den: 'Huế',
      ngay: '2026-12-15',
    })
    expect(screen.getByLabelText('Điểm đi')).toHaveValue('Đà Nẵng')
    expect(screen.getByLabelText('Ngày đi')).toHaveValue('2026-12-15')

    // Thẻ 1: còn ghế → link chọn chuyến
    expect(within(cards[0]).getByText('200.000 đ')).toBeInTheDocument()
    expect(within(cards[0]).getByText('Còn 4 ghế trống')).toBeInTheDocument()
    expect(within(cards[0]).getByRole('link', { name: 'Chọn chuyến' })).toHaveAttribute(
      'href',
      '/chuyen/CX00000001',
    )
    // Thẻ 2: hết ghế → nút bị khóa
    expect(within(cards[1]).getByText('07:00 → 09:30')).toBeInTheDocument()
    expect(within(cards[1]).getByText('150.000 đ')).toBeInTheDocument()
    expect(within(cards[1]).getByText('Hết ghế')).toBeInTheDocument()
    expect(within(cards[1]).getByRole('button', { name: 'Chọn chuyến' })).toBeDisabled()
  })

  it('bấm "Chọn chuyến" mở trang chuyến', async () => {
    mockBackend(() => jsonResponse(200, TRIPS))
    const router = renderAt(SEARCH_PATH)

    const [card] = await screen.findAllByRole('article')
    fireEvent.click(within(card).getByRole('link', { name: 'Chọn chuyến' }))

    expect(await screen.findByRole('heading', { name: 'Trang chuyến' })).toBeInTheDocument()
    expect(router.state.location.pathname).toBe('/chuyen/CX00000001')
  })

  it('hiện nguyên văn lỗi từ backend và cho thử lại', async () => {
    let calls = 0
    mockBackend(() => {
      calls += 1
      return calls === 1
        ? jsonResponse(400, { detail: 'Không thể tìm chuyến cho ngày đã qua' })
        : jsonResponse(200, TRIPS)
    })
    renderAt(SEARCH_PATH)

    expect(await screen.findByRole('alert')).toHaveTextContent('Không thể tìm chuyến cho ngày đã qua')

    fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }))

    expect(await screen.findAllByRole('article')).toHaveLength(2)
    expect(tripRequests()).toHaveLength(2)
  })

  it('không có chuyến thì hiện gợi ý; bấm gợi ý thì tìm theo ngày đó', async () => {
    mockBackend((url) =>
      jsonResponse(
        200,
        url.searchParams.get('ngay') === '2026-12-16'
          ? { chuyen: [NO_TRIP_WITH_SUGGESTIONS.goi_y[0]], goi_y: [] }
          : NO_TRIP_WITH_SUGGESTIONS,
      ),
    )
    const path = `/tim-chuyen?${new URLSearchParams({ di: 'Đà Nẵng', den: 'Hội An', ngay: '2026-12-15' })}`
    const router = renderAt(path)

    expect(await screen.findByText('Không có chuyến phù hợp ngày 15/12/2026.')).toBeInTheDocument()
    const suggestion = screen.getByRole('button', { name: /Ngày 16\/12\/2026/ })
    expect(suggestion).toHaveTextContent('08:00')
    expect(suggestion).toHaveTextContent('200.000 đ')

    fireEvent.click(suggestion)

    expect(await screen.findByText('08:00 → 09:00')).toBeInTheDocument()
    expect(new URLSearchParams(router.state.location.search).get('ngay')).toBe('2026-12-16')
    expect(tripRequests().at(-1)?.searchParams.get('ngay')).toBe('2026-12-16')
    expect(screen.getByLabelText('Ngày đi')).toHaveValue('2026-12-16')
  })

  it('không có chuyến và không có gợi ý', async () => {
    mockBackend(() => jsonResponse(200, { chuyen: [], goi_y: [] }))
    renderAt(SEARCH_PATH)

    expect(await screen.findByText('Không có chuyến phù hợp ngày 15/12/2026.')).toBeInTheDocument()
    expect(screen.getByText('Không có chuyến cùng tuyến vào ngày trước hoặc sau.')).toBeInTheDocument()
  })

  it('không tải được danh sách điểm thì báo lỗi và cho thử lại', async () => {
    let failed = false
    fetchMock.mockImplementation(async () => {
      if (!failed) {
        failed = true
        throw new TypeError('network')
      }
      return jsonResponse(200, LOCATIONS)
    })
    renderAt('/tim-chuyen')

    expect(await screen.findByRole('alert')).toHaveTextContent('Không kết nối được máy chủ')

    fireEvent.click(screen.getByRole('button', { name: 'Thử lại' }))

    expect(await screen.findAllByRole('option', { name: 'Hội An' })).toHaveLength(2)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
