import { get, post } from './apiClient'
import type { TripInfo } from './tripService'

/** Một khoản hoàn tiền thủ công chờ nhà xe chuyển khoản (chỉ NHA_XE). */
export type Refund = {
  thanh_toan_id: string
  yeu_cau_id: string
  ma_don: string | null
  ve_id: string
  so_ghe: string
  chuyen: TripInfo
  gia_ve: number
  so_tien: number
  ngay_huy: string
  ngan_hang_nhan: string | null
  so_tai_khoan_nhan: string | null
  trang_thai_thanh_toan: 'CHO_THANH_TOAN' | 'DA_THANH_TOAN' | 'THAT_BAI'
  ngay_thanh_toan: string | null
  ma_giao_dich: string | null
}

export function getPendingRefunds(): Promise<Refund[]> {
  return get<Refund[]>('/api/v1/refunds')
}

/** Đánh dấu đã hoàn bằng mã giao dịch ngân hàng; gọi lại cùng mã trả kết quả cũ. */
export function markRefunded(thanhToanId: string, maGiaoDich: string): Promise<Refund> {
  return post<Refund>(`/api/v1/refunds/${encodeURIComponent(thanhToanId)}/complete`, {
    ma_giao_dich: maGiaoDich,
  })
}
