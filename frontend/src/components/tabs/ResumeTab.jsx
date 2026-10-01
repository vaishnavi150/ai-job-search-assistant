import { useState, useEffect } from 'react';
import * as api from '../../api';

export default function ResumeTab() {
  const [file, setFile] = useState(null);
  const [resume, setResume] = useState(null);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getMyResume().then(setResume).catch(() => {});
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError('');
    setStatus('');
    try {
      const result = await api.uploadResume(file);
      setResume(result);
      setStatus('Resume uploaded and indexed.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-panel">
      <h2>📄 Resume</h2>
      <p className="hint">Upload a PDF, DOCX, or TXT resume. It's parsed, chunked, and embedded so the
        matching, tailoring, and chat features can retrieve from it.</p>
      <form onSubmit={handleUpload} className="upload-form">
        <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setFile(e.target.files[0])} />
        <button type="submit" disabled={!file || loading}>{loading ? 'Uploading...' : 'Upload'}</button>
      </form>
      {status && <p className="success-text">{status}</p>}
      {error && <p className="error-text">{error}</p>}

      {resume && (
        <div className="resume-preview">
          <h3>Current resume: {resume.filename}</h3>
          <pre>{resume.raw_text.slice(0, 1200)}{resume.raw_text.length > 1200 ? '…' : ''}</pre>
        </div>
      )}
    </div>
  );
}
