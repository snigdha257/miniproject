import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import DashboardOverviewPage from './pages/DashboardOverviewPage.jsx'
import UploadPage from './pages/UploadPage.jsx'
import TextMaskingPage from './pages/TextMaskingPage.jsx'
import ResultsPage from './pages/ResultsPage.jsx'
import UnmaskPage from './pages/UnmaskPage.jsx'
import HistoryPage from './pages/HistoryPage.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardOverviewPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/upload"
        element={
          <ProtectedRoute>
            <UploadPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/text-mask"
        element={
          <ProtectedRoute>
            <TextMaskingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/results"
        element={
          <ProtectedRoute>
            <ResultsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/unmask"
        element={
          <ProtectedRoute>
            <UnmaskPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard/history"
        element={
          <ProtectedRoute>
            <HistoryPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
