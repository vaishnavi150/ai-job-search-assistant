import { useEffect, useState } from 'react';
import * as api from '../api';
import Icon from '../components/Icon';
import { Alert, Button, EmptyState, Field, PageHeader, Spinner, STATUS_LABELS } from '../components/ui';

const STATUSES = Object.keys(STATUS_LABELS);
const EMPTY_FORM = { company: '', job_title: '', job_url: '', notes: '', status: 'saved' };

function ApplicationRow({ app, onUpdate, onDelete }) {
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState(app.notes ?? '');
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  const saveNotes = async () => {
    setBusy(true);
    const ok = await onUpdate(app.id, { notes: notes.trim() });
    setBusy(false);
    if (ok) setEditingNotes(false);
  };

  return (
    <li className="app-row">
      <div className="app-main">
        <div className="app-title-line">
          <strong className="app-title">{app.job_title}</strong>
          {app.match_score != null && <span className="match-pill">{Math.round(app.match_score * 100)}% match</span>}
        </div>
        <span className="muted">{app.company}</span>
        {app.job_url && (
          <a href={app.job_url} target="_blank" rel="noopener noreferrer" className="link small app-link">
            View posting <Icon name="external" size={12} />
          </a>
        )}
        {editingNotes ? (
          <div className="notes-edit">
            <label htmlFor={`notes-${app.id}`} className="sr-only">Notes</label>
            <textarea id={`notes-${app.id}`} rows={2} value={notes} maxLength={5000} onChange={(e) => setNotes(e.target.value)} />
            <div className="button-row">
              <Button variant="secondary" loading={busy} onClick={saveNotes}>Save</Button>
              <Button variant="ghost" onClick={() => { setNotes(app.notes ?? ''); setEditingNotes(false); }}>Cancel</Button>
            </div>
          </div>
        ) : (
          <button type="button" className="notes-display" onClick={() => setEditingNotes(true)}>
            {app.notes ? app.notes : <span className="muted">Add notes…</span>}
          </button>
        )}
      </div>
      <div className="app-side">
        <label htmlFor={`status-${app.id}`} className="sr-only">Status for {app.job_title}</label>
        <select
          id={`status-${app.id}`}
          className={`status-select status-${app.status}`}
          value={app.status}
          onChange={(e) => onUpdate(app.id, { status: e.target.value })}
        >
          {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
        {confirming ? (
          <div className="confirm-inline">
            <Button variant="danger" onClick={() => onDelete(app.id)}>Delete</Button>
            <Button variant="ghost" onClick={() => setConfirming(false)}>Keep</Button>
          </div>
        ) : (
          <button type="button" className="icon-btn" onClick={() => setConfirming(true)} aria-label={`Delete ${app.job_title} at ${app.company}`}>
            <Icon name="trash" size={16} />
          </button>
        )}
      </div>
    </li>
  );
}

export default function Applications() {
  const [applications, setApplications] = useState(null);
  const [filter, setFilter] = useState('all');
  const [form, setForm] = useState(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  const [error, setError] = useState('');
  const [adding, setAdding] = useState(false);

  const load = () => api.listApplications().then(setApplications).catch((err) => {
    setApplications((a) => a ?? []);
    setError(err.message);
  });

  useEffect(() => {
    load();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    const errs = {};
    if (!form.company.trim()) errs.company = 'Company is required.';
    if (!form.job_title.trim()) errs.job_title = 'Job title is required.';
    if (form.job_url && !/^https?:\/\//i.test(form.job_url.trim())) errs.job_url = 'Link must start with http:// or https://';
    setFormErrors(errs);
    if (Object.keys(errs).length) return;

    setAdding(true);
    setError('');
    try {
      await api.createApplication({ ...form, job_url: form.job_url.trim() || null, notes: form.notes.trim() || null });
      setForm(EMPTY_FORM);
      setShowForm(false);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setAdding(false);
    }
  };

  const handleUpdate = async (id, payload) => {
    try {
      const updated = await api.updateApplication(id, payload);
      setApplications((list) => list.map((a) => (a.id === id ? updated : a)));
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteApplication(id);
      setApplications((list) => list.filter((a) => a.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const counts = { all: applications?.length ?? 0 };
  STATUSES.forEach((s) => {
    counts[s] = applications?.filter((a) => a.status === s).length ?? 0;
  });
  const visible = applications?.filter((a) => filter === 'all' || a.status === filter) ?? [];

  return (
    <>
      <PageHeader
        title="Applications"
        description="Track every role from saved to offer."
        actions={!showForm && <Button icon="plus" onClick={() => setShowForm(true)}>Add application</Button>}
      />

      <Alert kind="error" onDismiss={error ? () => setError('') : undefined}>{error}</Alert>

      {showForm && (
        <form className="card form-grid" onSubmit={handleAdd} noValidate>
          <Field label="Company" htmlFor="app-company" error={formErrors.company}>
            <input id="app-company" value={form.company} maxLength={200} autoFocus
                   onChange={(e) => setForm({ ...form, company: e.target.value })} />
          </Field>
          <Field label="Job title" htmlFor="app-title" error={formErrors.job_title}>
            <input id="app-title" value={form.job_title} maxLength={200}
                   onChange={(e) => setForm({ ...form, job_title: e.target.value })} />
          </Field>
          <Field label="Job link" htmlFor="app-url" optional error={formErrors.job_url}>
            <input id="app-url" type="url" value={form.job_url} maxLength={1000} placeholder="https://"
                   onChange={(e) => setForm({ ...form, job_url: e.target.value })} />
          </Field>
          <Field label="Status" htmlFor="app-status">
            <select id="app-status" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
            </select>
          </Field>
          <Field label="Notes" htmlFor="app-notes" optional>
            <textarea id="app-notes" rows={2} value={form.notes} maxLength={5000}
                      onChange={(e) => setForm({ ...form, notes: e.target.value })} />
          </Field>
          <div className="button-row form-grid-actions">
            <Button type="submit" loading={adding}>{adding ? 'Adding…' : 'Add application'}</Button>
            <Button variant="ghost" onClick={() => { setShowForm(false); setFormErrors({}); }}>Cancel</Button>
          </div>
        </form>
      )}

      <div className="filter-tabs" role="group" aria-label="Filter by status">
        {['all', ...STATUSES].map((s) => (
          <button
            key={s}
            type="button"
            aria-pressed={filter === s}
            className={`filter-tab ${filter === s ? 'active' : ''}`}
            onClick={() => setFilter(s)}
          >
            {s === 'all' ? 'All' : STATUS_LABELS[s]} <span className="count">{counts[s]}</span>
          </button>
        ))}
      </div>

      {applications === null ? (
        <Spinner label="Loading applications…" />
      ) : visible.length === 0 ? (
        <EmptyState
          icon="briefcase"
          title={filter === 'all' ? 'No applications yet' : `Nothing marked “${STATUS_LABELS[filter]}”`}
          action={filter === 'all' && !showForm && <Button icon="plus" onClick={() => setShowForm(true)}>Add your first</Button>}
        >
          {filter === 'all' ? 'Save jobs from Find jobs, or add one you found elsewhere.' : 'Change a job’s status to see it here.'}
        </EmptyState>
      ) : (
        <ul className="card app-list">
          {visible.map((a) => (
            <ApplicationRow key={a.id} app={a} onUpdate={handleUpdate} onDelete={handleDelete} />
          ))}
        </ul>
      )}
    </>
  );
}
