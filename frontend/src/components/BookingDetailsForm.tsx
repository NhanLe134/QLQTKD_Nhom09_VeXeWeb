import { type FormEvent, useState } from 'react'

import { ApiError } from '../services/apiClient'
import {
  type BookerAtHold,
  type Booking,
  type BookingDetailsRequest,
  type PassengerInput,
  saveBookingDetails,
  type Ticket,
} from '../services/bookingService'
import { bookerReference } from '../utils/booker'
import { isPointTooLong, isValidPhone, MAX_PASSENGER_NAME_LENGTH, MAX_POINT_LENGTH } from '../utils/validation'
import FormField from './FormField'

type Props = {
  booking: Booking
  /** Lưu thành công: chi tiết đơn backend trả về */
  onSaved: (booking: Booking) => void
  /** Backend trả 410: đơn đã hết hạn giữ hoặc đã hủy */
  onGone: () => void
  /** Lỗi kèm tên trường từ bước khác (ví dụ xác nhận thanh toán), hiện ngay dưới ô đó */
  initialError?: { field: string; message: string } | null
}

type PassengerState = {
  /** "Giống người đặt": vé không được gửi trong hanh_khach, backend giữ nguyên vé */
  same: boolean
  ho_ten: string
  so_dien_thoai: string
}

type PointState = { khu_vuc: string; dia_chi: string }

/** Khóa lỗi: `ve:<ve_id>.ho_ten`, `ve:<ve_id>.so_dien_thoai`, `diem_don.khu_vuc`, `diem_tra.dia_chi`… */
type Errors = Record<string, string>

const PHONE_MESSAGE = 'Số điện thoại gồm 10 chữ số, bắt đầu bằng 0'

function ticketValues(ticket: Ticket): BookerAtHold {
  return { ho_ten: ticket.ho_ten ?? '', so_dien_thoai: ticket.so_dien_thoai ?? '' }
}

function sameValues(a: BookerAtHold, b: BookerAtHold): boolean {
  return a.ho_ten === b.ho_ten && a.so_dien_thoai === b.so_dien_thoai
}

function heldTickets(booking: Booking): Ticket[] {
  return booking.ve.filter((ve) => ve.trang_thai_ve === 'GIU_CHO')
}

function initialPassengers(booking: Booking): Record<string, PassengerState> {
  const reference = bookerReference(booking)
  return Object.fromEntries(
    heldTickets(booking).map((ticket) => {
      const values = ticketValues(ticket)
      // Chưa lưu lần nào: mọi ghế mặc định giống người đặt (BR-BUS-21)
      const same = !booking.da_nhap_thong_tin || sameValues(values, reference)
      return [ticket.ve_id, { same, ...values }]
    }),
  )
}

function initialPoint(saved: Booking['diem_don'], options: string[], fallback: string): PointState {
  const khuVuc = saved && options.includes(saved.khu_vuc) ? saved.khu_vuc : fallback
  return { khu_vuc: khuVuc, dia_chi: saved && khuVuc === saved.khu_vuc ? (saved.dia_chi ?? '') : '' }
}

function tickedValues(booking: Booking, ticket: Ticket): { values: BookerAtHold; send: boolean } {
  const current = ticketValues(ticket)
  const atHold = booking.nguoi_dat_luc_giu
  if (atHold === null || sameValues(current, bookerReference(booking))) {
    return { values: current, send: false }
  }
  return { values: atHold, send: true }
}

/** Đổi `hanh_khach[i].x` của backend thành khóa lỗi theo vé đã gửi ở vị trí i. */
function errorKey(field: string, sentIds: string[]): string {
  const match = /^hanh_khach\[(\d+)\]\.(\w+)$/.exec(field)
  if (!match) return field
  const veId = sentIds[Number(match[1])]
  return veId ? `ve:${veId}.${match[2]}` : field
}

