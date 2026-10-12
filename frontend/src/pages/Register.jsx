import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthLayout from '../components/AuthLayout';
import PasswordField from '../components/PasswordField';
import { Alert, Button, Field } from '../components/ui';
import { isPasswordValid, isValidEmail } from '../utils/password';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!isValidEmail(email)) errs.email = 'Enter a valid email address.';
    if (!isPasswordValid(password)) errs.password = 'Your password doesn’t meet all the requirements yet.';
    if (confirm !== password) errs.confirm = 'Passwords don’t match.';
    setFieldErrors(errs);
    if (Object.keys(errs).length) return;

    setError('');
    setLoading(true);
    try {
      await register(email, password, confirm);
      navigate('/app', { replace: true });
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create your account" subtitle="Start matching your resume to real jobs in minutes.">
      {error && (
      <Alert kind="error">
        {error}
        {error.includes('already exists') && (
          <> <Link to="/login" className="link">Log in</Link> or <Link to="/forgot-password" className="link">reset your password</Link>.</>
        )}
      </Alert>
      )}
      <form className="form" onSubmit={handleSubmit} noValidate>
        <Field label="Email" htmlFor="reg-email" error={fieldErrors.email}>
          <input
            id="reg-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            autoFocus
            aria-invalid={fieldErrors.email ? true : undefined}
            aria-describedby={fieldErrors.email ? 'reg-email-error' : undefined}
          />
        </Field>
        <PasswordField
          id="reg-password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          showRules
          error={fieldErrors.password}
        />
        <PasswordField
          id="reg-confirm"
          label="Confirm password"
          value={confirm}
          onChange={setConfirm}
          autoComplete="new-password"
          error={fieldErrors.confirm || (confirm && confirm !== password ? 'Passwords don’t match.' : '')}
        />
        <Button type="submit" loading={loading} className="btn-block">
          {loading ? 'Creating account…' : 'Create account'}
        </Button>
      </form>
      <p className="auth-switch">
        Already have an account? <Link to="/login" className="link">Log in</Link>
      </p>
    </AuthLayout>
  );
}
