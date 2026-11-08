// Dữ liệu mẫu cho test Vitest (không dùng trong ứng dụng).
import type { Booking, CancelQuoteTicket, CancelReceipt, Ticket } from '../services/bookingService'

export function ticket(overrides: Partial<Ticket> = {}): Ticket {
  return {
    ve_id: 'VE1',
    ghe_id: 'GH1',
    so_ghe: 'A01',
    gia_ve: 200000,
    trang_thai_ve: 'GIU_CHO',
    trang_thai_thanh_toan: 'CHO_THANH_TOAN',
    ho_ten: 'Trần Thị Bình',
    so_dien_thoai: '0905111222',
    diem_don: null,
    diem_tra: null,
    ...overrides,
  }
}

/** Đơn đang giữ 2 ghế trên tuyến Đà Nẵng → Lăng Cô → Huế, chưa nhập thông tin. */
export const HELD_BOOKING: Booking = {
  ma_don: 'DH00100000',
  chuyen: {
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
  },
  nguoi_dat: { ho_ten: 'Trần Thị Bình', so_dien_thoai: '0905111222', email: null },
  ve: [ticket(), ticket({ ve_id: 'VE2', ghe_id: 'GH2', so_ghe: 'A02' })],
  // Giá trị riêng của backend: trang chỉ hiển thị, không tự cộng
  tong_tien: 390000,
  han_giu_cho: '2026-12-01T03:20:00Z',
  dang_giu_cho: true,
  trang_thai_don: 'DANG_GIU',
  thoi_diem_hien_tai: '2026-12-01T03:15:00Z',
  diem_dung: ['Đà Nẵng', 'Lăng Cô', 'Huế'],
  diem_don: null,
  diem_tra: null,
  da_nhap_thong_tin: false,
  nguoi_dat_luc_giu: { ho_ten: 'Trần Thị Bình', so_dien_thoai: '0905111222' },
}

/** Đơn sau khi lưu: chuỗi điểm đón/trả do backend ghép. */
export const SAVED_BOOKING: Booking = {
  ...HELD_BOOKING,
  ve: HELD_BOOKING.ve.map((ve) => ({ ...ve, diem_don: 'Lăng Cô – 12 Lê Lợi', diem_tra: 'Huế' })),
  diem_don: { khu_vuc: 'Lăng Cô', dia_chi: '12 Lê Lợi', chuoi: 'Lăng Cô – 12 Lê Lợi' },
  diem_tra: { khu_vuc: 'Huế', dia_chi: null, chuoi: 'Huế' },
  da_nhap_thong_tin: true,
}

/** Đơn đã xác nhận trả tiền mặt (backend trả sau confirm-cash). */
export const CONFIRMED_BOOKING: Booking = {
  ...SAVED_BOOKING,
  ve: SAVED_BOOKING.ve.map((ve, index) => ({
    ...ve,
    ve_id: `VE0010000${index + 1}`,
    trang_thai_ve: 'DA_XAC_NHAN',
    trang_thai_thanh_toan: 'CHO_THU_TIEN_MAT',
  })),
  han_giu_cho: null,
  dang_giu_cho: false,
  trang_thai_don: 'DA_XAC_NHAN',
}

export function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

/** Báo giá hủy một vé do backend tính (mặc định: vé chuyển khoản, hoàn 50%). */
export function quoteTicket(overrides: Partial<CancelQuoteTicket> = {}): CancelQuoteTicket {
  return {
    ve_id: 'VE00100001',
    so_ghe: 'A01',
    gia_ve: 200000,
    trang_thai_ve: 'DA_XAC_NHAN',
    trang_thai_thanh_toan: 'DA_THANH_TOAN',
    duoc_huy: true,
    ly_do: null,
    ti_le_hoan: 50,
    // Giá trị riêng của backend: trang chỉ hiển thị, không tự tính từ giá vé
    muc_hoan: 99000,
    ghi_chu: null,
    can_tai_khoan_nhan: true,
    ...overrides,
  }
}

/** Biên lai hủy backend trả sau cancel-tickets. */
export const CANCEL_RECEIPT: CancelReceipt = {
  ma_don: 'DH00100000',
  chuyen: CONFIRMED_BOOKING.chuyen,
  ve: [
    {
      yeu_cau_id: 'YC00100000',
      ve_id: 'VE00100001',
      so_ghe: 'A01',
      gia_ve: 200000,
      muc_hoan: 99000,
      trang_thai_hoan: 'CHO_HOAN_TIEN',
      ngay_huy: '2026-12-13T20:00:00Z',
    },
  ],
  tong_hoan: 99000,
  ngan_hang_nhan: 'Vietcombank',
  so_tai_khoan_nhan: '****6789',
}
