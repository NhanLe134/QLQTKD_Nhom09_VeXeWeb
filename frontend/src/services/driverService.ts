import { get, post } from './apiClient'
import type { CashDeposit, TripStatus } from './operatorService'
import type { TripInfo } from './tripService'

/** Chuyến được phân công cho tài xế đang đăng nhập (chỉ TAI_XE). */
export type DriverTrip = {
  chuyen: TripInfo
  trang_thai: TripStatus
  so_khach: number
}

export type Passenger = {
  ve_id: string
  ma_don: string
  so_ghe: string
  ho_ten: string | null
  so_dien_thoai: string | null
  diem_don: string | null
  diem_tra: string | null
  trang_thai_thanh_toan: 'CHO_THANH_TOAN' | 'CHO_THU_TIEN_MAT' | 'DA_THANH_TOAN'
  so_tien_can_thu: number
  co_the_thu_tien: boolean
}

/** Tiền mặt của chuyến do backend tính; frontend chỉ hiển thị. */
export type CashSummary = {
  tong_da_thu: number
  tong_chua_thu: number
  da_nop: number
  dang_cho: number
  co_the_nop: number
}

export type DriverTripDetail = {
  chuyen: TripInfo
  trang_thai: TripStatus
  khach: Passenger[]
  tien_mat: CashSummary
  co_the_nop_tien: boolean
  co_the_ket_thuc: boolean
  khoan_nop: CashDeposit[]
  thoi_diem_hien_tai: string
}

export function getDriverTrips(): Promise<DriverTrip[]> {
  return get<DriverTrip[]>('/api/v1/driver/trips')
}

export function getDriverTrip(chuyenXeId: string): Promise<DriverTripDetail> {
  return get<DriverTripDetail>(`/api/v1/driver/trips/${encodeURIComponent(chuyenXeId)}`)
}

/** Đánh dấu đã thu tiền mặt một vé; gọi lại không lỗi. Trả lại chi tiết chuyến mới. */
export function collectCash(chuyenXeId: string, veId: string): Promise<DriverTripDetail> {
  return post<DriverTripDetail>(
    `/api/v1/driver/trips/${encodeURIComponent(chuyenXeId)}/tickets/${encodeURIComponent(veId)}/collect-cash`,
  )
}

/** Nộp tiền mặt của chuyến; số tiền do backend tính. */
export function submitCashDeposit(chuyenXeId: string): Promise<CashDeposit> {
  return post<CashDeposit>(`/api/v1/driver/trips/${encodeURIComponent(chuyenXeId)}/cash-deposits`)
}

export function completeTrip(chuyenXeId: string): Promise<DriverTripDetail> {
  return post<DriverTripDetail>(`/api/v1/driver/trips/${encodeURIComponent(chuyenXeId)}/complete`)
}
