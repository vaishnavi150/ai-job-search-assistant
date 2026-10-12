import { useState } from 'react';
import * as api from '../api';
import { useAuth } from '../context/AuthContext';
import PasswordField from '../components/PasswordField';
import { Alert, Button, PageHeader } from '../components/ui';
import { isPasswordValid } from '../utils/password';
import { clearOnEdit } from '../utils/forms';

export default function Account() {
  const { user, email, startSession, logout } = useAuth();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  const changePassword = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!current) errs.current = 'Enter your current password.';
    if (!isPasswordValid(next)) errs.next = 'Your new password doesn’t meet all the requirements yet.';
    else if (next === current) errs.next = 'Choose a password different from your current one.';
    if (confirm !== next) errs.confirm = 'Passwords don’t match.';
    setFieldErrors(errs);
    if (Object.keys(errs).length) return;

    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const res = await api.changePassword(current, next, confirm);
      await startSession(res.access_token);
      setCurrent('');
      setNext('');
      setConfirm('');
      setSuccess('Password updated. You’ve been signed out on your other devices.');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const signOutEverywhere = async () => {
    setSigningOut(true);
    try {
      await api.logoutAll();
    } catch {
      // even if this fails, sign out here
    }
    logout();
  };

  return (
    <>
      <PageHeader title="Account" description="Manage your sign-in details and security." />

      <section className="card section">
        <h2 className="card-title">Profile</h2>
        <dl className="detail-list">
          <div><dt>Email</dt><dd>{email}</dd></div>
          {user?.created_at && (
            <div><dt>Member since</dt><dd>{new Date(`${user.created_at}Z`).toLocaleDateString()}</dd></div>
          )}
        </dl>
      </section>

      <section className="card section">
        <h2 className="card-title">Change password</h2>
        <Alert kind="error">{error}</Alert>
        <Alert kind="success">{success}</Alert>
        <form className="form narrow" onSubmit={changePassword} noValidate>
          <PasswordField id="cur-pw" label="Current password" value={current} onChange={clearOnEdit(setCurrent, setFieldErrors, 'current')}
                         autoComplete="current-password" error={fieldErrors.current} />
          <PasswordField id="new-pw" label="New password" value={next} onChange={clearOnEdit(setNext, setFieldErrors, 'next', 'confirm')}
                         autoComplete="new-password" showRules error={fieldErrors.next} />
          <PasswordField id="confirm-pw" label="Confirm new password" value={confirm} onChange={clearOnEdit(setConfirm, setFieldErrors, 'confirm')}
                         autoComplete="new-password"
                         error={fieldErrors.confirm || (confirm && confirm !== next ? 'Passwords don’t match.' : '')} />
          <Button type="submit" loading={saving}>{saving ? 'Updating…' : 'Update password'}</Button>
        </form>
      </section>

      <section className="card section">
        <h2 className="card-title">Sessions</h2>
        <p className="muted">Signed in on a shared or lost device? Sign out everywhere, including here.</p>
        <Button variant="danger" loading={signingOut} onClick={signOutEverywhere}>Sign out of all devices</Button>
      </section>
    </>
  );
}
