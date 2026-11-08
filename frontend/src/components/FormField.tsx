import type { InputHTMLAttributes } from 'react'

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, 'id'> & {
  id: string
  label: string
  error?: string
  hint?: string
}

export default function FormField({ id, label, error, hint, ...inputProps }: Props) {
  const describedBy = error ? `${id}-error` : hint ? `${id}-hint` : undefined
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-xs font-bold uppercase tracking-wider text-slate-700">
        {label}
      </label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`w-full rounded-xl border bg-slate-50/60 px-3.5 py-2.5 text-sm font-medium text-slate-900 outline-none transition-all focus:border-brand-500 focus:bg-white focus:ring-3 focus:ring-brand-100 disabled:bg-slate-100 ${
          error ? 'border-rose-400 bg-rose-50/30' : 'border-slate-300/80 hover:border-slate-400'
        }`}
        {...inputProps}
      />
      {error ? (
        <p id={`${id}-error`} className="text-xs font-semibold text-rose-600">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-xs text-slate-500">
          {hint}
        </p>
      ) : null}
    </div>
  )
}
