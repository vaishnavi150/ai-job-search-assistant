import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import * as api from '../api';
import { useAuth } from '../context/AuthContext';
import AuthLayout from '../components/AuthLayout';
import PasswordField from '../components/PasswordField';
import { Alert, Button, Spinner } from '../components/ui';
import { isPasswordValid } from '../utils/password';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [token] = useState(() => params.get('token') || '');
  const [linkState, setLinkState] = useState(token ? 'checking' : 'invalid');
  const [linkError, setLinkError] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Remove the token from the address bar so it isn't kept in history
    // or leaked through screenshots. (Through the router, so its own
    // history bookkeeping stays intact.)
    if (token) navigate('/reset-password', { replace: true });
  }, [token, navigate]);

  useEffect(() => {
    if (!token) return;
    api.validateResetToken(token)
      .then(() => setLinkState('valid'))
      .catch((err) => {
        setLinkError(err.message);
        setLinkState('invalid');
      });
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!isPasswordValid(password)) errs.password = 'Your password doesn’t meet all the requirements yet.';
    if (confirm !== password) errs.confirm = 'Passwords don’t match.';
    setFieldErrors(errs);
    if (Object.keys(errs).length) return;

    setError('');
    setLoading(true);
    try {
      const res = await api.resetPassword(token, password, confirm);
      // The reset revoked every session, including this browser's if it was
      // signed in; drop it so /login doesn't bounce back to the app.
      logout();
      navigate('/login', { replace: true, state: { notice: res.message } });
    } catch (err) {
      setError(err.message);
      setLoading(false);
      if (err.status === 400) setLinkState('invalid');
    }
  };

  if (linkState === 'checking') {
    return (
      <AuthLayout title="Reset your password">
        <Spinner label="Checking your reset link…" />
      </AuthLayout>
    );
  }

  if (linkState === 'invalid') {
    return (
      <AuthLayout title="Link expired" subtitle="Reset links work once and expire after a short time.">
        <Alert kind="error">{error || linkError || 'This reset link is invalid or incomplete.'}</Alert>
        <Link to="/forgot-password" className="btn btn-primary btn-block">Request a new link</Link>
        <p className="auth-switch"><Link to="/login" className="link">Back to log in</Link></p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Choose a new password" subtitle="You’ll be signed out on all other devices.">
      <Alert kind="error">{error}</Alert>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <PasswordField
          id="reset-password"
          label="New password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          autoFocus
          showRules
          error={fieldErrors.password}
        />
        <PasswordField
          id="reset-confirm"
          label="Confirm new password"
          value={confirm}
          onChange={setConfirm}
          autoComplete="new-password"
          error={fieldErrors.confirm || (confirm && confirm !== password ? 'Passwords don’t match.' : '')}
        />
        <Button type="submit" loading={loading} className="btn-block">
          {loading ? 'Saving…' : 'Reset password'}
        </Button>
      </form>
    </AuthLayout>
  );
}
