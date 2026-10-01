import { useState, useEffect } from 'react';
import * as api from '../../api';

const STATUSES = ['saved', 'applied', 'interviewing', 'offer', 'rejected'];

export default function ApplicationsTab() {
  const [applications, setApplications] = useState([]);
  const [form, setForm] = useState({ company: '', job_title: '', job_description: '', notes: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = () => api.listApplications().then(setApplications).catch((err) => setError(err.message));

  useEffect(() => { load(); }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.company || !form.job_title) return;
    setLoading(true);
    setError('');
    try {
      await api.createApplication(form);
      setForm({ company: '', job_title: '', job_description: '', notes: '' });
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await api.updateApplication(id, { status });
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteApplication(id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="tab-panel">
      <h2>📊 Application Tracker</h2>
      <p className="hint">Every application lives in a real SQL table (Postgres or SQLite), queryable by status.</p>

      <form onSubmit={handleAdd} className="application-form">
        <input placeholder="Company" value={form.company}
               onChange={(e) => setForm({ ...form, company: e.target.value })} />
        <input placeholder="Job title" value={form.job_title}
               onChange={(e) => setForm({ ...form, job_title: e.target.value })} />
        <input placeholder="Notes (optional)" value={form.notes}
               onChange={(e) => setForm({ ...form, notes: e.target.value })} />
        <button type="submit" disabled={loading}>Add application</button>
      </form>
      {error && <p className="error-text">{error}</p>}

      <table className="applications-table">
        <thead>
          <tr><th>Company</th><th>Role</th><th>Status</th><th>Match</th><th>Notes</th><th></th></tr>
        </thead>
        <tbody>
          {applications.map((a) => (
            <tr key={a.id}>
              <td>{a.company}</td>
              <td>{a.job_title}</td>
              <td>
                <select value={a.status} onChange={(e) => handleStatusChange(a.id, e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
              <td>{a.match_score != null ? `${Math.round(a.match_score * 100)}%` : '-'}</td>
              <td>{a.notes || '-'}</td>
              <td><button className="btn-link" onClick={() => handleDelete(a.id)}>Delete</button></td>
            </tr>
          ))}
          {applications.length === 0 && (
            <tr><td colSpan={6} className="empty-row">No applications tracked yet.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
