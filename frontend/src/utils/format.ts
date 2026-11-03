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

// Ghép từ formatToParts để thứ tự ngày/giờ không phụ thuộc cách trình bày mặc định của ICU
function vietnamParts(value: string | Date): Record<string, string> | null {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) {
    return null
  }
  return Object.fromEntries(
    dateTimeFormatter.formatToParts(date).map((part) => [part.type, part.value]),
  )
}

/** Hiển thị theo giờ Việt Nam dạng dd/MM/yyyy HH:mm; giá trị không hợp lệ trả chuỗi rỗng. */
export function formatDateTime(value: string | Date): string {
  const parts = vietnamParts(value)
  return parts ? `${parts.day}/${parts.month}/${parts.year} ${parts.hour}:${parts.minute}` : ''
}

/** Giờ Việt Nam dạng HH:mm; giá trị không hợp lệ trả chuỗi rỗng. */
export function formatTime(value: string | Date): string {
  const parts = vietnamParts(value)
  return parts ? `${parts.hour}:${parts.minute}` : ''
}

/** Ngày dạng dd/MM/yyyy. Chuỗi "YYYY-MM-DD" (ngày theo giờ Việt Nam từ backend) giữ nguyên ngày. */
export function formatDate(value: string | Date): string {
  if (typeof value === 'string') {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
    if (match) {
      return `${match[3]}/${match[2]}/${match[1]}`
    }
  }
  const parts = vietnamParts(value)
  return parts ? `${parts.day}/${parts.month}/${parts.year}` : ''
}

/** Ngày hôm nay theo giờ Việt Nam dạng YYYY-MM-DD (giá trị của ô chọn ngày). */
export function todayInVietnam(now: Date = new Date()): string {
  const parts = vietnamParts(now)
  return parts ? `${parts.year}-${parts.month}-${parts.day}` : ''
}

/** Tên loại xe từ backend; thiếu tên thì hiện theo số chỗ. */
export function formatVehicleType(tenLoaiXe: string | null, soCho: number): string {
  return tenLoaiXe ?? `Xe ${soCho} chỗ`
}
