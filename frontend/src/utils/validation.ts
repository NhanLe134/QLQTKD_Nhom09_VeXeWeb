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
