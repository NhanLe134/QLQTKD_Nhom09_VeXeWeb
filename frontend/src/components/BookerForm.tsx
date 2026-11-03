import { type FormEvent, useEffect, useState } from 'react'

import { useAuth } from '../hooks/useAuth'
import { getMe, type MeResponse } from '../services/authService'
import type { NguoiDat } from '../services/bookingService'
import { isValidEmail, isValidPhone } from '../utils/validation'
import FormField from './FormField'

type Props = {
  /** null: khách đã đăng nhập, backend dùng hồ sơ tài khoản */
  onSubmit: (nguoiDat: NguoiDat | null) => void
  onCancel: () => void
  submitting: boolean
}

type FieldErrors = Partial<Record<'ho_ten' | 'so_dien_thoai' | 'email', string>>

// Kiểm tra phía client chỉ để báo lỗi sớm; backend vẫn kiểm tra lại (BR-BUS-20)
function validate(hoTen: string, soDienThoai: string, email: string): FieldErrors {
  const errors: FieldErrors = {}
  if (!hoTen.trim()) {
    errors.ho_ten = 'Vui lòng nhập họ tên'
  }
  if (!isValidPhone(soDienThoai)) {
    errors.so_dien_thoai = 'Số điện thoại gồm 10 chữ số, bắt đầu bằng 0'
  }
  if (email.trim() && !isValidEmail(email)) {
    errors.email = 'Email không hợp lệ'
  }
  return errors
}

function Actions({ submitting, onCancel }: Pick<Props, 'submitting' | 'onCancel'>) {
  return (
    <div className="flex gap-2">
      <button
        type="submit"
        disabled={submitting}
        className="flex-1 rounded-md bg-blue-700 px-4 py-2 font-medium text-white hover:bg-blue-800 disabled:bg-slate-400"
      >
        {submitting ? 'Đang giữ ghế…' : 'Xác nhận giữ ghế'}
      </button>
      <button
        type="button"
        onClick={onCancel}
        disabled={submitting}
        className="rounded-md border border-slate-300 px-4 py-2 font-medium text-slate-700"
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
    <form aria-label="Thông tin người đặt" onSubmit={handleSubmit} className="space-y-3">
      <p className="text-sm text-slate-600">Vé được đặt theo hồ sơ tài khoản của bạn.</p>
      {loadError && (
        <p role="alert" className="text-sm text-red-600">
          {loadError}
        </p>
      )}
      {!me && !loadError && <p role="status">Đang tải thông tin tài khoản…</p>}
      {me && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
          <dt className="text-slate-500">Họ tên</dt>
          <dd>{profile?.ho_ten ?? me.ten_dang_nhap}</dd>
          <dt className="text-slate-500">Số điện thoại</dt>
          <dd>{profile?.so_dien_thoai ?? me.so_dien_thoai}</dd>
          <dt className="text-slate-500">Email</dt>
          <dd>{profile?.email ?? 'Không có'}</dd>
        </dl>
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
      email: email.trim() || null,
    })
  }

  return (
    <form aria-label="Thông tin người đặt" noValidate onSubmit={handleSubmit} className="space-y-3">
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
        label="Email (không bắt buộc)"
        type="email"
        autoComplete="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
        error={errors.email}
      />
      <Actions submitting={submitting} onCancel={onCancel} />
    </form>
  )
}

/** Người đặt (BR-BUS-20): khách vãng lai nhập, khách đã đăng nhập chỉ xác nhận. */
export default function BookerForm(props: Props) {
  const { user } = useAuth()
  return user ? <AccountBooker {...props} /> : <GuestBooker {...props} />
}
