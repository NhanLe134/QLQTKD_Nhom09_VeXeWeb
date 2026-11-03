import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import BookingDetailsForm from '../components/BookingDetailsForm'
import BookingDetailsSummary from '../components/BookingDetailsSummary'
import BookingFailed, { type FailureReason } from '../components/BookingFailed'
import BookingSuccess from '../components/BookingSuccess'
import CancelBookingButton from '../components/CancelBookingButton'
import CashConfirmDialog from '../components/CashConfirmDialog'
import HoldCountdown from '../components/HoldCountdown'
import PaymentMethodPicker from '../components/PaymentMethodPicker'
import QrSePayPanel from '../components/QrSePayPanel'
import { useCountdown } from '../hooks/useCountdown'
import { type Booking, taoQrSePay, type QrSePay, getBooking } from '../services/bookingService'
import { bookerReference } from '../utils/booker'
import { clearStoredBookingFor, moveToConfirmed } from '../utils/bookingStorage'
import { formatCurrency, formatDate, formatTime, formatVehicleType } from '../utils/format'
import { ApiError } from '../services/apiClient'

type BookingState =
  | { state: 'loading' }
  | { state: 'loaded'; data: Booking; clockOffsetMs: number }
  | { state: 'error'; message: string }

export default function BookingPage() {
  const { maDon = '' } = useParams()
  const [booking, setBooking] = useState<BookingState>({ state: 'loading' })

  useEffect(() => {
    let cancelled = false
    getBooking(maDon)
      .then((data) => {
        if (cancelled) return
        // Độ lệch giữa giờ server và máy khách, để đếm ngược đúng hạn giữ của server
        const clockOffsetMs = Date.parse(data.thoi_diem_hien_tai) - Date.now()
        setBooking({ state: 'loaded', data, clockOffsetMs })
      })
      .catch((error: unknown) => {
        if (!cancelled) setBooking({ state: 'error', message: error instanceof Error ? error.message : String(error) })
      })
    return () => {
      cancelled = true
    }
  }, [maDon])

  if (booking.state !== 'loaded') {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-bold">Đặt vé</h1>
        {booking.state === 'loading' ? (
          <p role="status" className="text-slate-600">
            Đang tải đơn…
          </p>
        ) : (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {booking.message}
          </p>
        )}
      </section>
    )
  }

  // Giữ nguyên độ lệch giờ khi cập nhật đơn: hạn giữ không đổi nên đồng hồ chạy tiếp (BR-BUS-26)
  const { clockOffsetMs } = booking
  return (
    <BookingDetail
      data={booking.data}
      clockOffsetMs={clockOffsetMs}
      onChange={(data) => setBooking({ state: 'loaded', data, clockOffsetMs })}
    />
  )
}

type DetailProps = {
  data: Booking
  clockOffsetMs: number
  onChange: (data: Booking) => void
}

type Step = 'details' | 'payment' | 'confirm-cash'

type FieldError = { field: string; message: string }

