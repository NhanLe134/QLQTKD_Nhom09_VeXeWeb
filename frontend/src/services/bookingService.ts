import { accessCodeFor, clearStoredBookingFor, moveToConfirmed, saveStoredBooking } from '../utils/bookingStorage'
import { get, post, put, type RequestHeaders } from './apiClient'
import type { TripInfo } from './tripService'

export type NguoiDat = {
  ho_ten: string
  so_dien_thoai: string
  email: string | null
}

export type HoldRequest = {
  chuyen_xe_id: string
  /** Gửi `ghe_ids` hoặc `dat_ca_xe: true`, không gửi cả hai */
  ghe_ids?: string[]
  dat_ca_xe?: boolean
  /** Chỉ khách vãng lai; khách đã đăng nhập thì backend dùng hồ sơ tài khoản */
  nguoi_dat?: NguoiDat
}

export type HeldSeat = {
  ghe_id: string
  so_ghe: string
  gia_ve: number
}

export type HoldResponse = {
  ma_don: string
  /** Chỉ có trong response này; gửi lại qua header X-Ma-Truy-Cap */
  ma_truy_cap: string
  han_giu_cho: string
  thoi_diem_hien_tai: string
  ghe: HeldSeat[]
  tong_tien: number
}

export type TrangThaiVe = 'GIU_CHO' | 'DA_XAC_NHAN' | 'DA_HUY'

/** Trạng thái tổng của đơn do backend tính (docs/API.md) */
export type TrangThaiDon = 'DANG_GIU' | 'HET_HAN' | 'DA_HUY' | 'DA_XAC_NHAN'

export type TrangThaiThanhToanVe = 'CHO_THANH_TOAN' | 'CHO_THU_TIEN_MAT' | 'DA_THANH_TOAN'

export type Ticket = {
  /** Mã vé điện tử (docs/API.md) */
  ve_id: string
  ghe_id: string
  so_ghe: string
  gia_ve: number
  trang_thai_ve: TrangThaiVe
  trang_thai_thanh_toan: TrangThaiThanhToanVe
  ho_ten: string | null
  so_dien_thoai: string | null
  /** Chuỗi backend đã lưu ("Khu vực – địa chỉ"); null khi chưa nhập */
  diem_don: string | null
  diem_tra: string | null
}

/** Điểm đón/trả của đơn; backend tách sẵn, frontend không tự tách hay ghép chuỗi. */
export type BookingPoint = {
  khu_vuc: string
  dia_chi: string | null
  /** Chuỗi đúng như đã lưu, dùng để hiển thị */
  chuoi: string
}

export type BookerAtHold = {
  ho_ten: string
  so_dien_thoai: string
}

export type Booking = {
  ma_don: string
  chuyen: TripInfo
  nguoi_dat: NguoiDat
  ve: Ticket[]
  /** Tổng tiền do backend tính (vé chưa hủy) */
  tong_tien: number
  han_giu_cho: string | null
  /** Còn vé đang giữ chưa quá hạn */
  dang_giu_cho: boolean
  trang_thai_don: TrangThaiDon
  thoi_diem_hien_tai: string
  /** Điểm dừng của tuyến theo thứ tự: điểm đi, điểm trung gian, điểm đến */
  diem_dung: string[]
  diem_don: BookingPoint | null
  diem_tra: BookingPoint | null
  /** Mọi vé chưa hủy đã có điểm đón/trả hợp lệ (backend tính) */
  da_nhap_thong_tin: boolean
  /** Họ tên, SĐT người đặt ghi trên vé lúc giữ ghế; null khi backend không xác định được */
  nguoi_dat_luc_giu: BookerAtHold | null
}

export type PassengerInput = {
  ve_id: string
  ho_ten: string
  so_dien_thoai: string
}

export type PointInput = {
  khu_vuc: string
  dia_chi: string | null
}

