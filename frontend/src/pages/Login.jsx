import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthLayout from '../components/AuthLayout';
import PasswordField from '../components/PasswordField';
import { Alert, Button, Field } from '../components/ui';
import { isValidEmail } from '../utils/password';

export default function Login() {
  const { login, sessionExpired } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const notice = location.state?.notice;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!isValidEmail(email)) errs.email = 'Enter a valid email address.';
    if (!password) errs.password = 'Enter your password.';
    setFieldErrors(errs);
    if (Object.keys(errs).length) return;

    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate(location.state?.from?.startsWith('/app') ? location.state.from : '/app', { replace: true });
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue your job search.">
      {sessionExpired && !error && <Alert kind="info">Your session expired. Please log in again.</Alert>}
      {notice && !error && <Alert kind="success">{notice}</Alert>}
      <Alert kind="error">{error}</Alert>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Field label="Email" htmlFor="login-email" error={fieldErrors.email}>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            autoFocus
            aria-invalid={fieldErrors.email ? true : undefined}
            aria-describedby={fieldErrors.email ? 'login-email-error' : undefined}
          />
        </Field>
        <PasswordField
          id="login-password"
          value={password}
          onChange={setPassword}
          autoComplete="current-password"
          error={fieldErrors.password}
        />
        <div className="form-row-end">
          <Link to="/forgot-password" className="link">Forgot password?</Link>
        </div>
        <Button type="submit" loading={loading} className="btn-block">
          {loading ? 'Logging in…' : 'Log in'}
        </Button>
      </form>
      <p className="auth-switch">
        New here? <Link to="/register" className="link">Create an account</Link>
      </p>
    </AuthLayout>
  );
}
