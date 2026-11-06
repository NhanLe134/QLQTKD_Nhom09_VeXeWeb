import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import BookingDetailsForm from '../components/BookingDetailsForm'
import BookingDetailsSummary from '../components/BookingDetailsSummary'
import BookingFailed, { type FailureReason } from '../components/BookingFailed'
import BookingSuccess from '../components/BookingSuccess'
import CancelReceiptView from '../components/CancelReceipt'
import CancelBookingButton from '../components/CancelBookingButton'
import CashConfirmDialog from '../components/CashConfirmDialog'
import HoldCountdown from '../components/HoldCountdown'
import PaymentMethodPicker from '../components/PaymentMethodPicker'
import QrSePayPanel from '../components/QrSePayPanel'
import { useCountdown } from '../hooks/useCountdown'
import { type Booking, type CancelReceipt, taoQrSePay, type QrSePay, getBooking } from '../services/bookingService'
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
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Đặt vé</h1>
        {booking.state === 'loading' ? (
          <div className="flex items-center justify-center py-8">
            <p role="status" className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-xs font-medium text-slate-600 shadow-2xs border border-slate-200/80">
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
              Đang tải đơn…
            </p>
          </div>
        ) : (
          <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
            {booking.message}
          </p>
        )}
      </section>
    )
  }

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