// Tách riêng để useCountdown bắt đầu đếm đúng lúc đã có dữ liệu đơn
function BookingDetail({ data, clockOffsetMs, onChange }: DetailProps) {
  const [cancelled, setCancelled] = useState(false)
  const [gone, setGone] = useState(false)
  // Đã lưu thông tin thì hiện tóm tắt, bấm "Sửa" để nhập lại
  const [editing, setEditing] = useState(!data.da_nhap_thong_tin)
  const [step, setStep] = useState<Step>('details')
  // Lỗi kèm tên trường khi xác nhận thanh toán: mở lại form và báo đúng ô
  const [detailsError, setDetailsError] = useState<FieldError | null>(null)
  const dangGiu = data.trang_thai_don === 'DANG_GIU'
  const remainingMs = useCountdown(dangGiu ? data.han_giu_cho : null, clockOffsetMs)
  // Hết giờ trên đồng hồ thì coi như hết giữ chỗ ngay, không chờ tải lại đơn
  const holding = remainingMs !== null && remainingMs > 0
  const failure = failureReason(data, cancelled, dangGiu && !holding, gone)
  const { chuyen } = data
  const heldTickets = data.ve.filter((ve) => ve.trang_thai_ve !== 'DA_HUY')

  // ---- Chuyển khoản SePay (BR-BUS-29): QR hiện ngay khi chọn, đếm ngược 5 phút ở đây ----
  const [qrSePay, setQrSePay] = useState<QrSePay | null>(null)
  const [hanQr, setSepayDeadline] = useState<string | null>(null)
  const [dangTaoQr, setSepayLoading] = useState(false)
  const [loiQr, setSepayError] = useState<string | null>(null)
  const qrConLaiMs = useCountdown(qrSePay ? hanQr : null, 0)

  function xuLyChonChuyenKhoan() {
    if (qrSePay) {
      // Chọn lại: cùng QR (backend idempotent), đồng hồ 5 phút bắt đầu lại
      setSepayDeadline(new Date(Date.now() + qrSePay.thoi_gian_cho_giay * 1000).toISOString())
      return
    }
    setSepayLoading(true)
    setSepayError(null)
    taoQrSePay(data.ma_don)
      .then((qr) => {
        setQrSePay(qr)
        setSepayDeadline(new Date(Date.now() + qr.thoi_gian_cho_giay * 1000).toISOString())
        // Backend gia hạn giữ chỗ thêm 10 phút khi tạo QR: tải lại đơn để
        // đồng hồ giữ chỗ hiện hạn mới
        getBooking(data.ma_don).then(onChange).catch(() => {})
      })
      .catch((error: unknown) => {
        setSepayError(error instanceof ApiError ? error.detail : 'Không tạo được mã QR, vui lòng thử lại.')
      })
      .finally(() => setSepayLoading(false))
  }

  // Webhook SePay xác nhận đơn ở backend: hỏi lại đơn mỗi 2 giây để chuyển
  // "Đặt vé thành công" ngay khi webhook ghi xong (US-BUS-05 AC2);
  // dừng khi đơn không còn đang giữ
  useEffect(() => {
    if (!qrSePay || step !== 'payment' || data.trang_thai_don !== 'DANG_GIU') return
    const timer = setInterval(() => {
      getBooking(data.ma_don)
        .then((latest) => {
          if (latest.trang_thai_don === 'DA_XAC_NHAN') moveToConfirmed(latest.ma_don)
          if (latest.trang_thai_don !== 'DANG_GIU') onChange(latest)
        })
        .catch(() => {})
    }, 2000)
    return () => clearInterval(timer)
  }, [qrSePay, step, data.ma_don, data.trang_thai_don, onChange])

  useEffect(() => {
    if (failure) clearStoredBookingFor(data.ma_don)
  }, [failure, data.ma_don])

  // 410 khi lưu: tải lại đơn để hiện đúng lý do theo trạng thái backend
  function handleGone() {
    getBooking(data.ma_don)
      .then(onChange)
      .catch(() => setGone(true))
  }

  if (failure) {
    return <BookingFailed reason={failure} maDon={data.ma_don} chuyenXeId={chuyen.chuyen_xe_id} />
  }

  // Trạng thái do backend quyết định; mở lại hoặc tải lại đơn đã xác nhận cũng hiện vé
  if (data.trang_thai_don === 'DA_XAC_NHAN') {
    return <BookingSuccess booking={data} />
  }

  function showFieldError(field: string, message: string) {
    setDetailsError({ field, message })
    setEditing(true)
    setStep('details')
  }

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold">Đặt vé</h1>
      <p className="text-slate-600">
        Mã đơn: <span className="font-semibold text-slate-900">{data.ma_don}</span>
      </p>

      {dangGiu && <HoldCountdown remainingMs={remainingMs} />}

      <div className="space-y-1 rounded-lg border border-slate-200 bg-white p-4">
        <p className="text-lg font-semibold">{chuyen.ten_tuyen}</p>
        <p className="text-slate-700">
          {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
        </p>
        <p className="text-sm text-slate-600">{formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)}</p>
      </div>

      <div className="space-y-2 rounded-lg border border-slate-200 bg-white p-4">
        <h2 className="font-semibold">Ghế đã giữ</h2>
        <ul aria-label="Ghế đã giữ" className="divide-y divide-slate-100">
          {heldTickets.map((ve) => (
            <li key={ve.ve_id} className="flex justify-between py-1">
              <span>Ghế {ve.so_ghe}</span>
              <span>{formatCurrency(ve.gia_ve)}</span>
            </li>
          ))}
        </ul>
        <p className="flex justify-between border-t border-slate-200 pt-2 font-semibold">
          <span>Tổng tiền</span>
          <span data-testid="tong-tien">{formatCurrency(data.tong_tien)}</span>
        </p>
      </div>

      {holding && (
        <>
          {step === 'details' && (
            <div className="space-y-4 rounded-lg border border-slate-200 bg-white p-4">
              <h2 className="text-lg font-semibold">Thông tin hành khách</h2>
              <BookerInfo data={data} />
              {editing ? (
                <BookingDetailsForm
                  key={detailsError ? `${detailsError.field}:${detailsError.message}` : 'form'}
                  booking={data}
                  initialError={detailsError}
                  onSaved={(saved) => {
                    onChange(saved)
                    setEditing(false)
                    setDetailsError(null)
                  }}
                  onGone={handleGone}
                />
              ) : (
                <BookingDetailsSummary
                  booking={data}
                  onEdit={() => setEditing(true)}
                  onContinue={() => setStep('payment')}
                />
              )}
            </div>
          )}
          {step === 'payment' && (
            <PaymentMethodPicker
              tongTien={data.tong_tien}
              onChooseCash={() => setStep('confirm-cash')}
              onChooseTransfer={xuLyChonChuyenKhoan}
              transferActive={qrSePay !== null}
              transferLoading={dangTaoQr}
              onBack={() => setStep('details')}
            >
              {loiQr && (
                <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
                  {loiQr}
                </p>
              )}
              {qrSePay && <QrSePayPanel qr={qrSePay} conLaiMs={qrConLaiMs} />}
            </PaymentMethodPicker>
          )}
          {step === 'confirm-cash' && (
            <CashConfirmDialog
              maDon={data.ma_don}
              tongTien={data.tong_tien}
              onConfirmed={onChange}
              onGone={handleGone}
              onFieldError={showFieldError}
              onCancel={() => setStep('payment')}
            />
          )}
          <CancelBookingButton maDon={data.ma_don} onCancelled={() => setCancelled(true)} />
        </>
      )}
    </section>
  )
}

