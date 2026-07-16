import React, { createContext, useContext, useState } from 'react'

const ResultContext = createContext()

export function ResultProvider({ children }) {
  const [result, setResult] = useState(null)
  const [restoredText, setRestoredText] = useState('')

  return (
    <ResultContext.Provider value={{ result, setResult, restoredText, setRestoredText }}>
      {children}
    </ResultContext.Provider>
  )
}

export function useResult() {
  const context = useContext(ResultContext)
  if (!context) {
    throw new Error('useResult must be used within ResultProvider')
  }
  return context
}