export type BookingDetailsRequest = {
  /** Vé không gửi thì backend giữ nguyên họ tên, SĐT hiện có trên vé */
  hanh_khach: PassengerInput[]
  diem_don: PointInput
  diem_tra: PointInput
}

function accessHeaders(maDon: string): RequestHeaders | undefined {
  const code = accessCodeFor(maDon)
  return code ? { 'X-Ma-Truy-Cap': code } : undefined
}

/** Giữ ghế; thành công thì lưu mã đơn và mã truy cập để mở lại đơn. */
export async function holdSeats(data: HoldRequest): Promise<HoldResponse> {
  const result = await post<HoldResponse>('/api/v1/bookings/hold', data)
  saveStoredBooking({ ma_don: result.ma_don, ma_truy_cap: result.ma_truy_cap })
  return result
}

export function getBooking(maDon: string): Promise<Booking> {
  return get<Booking>(`/api/v1/bookings/${encodeURIComponent(maDon)}`, accessHeaders(maDon))
}

/** Hủy đơn đang giữ (BR-BUS-33); thành công thì xóa đơn khỏi tab. */
export async function cancelBooking(maDon: string): Promise<Booking> {
  const result = await post<Booking>(
    `/api/v1/bookings/${encodeURIComponent(maDon)}/cancel`,
    undefined,
    accessHeaders(maDon),
  )
  clearStoredBookingFor(maDon)
  return result
}

/** Lưu hành khách và điểm đón/trả (BR-BUS-21 đến 26); trả chi tiết đơn đã đọc lại. */
export function saveBookingDetails(maDon: string, data: BookingDetailsRequest): Promise<Booking> {
  return put<Booking>(`/api/v1/bookings/${encodeURIComponent(maDon)}/details`, data, accessHeaders(maDon))
}

/**
 * Trả tiền mặt khi lên xe (BR-BUS-28); gọi lại trả kết quả cũ (backend idempotent).
 * Thành công thì giữ mã truy cập ở kho đơn đã xác nhận để tải lại trang vẫn xem được vé.
 */
export async function confirmCash(maDon: string): Promise<Booking> {
  const result = await post<Booking>(
    `/api/v1/bookings/${encodeURIComponent(maDon)}/confirm-cash`,
    undefined,
    accessHeaders(maDon),
  )
  moveToConfirmed(maDon)
  return result
}

/** Một đơn trong "Vé của tôi": vé đã xác nhận gom theo mã đơn. */
export type MyBooking = {
  ma_don: string
  chuyen: TripInfo
  ngay_dat: string
  /** Tổng tiền do backend tính */
  tong_tien: number
  trang_thai_don: TrangThaiDon
  ve: Ticket[]
}

/** Vé đã xác nhận của khách đang đăng nhập, mới nhất trước (BR-BUS-36). */
export function getMyTickets(): Promise<MyBooking[]> {
  return get<MyBooking[]>('/api/v1/me/tickets')
}

/** Mã QR chuyển khoản SePay của đơn (BR-BUS-29); đếm ngược do frontend chạy. */
export type QrSePay = {
  ma_don: string
  so_tien: number
  /** Nội dung chuyển khoản "THANH TOAN VE {ma_don}", khách không được sửa */
  noi_dung: string
  /** Ảnh QR dựng sẵn (VietQR) để hiển thị trực tiếp */
  qr_url: string
  /** Cửa sổ chuyển khoản hiển thị cho khách (giây) */
  thoi_gian_cho_giay: number
}

/**
 * Tạo mã QR chuyển khoản SePay (BR-BUS-29); gọi lại trả đúng QR cũ (NFR-BUS-05).
 * Khách chọn chuyển khoản thì gọi, chọn lại tiền mặt thì không gọi thêm.
 */
export function taoQrSePay(maDon: string): Promise<QrSePay> {
  return post<QrSePay>(
    `/api/v1/bookings/${encodeURIComponent(maDon)}/pay-sepay`,
    undefined,
    accessHeaders(maDon),
  )
}
