// Kiểm tra phía client chỉ để báo lỗi sớm; backend vẫn kiểm tra lại.

/** BR-BUS-03 */
export const MIN_PASSWORD_LENGTH = 8

const PHONE_PATTERN = /^0\d{9}$/
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

/** BR-BUS-04: 10 chữ số, bắt đầu bằng 0. */
export function isValidPhone(value: string): boolean {
  return PHONE_PATTERN.test(value.trim())
}

export function isValidEmail(value: string): boolean {
  return EMAIL_PATTERN.test(value.trim())
}

/** Độ dài cột ve.ho_ten (docs/data-model.md) */
export const MAX_PASSENGER_NAME_LENGTH = 200
/** Độ dài cột ve.diem_don, ve.diem_tra: cả chuỗi "Khu vực – địa chỉ" */
export const MAX_POINT_LENGTH = 150
/** Độ dài phần " – " backend chèn giữa khu vực và địa chỉ */
const POINT_SEPARATOR_LENGTH = 3

/** Gộp khoảng trắng thừa như backend trước khi kiểm tra. */
export function collapseSpaces(value: string): string {
  return value.trim().split(/\s+/).filter(Boolean).join(' ')
}

/** Chỉ để báo sớm: điểm và địa chỉ sau khi backend ghép có vượt độ dài cột không. */
export function isPointTooLong(khuVuc: string, diaChi: string): boolean {
  const address = collapseSpaces(diaChi)
  const length = khuVuc.length + (address ? POINT_SEPARATOR_LENGTH + address.length : 0)
  return length > MAX_POINT_LENGTH
}
