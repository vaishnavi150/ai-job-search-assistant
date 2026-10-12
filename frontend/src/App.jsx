import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute, { GuestRoute } from './components/ProtectedRoute';
import AppLayout from './components/AppLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Overview from './pages/Overview';
import Resume from './pages/Resume';
import Jobs from './pages/Jobs';
import Match from './pages/Match';
import Interview from './pages/Interview';
import MockInterview from './pages/MockInterview';
import Applications from './pages/Applications';
import Chat from './pages/Chat';
import Account from './pages/Account';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/app" replace />} />
          <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
          <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />
          <Route path="/forgot-password" element={<GuestRoute><ForgotPassword /></GuestRoute>} />
          {/* Not guest-only: a logged-in user may follow a reset link too. */}
          <Route path="/reset-password" element={<ResetPassword />} />

          <Route path="/app" element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route index element={<Overview />} />
            <Route path="resume" element={<Resume />} />
            <Route path="jobs" element={<Jobs />} />
            <Route path="match" element={<Match />} />
            <Route path="interview" element={<Interview />} />
            <Route path="mock-interview" element={<MockInterview />} />
            <Route path="applications" element={<Applications />} />
            <Route path="chat" element={<Chat />} />
            <Route path="account" element={<Account />} />
            <Route path="*" element={<Navigate to="/app" replace />} />
          </Route>

          {/* v0.1 URL */}
          <Route path="/dashboard" element={<Navigate to="/app" replace />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