export default function BookingDetailsForm({ booking, onSaved, onGone, initialError = null }: Props) {
  const stops = booking.diem_dung
  // Ô đón không có điểm đến, ô trả không có điểm đi (BR-BUS-23)
  const pickupOptions = stops.slice(0, -1)
  const dropoffOptions = stops.slice(1)
  const tickets = heldTickets(booking)

  const [passengers, setPassengers] = useState(() => initialPassengers(booking))
  // Điền sẵn: đón = điểm đi, trả = điểm đến (BR-BUS-22, US-BUS-03 AC3)
  const [pickup, setPickup] = useState(() =>
    initialPoint(booking.diem_don, pickupOptions, pickupOptions[0] ?? ''),
  )
  const [dropoff, setDropoff] = useState(() =>
    initialPoint(booking.diem_tra, dropoffOptions, dropoffOptions[dropoffOptions.length - 1] ?? ''),
  )
  const [errors, setErrors] = useState<Errors>(() =>
    initialError ? { [errorKey(initialError.field, [])]: initialError.message } : {},
  )
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function updatePassenger(veId: string, change: Partial<PassengerState>) {
    setPassengers((current) => ({ ...current, [veId]: { ...current[veId], ...change } }))
  }

  function buildRequest(): BookingDetailsRequest {
    const hanhKhach: PassengerInput[] = []
    for (const ticket of tickets) {
      const state = passengers[ticket.ve_id]
      if (state.same) {
        const { values, send } = tickedValues(booking, ticket)
        if (send) hanhKhach.push({ ve_id: ticket.ve_id, ...values })
      } else {
        hanhKhach.push({ ve_id: ticket.ve_id, ho_ten: state.ho_ten.trim(), so_dien_thoai: state.so_dien_thoai.trim() })
      }
    }
    return {
      hanh_khach: hanhKhach,
      diem_don: { khu_vuc: pickup.khu_vuc, dia_chi: pickup.dia_chi.trim() || null },
      diem_tra: { khu_vuc: dropoff.khu_vuc, dia_chi: dropoff.dia_chi.trim() || null },
    }
  }

  // Kiểm tra phía client chỉ để báo sớm; backend vẫn kiểm tra lại
  function validate(): Errors {
    const next: Errors = {}
    for (const ticket of tickets) {
      const state = passengers[ticket.ve_id]
      if (state.same) continue
      const hoTen = state.ho_ten.trim()
      if (!hoTen) next[`ve:${ticket.ve_id}.ho_ten`] = 'Vui lòng nhập họ tên'
      else if (hoTen.length > MAX_PASSENGER_NAME_LENGTH) {
        next[`ve:${ticket.ve_id}.ho_ten`] = `Họ tên tối đa ${MAX_PASSENGER_NAME_LENGTH} ký tự`
      }
      if (!isValidPhone(state.so_dien_thoai)) next[`ve:${ticket.ve_id}.so_dien_thoai`] = PHONE_MESSAGE
    }
    if (stops.indexOf(pickup.khu_vuc) >= stops.indexOf(dropoff.khu_vuc)) {
      next['diem_don.khu_vuc'] = 'Điểm đón phải trước điểm trả'
    }
    if (isPointTooLong(pickup.khu_vuc, pickup.dia_chi)) {
      next['diem_don.dia_chi'] = `Điểm đón và địa chỉ tối đa ${MAX_POINT_LENGTH} ký tự`
    }
    if (isPointTooLong(dropoff.khu_vuc, dropoff.dia_chi)) {
      next['diem_tra.dia_chi'] = `Điểm trả và địa chỉ tối đa ${MAX_POINT_LENGTH} ký tự`
    }
    return next
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError('')
    const nextErrors = validate()
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    const request = buildRequest()
    setSubmitting(true)
    try {
      onSaved(await saveBookingDetails(booking.ma_don, request))
    } catch (error: unknown) {
      setSubmitting(false)
      if (error instanceof ApiError && error.status === 410) {
        onGone()
        return
      }
      const message = error instanceof Error ? error.message : String(error)
      if (error instanceof ApiError && error.field) {
        setErrors({ [errorKey(error.field, request.hanh_khach.map((p) => p.ve_id))]: message })
      } else {
        setFormError(message)
      }
    }
  }

  return (
    <form aria-label="Thông tin hành khách" noValidate onSubmit={handleSubmit} className="space-y-4">
      <fieldset className="space-y-3">
        <legend className="text-xs font-bold uppercase tracking-wider text-slate-700">Hành khách</legend>
        {tickets.map((ticket) => {
          const state = passengers[ticket.ve_id]
          const shown = state.same ? tickedValues(booking, ticket).values : state
          const prefix = `ve-${ticket.ve_id}`
          return (
            <div
              key={ticket.ve_id}
              role="group"
              aria-label={`Ghế ${ticket.so_ghe}`}
              className="space-y-2.5 rounded-xl border border-slate-200/90 bg-white p-3.5 shadow-2xs"
            >
              <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2">
                <span className="rounded-md bg-brand-50 px-2 py-0.5 text-xs font-bold text-brand-700 ring-1 ring-brand-200/60">
                  Ghế {ticket.so_ghe}
                </span>
                <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={state.same}
                    onChange={(event) => updatePassenger(ticket.ve_id, { same: event.target.checked })}
                    className="h-3.5 w-3.5 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  />
                  <span>Giống người đặt</span>
                </label>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <FormField
                  id={`${prefix}-ho-ten`}
                  label="Họ tên"
                  autoComplete="off"
                  value={shown.ho_ten}
                  disabled={state.same}
                  onChange={(event) => updatePassenger(ticket.ve_id, { ho_ten: event.target.value })}
                  error={errors[`ve:${ticket.ve_id}.ho_ten`]}
                />
                <FormField
                  id={`${prefix}-so-dien-thoai`}
                  label="Số điện thoại"
                  type="tel"
                  inputMode="numeric"
                  autoComplete="off"
                  value={shown.so_dien_thoai}
                  disabled={state.same}
                  onChange={(event) => updatePassenger(ticket.ve_id, { so_dien_thoai: event.target.value })}
                  error={errors[`ve:${ticket.ve_id}.so_dien_thoai`]}
                />
              </div>
              {errors[`ve:${ticket.ve_id}.ve_id`] && (
                <p className="text-[11px] font-semibold text-rose-600">{errors[`ve:${ticket.ve_id}.ve_id`]}</p>
              )}
            </div>
          )
        })}
      </fieldset>

      <fieldset className="space-y-3">
        <legend className="text-xs font-bold uppercase tracking-wider text-slate-700">Điểm đón/trả</legend>
        <PointFields
          id="diem-don"
          field="diem_don"
          label="Điểm đón"
          options={pickupOptions}
          value={pickup}
          onChange={setPickup}
          errors={errors}
        />
        <PointFields
          id="diem-tra"
          field="diem_tra"
          label="Điểm trả"
          options={dropoffOptions}
          value={dropoff}
          onChange={setDropoff}
          errors={errors}
        />
      </fieldset>

      {formError && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700 ring-1 ring-rose-200/70">
          {formError}
        </p>
      )}
      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-xl bg-brand-600 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98] disabled:bg-slate-300"
      >
        {submitting ? 'Đang lưu…' : 'Lưu thông tin'}
      </button>
    </form>
  )
}

