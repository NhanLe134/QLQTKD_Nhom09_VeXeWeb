import { type FormEvent, useState } from 'react'

import type { Locations, TripSearchQuery } from '../services/tripService'
import { todayInVietnam } from '../utils/format'
import { SearchIcon, SwapIcon } from './icons'

type Props = {
  /** null khi đang tải danh sách điểm */
  locations: Locations | null
  initialValues: TripSearchQuery
  onSearch: (query: TripSearchQuery) => void
}

type FieldErrors = Partial<Record<keyof TripSearchQuery, string>>

// Kiểm tra sớm phía client; backend vẫn kiểm tra lại (BR-BUS-10)
function validate(values: TripSearchQuery, today: string): FieldErrors {
  const errors: FieldErrors = {}
  if (!values.diemDi) {
    errors.diemDi = 'Vui lòng chọn điểm đi'
  }
  if (!values.diemDen) {
    errors.diemDen = 'Vui lòng chọn điểm đến'
  } else if (values.diemDen === values.diemDi) {
    errors.diemDen = 'Điểm đến phải khác điểm đi'
  }
  if (!values.ngay) {
    errors.ngay = 'Vui lòng chọn ngày đi'
  } else if (values.ngay < today) {
    errors.ngay = 'Không chọn được ngày trong quá khứ'
  }
  return errors
}

// Giữ giá trị đang có trên URL trong danh sách để ô chọn không tự nhảy sang lựa chọn khác
function withCurrent(options: string[], current: string): string[] {
  return current && !options.includes(current) ? [...options, current] : options
}

type SelectProps = {
  id: string
  label: string
  placeholder: string
  options: string[]
  value: string
  disabled: boolean
  error?: string
  onChange: (value: string) => void
}

function SelectField({ id, label, placeholder, options, value, disabled, error, onChange }: SelectProps) {
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-xs font-semibold text-slate-700">
        {label}
      </label>
      <select
        id={id}
        value={value}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        onChange={(event) => onChange(event.target.value)}
        className={`w-full rounded-lg border bg-white px-2.5 py-1.5 text-xs sm:text-sm font-medium text-slate-900 outline-none transition-all focus:border-brand-500 focus:ring-2 focus:ring-brand-100 disabled:bg-slate-50 ${
          error ? 'border-rose-400 bg-rose-50/20' : 'border-slate-300 hover:border-slate-400'
        }`}
      >
        <option value="">{placeholder}</option>
        {withCurrent(options, value).map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
      {error && (
        <p id={`${id}-error`} className="text-[11px] font-medium text-rose-600">
          {error}
        </p>
      )}
    </div>
  )
}

export default function TripSearchForm({ locations, initialValues, onSearch }: Props) {
  const [values, setValues] = useState<TripSearchQuery>(initialValues)
  const [errors, setErrors] = useState<FieldErrors>({})
  const today = todayInVietnam()

  function update(name: keyof TripSearchQuery) {
    return (value: string) => setValues((current) => ({ ...current, [name]: value }))
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors = validate(values, today)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length === 0) {
      onSearch(values)
    }
  }

  const loading = locations === null
  return (
    <form
      noValidate
      onSubmit={handleSubmit}
      aria-label="Tìm chuyến"
      className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs sm:p-5"
    >
      <div className="grid gap-3 sm:grid-cols-[1fr_auto_1fr_160px_auto] sm:items-end">
        <SelectField
          id="diem_di"
          label="Điểm đi"
          placeholder={loading ? 'Đang tải…' : 'Chọn điểm đi'}
          options={locations?.diem_di ?? []}
          value={values.diemDi}
          disabled={loading}
          error={errors.diemDi}
          onChange={update('diemDi')}
        />

        {/* Biểu tượng chuyển hướng nhỏ gọn */}
        <div aria-hidden="true" className="hidden items-center justify-center pb-2 text-brand-500 sm:flex">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-50 text-brand-600 ring-1 ring-brand-100">
            <SwapIcon className="h-3.5 w-3.5" />
          </div>
        </div>

        <SelectField
          id="diem_den"
          label="Điểm đến"
          placeholder={loading ? 'Đang tải…' : 'Chọn điểm đến'}
          options={locations?.diem_den ?? []}
          value={values.diemDen}
          disabled={loading}
          error={errors.diemDen}
          onChange={update('diemDen')}
        />

        <div className="space-y-1">
          <label htmlFor="ngay" className="block text-xs font-semibold text-slate-700">
            Ngày đi
          </label>
          <input
            id="ngay"
            type="date"
            min={today}
            value={values.ngay}
            aria-invalid={errors.ngay ? true : undefined}
            aria-describedby={errors.ngay ? 'ngay-error' : undefined}
            onChange={(event) => update('ngay')(event.target.value)}
            className={`w-full rounded-lg border bg-white px-2.5 py-1.5 text-xs sm:text-sm font-medium text-slate-900 outline-none transition-all focus:border-brand-500 focus:ring-2 focus:ring-brand-100 ${
              errors.ngay ? 'border-rose-400 bg-rose-50/20' : 'border-slate-300 hover:border-slate-400'
            }`}
          />
          {errors.ngay && (
            <p id="ngay-error" className="text-[11px] font-medium text-rose-600">
              {errors.ngay}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="inline-flex h-[38px] w-full items-center justify-center gap-1.5 rounded-lg bg-brand-600 px-4 text-xs sm:text-sm font-bold text-white shadow-2xs transition-all hover:bg-brand-700 active:scale-[0.98] disabled:opacity-50 sm:w-auto"
        >
          <SearchIcon className="h-3.5 w-3.5" />
          <span>Tìm chuyến</span>
        </button>
      </div>
    </form>
  )
}
