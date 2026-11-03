import { get } from './apiClient'

export type HealthResponse = {
  status: string
}

export function getHealth(): Promise<HealthResponse> {
  return get<HealthResponse>('/health')
}