type PointFieldsProps = {
  id: string
  field: 'diem_don' | 'diem_tra'
  label: string
  options: string[]
  value: PointState
  onChange: (value: PointState) => void
  errors: Errors
}

function PointFields({ id, field, label, options, value, onChange, errors }: PointFieldsProps) {
  const areaError = errors[`${field}.khu_vuc`]
  return (
    <div className="space-y-2 rounded-xl border border-slate-200/90 bg-white p-3.5 shadow-2xs">
      <div className="space-y-1">
        <label htmlFor={`${id}-khu-vuc`} className="block text-xs font-bold uppercase tracking-wider text-slate-700">
          {label}
        </label>
        <select
          id={`${id}-khu-vuc`}
          value={value.khu_vuc}
          onChange={(event) => onChange({ ...value, khu_vuc: event.target.value })}
          aria-invalid={areaError ? true : undefined}
          aria-describedby={areaError ? `${id}-khu-vuc-error` : undefined}
          className={`w-full rounded-lg border bg-white px-2.5 py-1.5 text-xs sm:text-sm font-medium text-slate-900 outline-none transition-all focus:border-brand-500 focus:ring-2 focus:ring-brand-100 ${
            areaError ? 'border-rose-400 bg-rose-50/20' : 'border-slate-300 hover:border-slate-400'
          }`}
        >
          {options.map((stop) => (
            <option key={stop} value={stop}>
              {stop}
            </option>
          ))}
        </select>
        {areaError && (
          <p id={`${id}-khu-vuc-error`} className="text-[11px] font-medium text-rose-600">
            {areaError}
          </p>
        )}
      </div>
      <FormField
        id={`${id}-dia-chi`}
        label="Địa chỉ cụ thể (không bắt buộc)"
        autoComplete="off"
        value={value.dia_chi}
        onChange={(event) => onChange({ ...value, dia_chi: event.target.value })}
        error={errors[`${field}.dia_chi`]}
      />
    </div>
  )
}