function BookingDetail({ data, clockOffsetMs, onChange }: DetailProps) {
  const [cancelled, setCancelled] = useState(false)
  const [gone, setGone] = useState(false)
  const [editing, setEditing] = useState(!data.da_nhap_thong_tin)
  const [step, setStep] = useState<Step>('details')
  const [detailsError, setDetailsError] = useState<FieldError | null>(null)
  const [cancelReceipt, setCancelReceipt] = useState<CancelReceipt | null>(null)
  const dangGiu = data.trang_thai_don === 'DANG_GIU'
  const remainingMs = useCountdown(dangGiu ? data.han_giu_cho : null, clockOffsetMs)
  const holding = remainingMs !== null && remainingMs > 0
  const failure = failureReason(data, cancelled, dangGiu && !holding, gone)
  const { chuyen } = data
  const heldTickets = data.ve.filter((ve) => ve.trang_thai_ve !== 'DA_HUY')

  const [qrSePay, setQrSePay] = useState<QrSePay | null>(null)
  const [hanQr, setSepayDeadline] = useState<string | null>(null)
  const [dangTaoQr, setSepayLoading] = useState(false)
  const [loiQr, setSepayError] = useState<string | null>(null)
  const qrConLaiMs = useCountdown(qrSePay ? hanQr : null, 0)

  function xuLyChonChuyenKhoan() {
    if (qrSePay) {
      setSepayDeadline(new Date(Date.now() + qrSePay.thoi_gian_cho_giay * 1000).toISOString())
      return
    }
    setSepayLoading(true)
    setSepayError(null)
    taoQrSePay(data.ma_don)
      .then((qr) => {
        setQrSePay(qr)
        setSepayDeadline(new Date(Date.now() + qr.thoi_gian_cho_giay * 1000).toISOString())
        getBooking(data.ma_don).then(onChange).catch(() => {})
      })
      .catch((error: unknown) => {
        setSepayError(error instanceof ApiError ? error.detail : 'Không tạo được mã QR, vui lòng thử lại.')
      })
      .finally(() => setSepayLoading(false))
  }

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

  function handleGone() {
    getBooking(data.ma_don)
      .then(onChange)
      .catch(() => setGone(true))
  }

  // Biên lai hủy vé đứng trước: hủy hết vé thì đơn thành DA_HUY nhưng vẫn phải xem được biên lai
  if (cancelReceipt) {
    return (
      <CancelReceiptView
        receipt={cancelReceipt}
        onDone={data.trang_thai_don === 'DA_XAC_NHAN' ? () => setCancelReceipt(null) : undefined}
      />
    )
  }

  if (failure) {
    return <BookingFailed reason={failure} maDon={data.ma_don} chuyenXeId={chuyen.chuyen_xe_id} />
  }

  if (data.trang_thai_don === 'DA_XAC_NHAN') {
    return (
      <BookingSuccess
        booking={data}
        onCancelled={(receipt) => {
          setCancelReceipt(receipt)
          // Đọc lại đơn: còn vé đã xác nhận thì cho quay lại xem
          getBooking(data.ma_don).then(onChange).catch(() => {})
        }}
      />
    )
  }

  function showFieldError(field: string, message: string) {
    setDetailsError({ field, message })
    setEditing(true)
    setStep('details')
  }

  return (
    <section className="space-y-4">
      {/* Header trang đặt vé */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">Đặt vé</h1>
          <p className="text-xs text-slate-500">Hoàn tất thông tin hành khách và thanh toán để nhận vé.</p>
        </div>
        <p className="text-xs font-semibold text-slate-500">
          Mã đơn: <span className="font-mono font-bold text-slate-900">{data.ma_don}</span>
        </p>
      </div>

      {dangGiu && <HoldCountdown remainingMs={remainingMs} />}

      <div className="grid gap-4 md:grid-cols-[1fr_320px] items-start">
        {/* Cột trái: Form & Quy trình thanh toán */}
        <div className="space-y-4">
          {holding && (
            <>
              {step === 'details' && (
                <div className="space-y-3.5 rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs">
                  <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Thông tin hành khách</h2>
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
                    <p role="alert" className="rounded-xl bg-rose-50 p-2.5 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/60">
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

              <div className="pt-1">
                <CancelBookingButton maDon={data.ma_don} onCancelled={() => setCancelled(true)} />
              </div>
            </>
          )}
        </div>

        {/* Cột phải: Tóm tắt chuyến xe & Ghế đã giữ */}
        <div className="space-y-3">
          <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs space-y-1">
            <p className="text-sm font-bold text-slate-900">{chuyen.ten_tuyen}</p>
            <p className="text-xs text-slate-600">
              {formatTime(chuyen.gio_di)} ngày {formatDate(chuyen.ngay_khoi_hanh)}
            </p>
            <p className="text-[11px] text-slate-500">{formatVehicleType(chuyen.ten_loai_xe, chuyen.so_cho)}</p>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-2xs space-y-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Ghế đã giữ</h2>
            <ul aria-label="Ghế đã giữ" className="divide-y divide-slate-100 text-xs">
              {heldTickets.map((ve) => (
                <li key={ve.ve_id} className="flex justify-between py-1 text-slate-700">
                  <span className="font-medium">Ghế {ve.so_ghe}</span>
                  <span className="font-semibold text-slate-900">{formatCurrency(ve.gia_ve)}</span>
                </li>
              ))}
            </ul>
            <div className="flex justify-between border-t border-slate-200 pt-2 text-xs font-bold text-slate-800">
              <span>Tổng tiền</span>
              <span data-testid="tong-tien" className="text-base font-black text-amber-600">
                {formatCurrency(data.tong_tien)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function BookerInfo({ data }: { data: Booking }) {
  const booker = bookerReference(data)
  return (
    <section aria-label="Người đặt" className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-3 space-y-1.5">
      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Người đặt</h3>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-xs">
        <dt className="text-slate-400 font-medium">Họ tên</dt>
        <dd className="font-semibold text-slate-800">{booker.ho_ten}</dd>
        <dt className="text-slate-400 font-medium">Số điện thoại</dt>
        <dd className="font-semibold text-slate-800">{data.nguoi_dat.so_dien_thoai}</dd>
        <dt className="text-slate-400 font-medium">Email</dt>
        <dd className="font-semibold text-slate-800">{data.nguoi_dat.email ?? 'Không có'}</dd>
      </dl>
    </section>
  )
}

function failureReason(data: Booking, cancelled: boolean, timedOut: boolean, gone: boolean): FailureReason | null {
  if (cancelled) return 'TU_HUY'
  if (timedOut) return 'HET_GIO'
  if (data.trang_thai_don === 'HET_HAN' || data.trang_thai_don === 'DA_HUY') return data.trang_thai_don
  if (gone) return 'DA_HUY'
  return null
}
