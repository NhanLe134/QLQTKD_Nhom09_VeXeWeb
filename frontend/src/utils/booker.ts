import type { BookerAtHold, Booking } from '../services/bookingService'

/**
 * Người đặt dùng để hiển thị và so ô "Giống người đặt": họ tên, SĐT ghi trên vé lúc giữ ghế
 * (backend trả `nguoi_dat_luc_giu`); backend không xác định được thì dùng `nguoi_dat`.
 */
export function bookerReference(booking: Booking): BookerAtHold {
  return (
    booking.nguoi_dat_luc_giu ?? {
      ho_ten: booking.nguoi_dat.ho_ten,
      so_dien_thoai: booking.nguoi_dat.so_dien_thoai,
    }
  )
}
