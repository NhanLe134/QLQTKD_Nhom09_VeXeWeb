import { get, post, put } from './apiClient'
import type { TripInfo } from './tripService'

export type TripStatus = 'MO_BAN' | 'NGUNG_BAN' | 'HOAN_THANH' | 'DA_HUY'
export type DepositStatus = 'CHO_XAC_NHAN' | 'DA_XAC_NHAN' | 'TU_CHOI'

export type Driver = {
  tai_xe_id: string
  ho_ten: string | null
}

/** Chuyến của nhà xe kèm tài xế đang được phân công (chỉ NHA_XE). */
export type OperatorTrip = {
  chuyen: TripInfo
  trang_thai: TripStatus
  tai_xe: Driver | null
}

/** Khoản tài xế nộp tiền mặt; số tiền do backend tính. */
export type CashDeposit = {
  nop_tien_id: string
  tai_xe_id: string
  ten_tai_xe: string | null
  chuyen: TripInfo
  so_tien: number
  ngay_nop: string
  trang_thai: DepositStatus
  ngay_xac_nhan: string | null
}

/** `ngay` dạng YYYY-MM-DD theo giờ Việt Nam. */
export function getOperatorTrips(ngay: string): Promise<OperatorTrip[]> {
  return get<OperatorTrip[]>(`/api/v1/operator/trips?ngay=${encodeURIComponent(ngay)}`)
}

/** Tài xế còn làm việc cho nhà xe vào ngày `ngay`. */
export function getDrivers(ngay: string): Promise<Driver[]> {
  return get<Driver[]>(`/api/v1/operator/drivers?ngay=${encodeURIComponent(ngay)}`)
}

/** Lỗi trùng giờ / tài xế ngoài nhà xe trả `truong = "tai_xe_id"`. */
export function assignDriver(chuyenXeId: string, taiXeId: string): Promise<OperatorTrip> {
  return put<OperatorTrip>(`/api/v1/operator/trips/${encodeURIComponent(chuyenXeId)}/driver`, {
    tai_xe_id: taiXeId,
  })
}

export function getCashDeposits(trangThai: DepositStatus): Promise<CashDeposit[]> {
  return get<CashDeposit[]>(`/api/v1/operator/cash-deposits?trang_thai=${trangThai}`)
}

export function confirmCashDeposit(nopTienId: string): Promise<CashDeposit> {
  return post<CashDeposit>(`/api/v1/operator/cash-deposits/${encodeURIComponent(nopTienId)}/confirm`)
}

export function rejectCashDeposit(nopTienId: string): Promise<CashDeposit> {
  return post<CashDeposit>(`/api/v1/operator/cash-deposits/${encodeURIComponent(nopTienId)}/reject`)
}
