import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { attachToken } from '../api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('auth_token'))
  const [email, setEmail] = useState(() => localStorage.getItem('auth_email'))

  useEffect(() => {
    if (token) {
      localStorage.setItem('auth_token', token)
      attachToken(token)
    } else {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_email')
      attachToken(null)
    }
  }, [token])

  useEffect(() => {
    if (email) {
      localStorage.setItem('auth_email', email)
    }
  }, [email])

  const value = useMemo(
    () => ({ token, email, setToken, setEmail, signOut: () => { setToken(null); setEmail(null) } }),
    [token, email],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
