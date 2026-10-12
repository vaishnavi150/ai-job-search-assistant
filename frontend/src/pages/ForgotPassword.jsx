import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import * as api from '../api';
import AuthLayout from '../components/AuthLayout';
import Icon from '../components/Icon';
import { Alert, Button, Field } from '../components/ui';
import { isValidEmail } from '../utils/password';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [fieldError, setFieldError] = useState('');
  const [error, setError] = useState('');
  const [sentMessage, setSentMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailEnabled, setEmailEnabled] = useState(true);

  useEffect(() => {
    api.getServerConfig().then((cfg) => setEmailEnabled(cfg.email_enabled)).catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!isValidEmail(email)) {
      setFieldError('Enter a valid email address.');
      return;
    }
    setFieldError('');
    setError('');
    setLoading(true);
    try {
      const res = await api.forgotPassword(email.trim());
      setSentMessage(res.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (sentMessage) {
    return (
      <AuthLayout title="Check your email">
        <div className="auth-confirm">
          <span className="confirm-icon"><Icon name="mail" size={24} /></span>
          <p>{sentMessage}</p>
          <p className="muted">Didn’t get it? Check your spam folder, or wait a minute and try again.</p>
        </div>
        <Button variant="secondary" className="btn-block" onClick={() => setSentMessage('')}>Try another email</Button>
        <p className="auth-switch"><Link to="/login" className="link">Back to log in</Link></p>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout title="Reset your password" subtitle="Enter the email you signed up with and we’ll send you a reset link.">
      {!emailEnabled && (
        <Alert kind="warning">
          Password reset emails aren’t set up on this server yet, so no email will arrive. Contact the site owner for help.
        </Alert>
      )}
      <Alert kind="error">{error}</Alert>
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Field label="Email" htmlFor="forgot-email" error={fieldError}>
          <input
            id="forgot-email"
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setFieldError(''); }}
            autoComplete="email"
            autoFocus
            aria-invalid={fieldError ? true : undefined}
            aria-describedby={fieldError ? 'forgot-email-error' : undefined}
          />
        </Field>
        <Button type="submit" loading={loading} className="btn-block">
          {loading ? 'Sending…' : 'Send reset link'}
        </Button>
      </form>
      <p className="auth-switch"><Link to="/login" className="link">Back to log in</Link></p>
    </AuthLayout>
  );
}
