import { type FormEvent, useState } from 'react'

import type { Locations, TripSearchQuery } from '../services/tripService'
import { todayInVietnam } from '../utils/format'
import { PinIcon, SearchIcon, SwapIcon } from './icons'

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
      <label htmlFor={id} className="block text-sm font-semibold text-brand-800">
        {label}
      </label>
      <select
        id={id}
        value={value}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        onChange={(event) => onChange(event.target.value)}
        className={`w-full rounded-lg border bg-white px-3 py-2 text-base outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-slate-100 ${
          error ? 'border-red-500' : 'border-slate-300'
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
        <p id={`${id}-error`} className="text-sm text-red-600">
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
      className="grid gap-4 rounded-2xl bg-white p-5 shadow-md ring-1 ring-brand-100 sm:grid-cols-[1fr_auto_1fr] sm:gap-x-6"
    >
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
      {/* Chỉ để trang trí: đường nối điểm đi → điểm đến */}
      <div aria-hidden="true" className="hidden items-center gap-1 self-start pt-9 text-brand-500 sm:flex">
        <span className="h-2 w-2 rounded-full bg-green-500" />
        <span className="w-6 border-t-2 border-dashed border-brand-300" />
        <SwapIcon className="h-5 w-5" />
        <span className="w-6 border-t-2 border-dashed border-brand-300" />
        <PinIcon className="h-4 w-4 text-red-500" />
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
      <div className="space-y-1 sm:col-start-1">
        <label htmlFor="ngay" className="block text-sm font-semibold text-brand-800">
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
          className={`w-full rounded-lg border px-3 py-2 text-base outline-none focus:ring-2 focus:ring-brand-400 ${
            errors.ngay ? 'border-red-500' : 'border-slate-300'
          }`}
        />
        {errors.ngay && (
          <p id="ngay-error" className="text-sm text-red-600">
            {errors.ngay}
          </p>
        )}
      </div>
      <button
        type="submit"
        disabled={loading}
        className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-700 px-5 py-2.5 font-semibold text-white shadow-sm hover:bg-brand-800 disabled:opacity-60 sm:col-start-3 sm:mt-7 sm:w-auto sm:self-start sm:justify-self-end"
      >
        <SearchIcon className="h-4 w-4" />
        Tìm chuyến
      </button>
    </form>
  )
}