/**
 * Người đặt chỉ hiển thị, không sửa (đã nhập ở bước giữ ghế). Họ tên lấy theo tên đã ghi
 * trên vé lúc giữ ghế nếu backend xác định được, không thì theo hồ sơ `nguoi_dat`.
 */
function BookerInfo({ data }: { data: Booking }) {
  const booker = bookerReference(data)
  return (
    <section aria-label="Người đặt" className="space-y-1">
      <h3 className="font-semibold">Người đặt</h3>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
        <dt className="text-slate-500">Họ tên</dt>
        <dd>{booker.ho_ten}</dd>
        <dt className="text-slate-500">Số điện thoại</dt>
        <dd>{data.nguoi_dat.so_dien_thoai}</dd>
        <dt className="text-slate-500">Email</dt>
        <dd>{data.nguoi_dat.email ?? 'Không có'}</dd>
      </dl>
    </section>
  )
}

/** Lý do biết ngay trên trang (tự hủy, hết giờ) ưu tiên hơn trạng thái tải từ backend. */
function failureReason(data: Booking, cancelled: boolean, timedOut: boolean, gone: boolean): FailureReason | null {
  if (cancelled) return 'TU_HUY'
  if (timedOut) return 'HET_GIO'
  if (data.trang_thai_don === 'HET_HAN' || data.trang_thai_don === 'DA_HUY') return data.trang_thai_don
  // 410 mà không tải lại được đơn: dùng câu trung tính
  if (gone) return 'DA_HUY'
  return null
}
