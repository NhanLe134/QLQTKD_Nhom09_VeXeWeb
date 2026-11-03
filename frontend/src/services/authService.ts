import { get, post } from './apiClient'

export type VaiTro = 'KHACH' | 'NHA_XE' | 'TAI_XE' | 'ADMIN'

export type LoginRequest = {
  ten_dang_nhap: string
  mat_khau: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
  vai_tro: VaiTro
  ho_ten: string
}

export type RegisterRequest = {
  ten_dang_nhap: string
  mat_khau: string
  ho_ten: string
  so_dien_thoai: string
  email: string | null
}

export type KhachHang = {
  khach_hang_id: string
  ho_ten: string
  email: string | null
  so_dien_thoai: string
  ngay_dang_ky: string
}

export type MeResponse = {
  user_id: string
  ten_dang_nhap: string
  vai_tro: VaiTro
  so_dien_thoai: string
  khach_hang: KhachHang | null
}

export function login(data: LoginRequest): Promise<LoginResponse> {
  return post<LoginResponse>('/api/v1/auth/login', data)
}

export function register(data: RegisterRequest): Promise<MeResponse> {
  return post<MeResponse>('/api/v1/auth/register', data)
}

export function getMe(): Promise<MeResponse> {
  return get<MeResponse>('/api/v1/auth/me')
}
