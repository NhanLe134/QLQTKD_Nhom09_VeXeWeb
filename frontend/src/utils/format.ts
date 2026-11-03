const VIETNAM_TIME_ZONE = 'Asia/Ho_Chi_Minh'

const numberFormatter = new Intl.NumberFormat('vi-VN')

const dateTimeFormatter = new Intl.DateTimeFormat('vi-VN', {
  timeZone: VIETNAM_TIME_ZONE,
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})

/** 200000 -> "200.000 đ" */
export function formatCurrency(amount: number): string {
  return `${numberFormatter.format(amount)} đ`
}

/** Hiển thị theo giờ Việt Nam dạng dd/MM/yyyy HH:mm; giá trị không hợp lệ trả chuỗi rỗng. */
export function formatDateTime(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  // Ghép từ formatToParts để thứ tự ngày/giờ không phụ thuộc cách trình bày mặc định của ICU
  const parts = Object.fromEntries(
    dateTimeFormatter.formatToParts(date).map((part) => [part.type, part.value]),
  )
  return `${parts.day}/${parts.month}/${parts.year} ${parts.hour}:${parts.minute}`
}
