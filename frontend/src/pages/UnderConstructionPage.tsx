type Props = {
  title: string
}

export default function UnderConstructionPage({ title }: Props) {
  return (
    <section className="space-y-2">
      <h1 className="text-2xl font-bold text-brand-800">{title}</h1>
      <p className="text-slate-600">Đang xây dựng.</p>
    </section>
  )
}
