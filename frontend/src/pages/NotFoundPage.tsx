import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section className="space-y-2">
      <h1 className="text-2xl font-bold text-brand-800">404 – Không tìm thấy trang</h1>
      <p className="text-slate-600">Trang bạn tìm không tồn tại.</p>
      <Link to="/" className="text-brand-700 underline">
        Về trang chủ
      </Link>
    </section>
  )
}
