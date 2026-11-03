// sessionStorage: mỗi tab 1 đơn đang giữ (BR-BUS-18; backend chặn thêm theo số điện thoại).
// Mã truy cập chỉ dùng để mở lại đơn, tự xóa khi đóng tab.
export const BOOKING_STORAGE_KEY = 'vexe.don_dang_giu'

export type StoredBooking = {
  ma_don: string
  ma_truy_cap: string
}

export function readStoredBooking(): StoredBooking | null {
  try {
    const raw = sessionStorage.getItem(BOOKING_STORAGE_KEY)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw) as Partial<StoredBooking> | null
    if (typeof parsed?.ma_don !== 'string' || typeof parsed.ma_truy_cap !== 'string') {
      return null
    }
    return { ma_don: parsed.ma_don, ma_truy_cap: parsed.ma_truy_cap }
  } catch {
    return null
  }
}

export function saveStoredBooking(booking: StoredBooking): void {
  try {
    sessionStorage.setItem(BOOKING_STORAGE_KEY, JSON.stringify(booking))
  } catch {
    // Trình duyệt chặn storage: khách vãng lai không mở lại được đơn sau khi rời trang
  }
}

export function clearStoredBooking(): void {
  try {
    sessionStorage.removeItem(BOOKING_STORAGE_KEY)
  } catch {
    // Bỏ qua: không có gì để xóa
  }
}

/** Xóa đơn đã lưu chỉ khi đúng là đơn này, không xóa nhầm đơn khác của tab. */
export function clearStoredBookingFor(maDon: string): void {
  if (readStoredBooking()?.ma_don === maDon) {
    clearStoredBooking()
  }
}

/** Mã truy cập đã lưu của đúng đơn này; đơn khác trả null. */
export function accessCodeFor(maDon: string): string | null {
  const stored = readStoredBooking()
  return stored?.ma_don === maDon ? stored.ma_truy_cap : null
}
