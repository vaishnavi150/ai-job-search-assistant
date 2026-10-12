import { useEffect, useRef, useState } from 'react';
import * as api from '../api';
import Icon from '../components/Icon';
import { Alert, Button, EmptyState, PageHeader, Spinner } from '../components/ui';

const ACCEPTED = ['pdf', 'docx', 'txt'];
const MAX_MB = 5;

function validateFile(file) {
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (!ACCEPTED.includes(ext)) return 'Please choose a PDF, DOCX, or TXT file.';
  if (file.size > MAX_MB * 1024 * 1024) return `That file is larger than ${MAX_MB} MB.`;
  if (file.size === 0) return 'That file is empty.';
  return '';
}

export default function Resume() {
  const [resume, setResume] = useState(undefined);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [uploading, setUploading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    api.getMyResume()
      .then(setResume)
      .catch((err) => {
        setResume(null);
        if (err.status !== 404) setError(err.message);
      });
  }, []);

  const pick = (f) => {
    if (!f) return;
    const problem = validateFile(f);
    setSuccess('');
    setError(problem);
    setFile(problem ? null : f);
  };

  const upload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    setSuccess('');
    try {
      const result = await api.uploadResume(file);
      setResume(result);
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
      setSuccess('Resume uploaded and analysed. Matching, job ranking and chat will now use it.');
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const remove = async () => {
    setDeleting(true);
    setError('');
    try {
      await api.deleteMyResume();
      setResume(null);
      setConfirmDelete(false);
      setSuccess('Resume deleted.');
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Resume"
        description="Upload your resume once - every tool uses it to give advice grounded in your real experience."
      />
      <Alert kind="error" onDismiss={error ? () => setError('') : undefined}>{error}</Alert>
      <Alert kind="success" onDismiss={success ? () => setSuccess('') : undefined}>{success}</Alert>

      <div
        className={`dropzone ${dragging ? 'dragging' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files?.[0]);
        }}
      >
        <span className="dropzone-icon"><Icon name="upload" size={24} /></span>
        <p className="dropzone-title">
          {file ? file.name : resume ? 'Replace your resume' : 'Drag and drop your resume here'}
        </p>
        <p className="muted small">
          {file ? `${(file.size / 1024).toFixed(0)} KB · ready to upload` : `PDF, DOCX or TXT · up to ${MAX_MB} MB`}
        </p>
        <div className="button-row center">
          <label className="btn btn-secondary">
            <Icon name="file" size={16} />
            <span>Choose file</span>
            <input
              ref={inputRef}
              type="file"
              className="sr-only"
              aria-label="Choose a resume file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => pick(e.target.files?.[0])}
            />
          </label>
          {file && (
            <Button onClick={upload} loading={uploading} icon="upload">
              {uploading ? 'Analysing…' : 'Upload'}
            </Button>
          )}
        </div>
      </div>

      <section className="section">
        <h2 className="section-title">Current resume</h2>
        {resume === undefined ? (
          <Spinner label="Loading…" />
        ) : resume === null ? (
          <EmptyState icon="file" title="No resume yet">
            Upload one above to unlock matching, tailored bullets, and resume-ranked job search.
          </EmptyState>
        ) : (
          <div className="card">
            <div className="card-head">
              <div>
                <h3 className="card-title">{resume.filename}</h3>
                {resume.created_at && (
                  <p className="muted small">Uploaded {new Date(`${resume.created_at}Z`).toLocaleDateString()}</p>
                )}
              </div>
              {confirmDelete ? (
                <div className="button-row">
                  <span className="small">Delete this resume?</span>
                  <Button variant="danger" loading={deleting} onClick={remove}>Delete</Button>
                  <Button variant="ghost" onClick={() => setConfirmDelete(false)}>Cancel</Button>
                </div>
              ) : (
                <Button variant="ghost" icon="trash" onClick={() => setConfirmDelete(true)}>Delete</Button>
              )}
            </div>
            <p className="muted small">This is the text we extracted. If it looks garbled, try a different file format.</p>
            <pre className={`resume-text ${expanded ? 'expanded' : ''}`}>{resume.raw_text}</pre>
            {resume.raw_text.length > 1200 && (
              <button type="button" className="link-btn" onClick={() => setExpanded((v) => !v)} aria-expanded={expanded}>
                {expanded ? 'Show less' : 'Show full text'}
              </button>
            )}
          </div>
        )}
      </section>
    </>
  );
}
