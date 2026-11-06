import { type FormEvent, useEffect, useState } from 'react'

import { useAuth } from '../hooks/useAuth'
import { getMe, type MeResponse } from '../services/authService'
import type { NguoiDatInput } from '../services/bookingService'
import { isValidEmail, isValidPhone } from '../utils/validation'
import FormField from './FormField'

type Props = {
  /** null: khách đã đăng nhập, backend dùng hồ sơ tài khoản */
  onSubmit: (nguoiDat: NguoiDatInput | null) => void
  onCancel: () => void
  submitting: boolean
}

type FieldErrors = Partial<Record<'ho_ten' | 'so_dien_thoai' | 'email', string>>

function validate(hoTen: string, soDienThoai: string, email: string): FieldErrors {
  const errors: FieldErrors = {}
  if (!hoTen.trim()) {
    errors.ho_ten = 'Vui lòng nhập họ tên'
  }
  if (!isValidPhone(soDienThoai)) {
    errors.so_dien_thoai = 'Số điện thoại gồm 10 chữ số, bắt đầu bằng 0'
  }
  if (!email.trim()) {
    errors.email = 'Vui lòng nhập email'
  } else if (!isValidEmail(email)) {
    errors.email = 'Email không hợp lệ'
  }
  return errors
}

function Actions({ submitting, onCancel }: Pick<Props, 'submitting' | 'onCancel'>) {
  return (
    <div className="flex items-center gap-3 pt-2">
      <button
        type="submit"
        disabled={submitting}
        className="flex-1 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50"
      >
        {submitting ? 'Đang giữ ghế…' : 'Xác nhận giữ ghế'}
      </button>
      <button
        type="button"
        onClick={onCancel}
        disabled={submitting}
        className="rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50"
      >
        Hủy
      </button>
    </div>
  )
}

function AccountBooker({ onSubmit, onCancel, submitting }: Props) {
  const [me, setMe] = useState<MeResponse | null>(null)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    let cancelled = false
    getMe()
      .then((data) => {
        if (!cancelled) setMe(data)
      })
      .catch((error: unknown) => {
        if (!cancelled) setLoadError(error instanceof Error ? error.message : String(error))
      })
    return () => {
      cancelled = true
    }
  }, [])

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSubmit(null)
  }

  const profile = me?.khach_hang
  return (
    <form aria-label="Thông tin người đặt" onSubmit={handleSubmit} className="space-y-4">
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
        Vé sẽ được đặt theo hồ sơ tài khoản:
      </p>
      {loadError && (
        <p role="alert" className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-700">
          {loadError}
        </p>
      )}
      {!me && !loadError && (
        <p role="status" className="text-sm text-slate-500">
          Đang tải thông tin tài khoản…
        </p>
      )}
      {me && (
        <div className="rounded-2xl border border-slate-200/80 bg-slate-50/70 p-4">
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">Họ tên</dt>
            <dd className="font-semibold text-slate-800">{profile?.ho_ten ?? me.ten_dang_nhap}</dd>
            <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">Số điện thoại</dt>
            <dd className="font-semibold text-slate-800">{profile?.so_dien_thoai ?? me.so_dien_thoai}</dd>
            <dt className="text-xs font-bold uppercase tracking-wider text-slate-400">Email</dt>
            <dd className="font-semibold text-slate-800">{profile?.email ?? 'Không có'}</dd>
          </dl>
        </div>
      )}
      {me && !profile?.email && (
        <p role="note" className="text-xs font-medium text-amber-700">
          Tài khoản chưa có email nên vé sẽ không được gửi qua email.
        </p>
      )}
      <Actions submitting={submitting} onCancel={onCancel} />
    </form>
  )
}

function GuestBooker({ onSubmit, onCancel, submitting }: Props) {
  const [hoTen, setHoTen] = useState('')
  const [soDienThoai, setSoDienThoai] = useState('')
  const [email, setEmail] = useState('')
  const [errors, setErrors] = useState<FieldErrors>({})

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = validate(hoTen, soDienThoai, email)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) {
      return
    }
    onSubmit({
      ho_ten: hoTen.trim(),
      so_dien_thoai: soDienThoai.trim(),
      email: email.trim(),
    })
  }

  return (
    <form aria-label="Thông tin người đặt" noValidate onSubmit={handleSubmit} className="space-y-3.5">
      <FormField
        id="nguoi-dat-ho-ten"
        label="Họ tên"
        autoComplete="name"
        value={hoTen}
        onChange={(event) => setHoTen(event.target.value)}
        error={errors.ho_ten}
      />
      <FormField
        id="nguoi-dat-so-dien-thoai"
        label="Số điện thoại"
        type="tel"
        inputMode="numeric"
        autoComplete="tel"
        value={soDienThoai}
        onChange={(event) => setSoDienThoai(event.target.value)}
        error={errors.so_dien_thoai}
      />
      <FormField
        id="nguoi-dat-email"
        label="Email"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={errors.email}
        hint="Vé điện tử sẽ được gửi về email này"
      />
      <Actions submitting={submitting} onCancel={onCancel} />
    </form>
  )
}

export default function BookerForm(props: Props) {
  const { user } = useAuth()
  return user ? <AccountBooker {...props} /> : <GuestBooker {...props} />
}
