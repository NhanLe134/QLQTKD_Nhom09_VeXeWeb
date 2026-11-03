import { type ChangeEvent, type FormEvent, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'

import FormField from '../components/FormField'
import { useAuth } from '../hooks/useAuth'
import { register } from '../services/authService'
import { isValidEmail, isValidPhone, MIN_PASSWORD_LENGTH } from '../utils/validation'

type Fields = {
  ho_ten: string
  so_dien_thoai: string
  email: string
  ten_dang_nhap: string
  mat_khau: string
  nhap_lai_mat_khau: string
}

type FieldErrors = Partial<Record<keyof Fields, string>>

const EMPTY_FIELDS: Fields = {
  ho_ten: '',
  so_dien_thoai: '',
  email: '',
  ten_dang_nhap: '',
  mat_khau: '',
  nhap_lai_mat_khau: '',
}

function validate(fields: Fields): FieldErrors {
  const errors: FieldErrors = {}
  if (!fields.ho_ten.trim()) {
    errors.ho_ten = 'Vui lòng nhập họ tên'
  }
  if (!fields.so_dien_thoai.trim()) {
    errors.so_dien_thoai = 'Vui lòng nhập số điện thoại'
  } else if (!isValidPhone(fields.so_dien_thoai)) {
    errors.so_dien_thoai = 'Số điện thoại gồm 10 chữ số, bắt đầu bằng 0'
  }
  if (fields.email.trim() && !isValidEmail(fields.email)) {
    errors.email = 'Email không hợp lệ'
  }
  if (!fields.ten_dang_nhap.trim()) {
    errors.ten_dang_nhap = 'Vui lòng nhập tên đăng nhập'
  }
  if (fields.mat_khau.length < MIN_PASSWORD_LENGTH) {
    errors.mat_khau = `Mật khẩu tối thiểu ${MIN_PASSWORD_LENGTH} ký tự`
  }
  if (fields.nhap_lai_mat_khau !== fields.mat_khau) {
    errors.nhap_lai_mat_khau = 'Mật khẩu nhập lại không khớp'
  }
  return errors
}

export default function RegisterPage() {
  const { user, login } = useAuth()
  const [fields, setFields] = useState<Fields>(EMPTY_FIELDS)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Đăng ký xong thì đã tự đăng nhập → về trang chủ
  if (user) {
    return <Navigate to="/" replace />
  }

  function update(name: keyof Fields) {
    return (event: ChangeEvent<HTMLInputElement>) =>
      setFields((current) => ({ ...current, [name]: event.target.value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const errors = validate(fields)
    setFieldErrors(errors)
    setFormError('')
    if (Object.keys(errors).length > 0) {
      return
    }

    setSubmitting(true)
    const tenDangNhap = fields.ten_dang_nhap.trim()
    try {
      await register({
        ten_dang_nhap: tenDangNhap,
        mat_khau: fields.mat_khau,
        ho_ten: fields.ho_ten.trim(),
        so_dien_thoai: fields.so_dien_thoai.trim(),
        email: fields.email.trim() || null,
      })
    } catch (error: unknown) {
      setFormError(error instanceof Error ? error.message : String(error))
      setSubmitting(false)
      return
    }

    try {
      await login(tenDangNhap, fields.mat_khau)
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error)
      setFormError(`Đăng ký thành công nhưng chưa đăng nhập được: ${message}`)
      setSubmitting(false)
    }
  }

  return (
    <section className="mx-auto max-w-sm space-y-4">
      <h1 className="text-2xl font-bold">Đăng ký</h1>
      <p className="text-sm text-slate-600">
        Nếu bạn từng đặt vé bằng số điện thoại này, các vé cũ sẽ được gắn vào tài khoản mới.
      </p>
      <form noValidate onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="ho_ten"
          label="Họ tên"
          autoComplete="name"
          value={fields.ho_ten}
          onChange={update('ho_ten')}
          error={fieldErrors.ho_ten}
        />
        <FormField
          id="so_dien_thoai"
          label="Số điện thoại"
          type="tel"
          inputMode="numeric"
          autoComplete="tel"
          value={fields.so_dien_thoai}
          onChange={update('so_dien_thoai')}
          error={fieldErrors.so_dien_thoai}
        />
        <FormField
          id="email"
          label="Email (không bắt buộc)"
          type="email"
          autoComplete="email"
          value={fields.email}
          onChange={update('email')}
          error={fieldErrors.email}
        />
        <FormField
          id="ten_dang_nhap"
          label="Tên đăng nhập"
          autoComplete="username"
          value={fields.ten_dang_nhap}
          onChange={update('ten_dang_nhap')}
          error={fieldErrors.ten_dang_nhap}
        />
        <FormField
          id="mat_khau"
          label="Mật khẩu"
          type="password"
          autoComplete="new-password"
          value={fields.mat_khau}
          onChange={update('mat_khau')}
          error={fieldErrors.mat_khau}
          hint={`Tối thiểu ${MIN_PASSWORD_LENGTH} ký tự`}
        />
        <FormField
          id="nhap_lai_mat_khau"
          label="Nhập lại mật khẩu"
          type="password"
          autoComplete="new-password"
          value={fields.nhap_lai_mat_khau}
          onChange={update('nhap_lai_mat_khau')}
          error={fieldErrors.nhap_lai_mat_khau}
        />
        {formError && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {formError}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-md bg-blue-700 px-4 py-2 font-medium text-white hover:bg-blue-800 disabled:opacity-60"
        >
          {submitting ? 'Đang đăng ký…' : 'Đăng ký'}
        </button>
      </form>
      <p className="text-sm text-slate-600">
        Đã có tài khoản?{' '}
        <Link to="/dang-nhap" className="font-medium text-blue-700 hover:underline">
          Đăng nhập
        </Link>
      </p>
    </section>
  )
}
