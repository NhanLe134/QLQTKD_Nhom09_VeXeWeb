import { type FormEvent, useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'

import FormField from '../components/FormField'
import BrandLogo from '../components/BrandLogo'
import { useAuth } from '../hooks/useAuth'

type FieldErrors = Partial<Record<'ten_dang_nhap' | 'mat_khau', string>>

function validate(tenDangNhap: string, matKhau: string): FieldErrors {
  const errors: FieldErrors = {}
  if (!tenDangNhap.trim()) {
    errors.ten_dang_nhap = 'Vui lòng nhập tên đăng nhập'
  }
  if (!matKhau) {
    errors.mat_khau = 'Vui lòng nhập mật khẩu'
  }
  return errors
}

export default function LoginPage() {
  const { user, login } = useAuth()
  const location = useLocation()
  const [tenDangNhap, setTenDangNhap] = useState('')
  const [matKhau, setMatKhau] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Đăng nhập xong (hoặc đã đăng nhập sẵn) thì quay về trang trước đó
  if (user) {
    const from = (location.state as { from?: string } | null)?.from ?? '/'
    return <Navigate to={from} replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const errors = validate(tenDangNhap, matKhau)
    setFieldErrors(errors)
    setFormError('')
    if (Object.keys(errors).length > 0) {
      return
    }

    setSubmitting(true)
    try {
      await login(tenDangNhap.trim(), matKhau)
    } catch (error: unknown) {
      setFormError(error instanceof Error ? error.message : String(error))
      setSubmitting(false)
    }
  }

  return (
    <section className="mx-auto max-w-md space-y-5 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-brand-100 sm:p-8">
      <div className="flex flex-col items-center gap-2 text-center">
        <BrandLogo className="h-28 w-28" />
        <h1 className="text-2xl font-bold text-brand-800">Đăng nhập</h1>
      </div>
      <p className="text-center text-sm text-slate-600">
        Không bắt buộc: bạn vẫn tìm chuyến và đặt vé được khi chưa đăng nhập.
      </p>
      <form noValidate onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="ten_dang_nhap"
          label="Tên đăng nhập"
          autoComplete="username"
          value={tenDangNhap}
          onChange={(e) => setTenDangNhap(e.target.value)}
          error={fieldErrors.ten_dang_nhap}
        />
        <FormField
          id="mat_khau"
          label="Mật khẩu"
          type="password"
          autoComplete="current-password"
          value={matKhau}
          onChange={(e) => setMatKhau(e.target.value)}
          error={fieldErrors.mat_khau}
        />
        {formError && (
          <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
            {formError}
          </p>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-brand-700 px-4 py-2.5 font-semibold text-white shadow-sm hover:bg-brand-800 disabled:opacity-60"
        >
          {submitting ? 'Đang đăng nhập…' : 'Đăng nhập'}
        </button>
      </form>
      <p className="text-center text-sm text-slate-600">
        Chưa có tài khoản?{' '}
        <Link to="/dang-ky" className="font-semibold text-brand-700 underline underline-offset-2 hover:text-brand-800">
          Đăng ký
        </Link>
      </p>
    </section>
  )
}
