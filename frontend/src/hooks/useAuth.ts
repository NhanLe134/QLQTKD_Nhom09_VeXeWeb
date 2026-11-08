import { useContext } from 'react'

import { AuthContext, type AuthContextValue } from '../context/AuthContext'

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth phải dùng bên trong <AuthProvider>.')
  }
  return value
}
