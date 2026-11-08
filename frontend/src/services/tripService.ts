import { get } from './apiClient'

export type Locations = {
  diem_di: string[]
  diem_den: string[]
}

export type Trip = {
  chuyen_xe_id: string
  ten_tuyen: string
  diem_di: string
  diem_den: string
  diem_trung_gian: string | null
  /** Ngày theo giờ Việt Nam, YYYY-MM-DD */
  ngay_khoi_hanh: string
  /** UTC, ISO 8601 */
  gio_di: string
  gio_den: string | null
  ten_loai_xe: string | null
  so_cho: number
  /** Giá mỗi ghế (VND), do backend tính theo loại xe */
  gia_ve: number
  so_ghe_trong: number
}

/** Thông tin chuyến trên trang chọn ghế (không có số ghế trống). */
export type TripInfo = Omit<Trip, 'so_ghe_trong'>

/** Trạng thái hiển thị do backend tính: ghế giữ đã quá hạn hiện TRONG. */
export type SeatStatus = 'TRONG' | 'GIU_CHO' | 'DA_BAN'

export type Seat = {
  ghe_id: string
  so_ghe: string
  trang_thai: SeatStatus
}

export type SeatMap = {
  chuyen: TripInfo
  /** Chuyến đang mở bán và chưa khởi hành */
  co_the_dat: boolean
  ghe: Seat[]
  /** Giờ server (UTC) */
  thoi_diem_hien_tai: string
}

export type TripSearchResult = {
  chuyen: Trip[]
  /** Chỉ có phần tử khi `chuyen` rỗng: cùng tuyến, ±1 ngày */
  goi_y: Trip[]
}

export type TripSearchQuery = {
  diemDi: string
  diemDen: string
  ngay: string
}

export function getLocations(): Promise<Locations> {
  return get<Locations>('/api/v1/locations')
}

export function searchTrips({ diemDi, diemDen, ngay }: TripSearchQuery): Promise<TripSearchResult> {
  const query = new URLSearchParams({ diem_di: diemDi, diem_den: diemDen, ngay })
  return get<TripSearchResult>(`/api/v1/trips?${query.toString()}`)
}

export function getTripSeats(chuyenXeId: string): Promise<SeatMap> {
  return get<SeatMap>(`/api/v1/trips/${encodeURIComponent(chuyenXeId)}/seats`)
}
