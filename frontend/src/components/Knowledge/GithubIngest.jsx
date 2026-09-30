import { useState } from 'react';
import { CheckCircle, XCircle, GitBranch } from 'lucide-react';
import { ingestGithub } from '../../api/client';
import styles from './GithubIngest.module.css';

function GithubIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
      <path d="M9 18c-4.51 2-5-2-7-2" />
    </svg>
  );
}

export default function GithubIngest({ onSuccess }) {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState('idle'); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setStatus('loading');
    setResult(null);
    setErrorMsg('');
    try {
      const data = await ingestGithub(url.trim());
      setResult(data);
      setStatus('success');
      onSuccess?.();
    } catch (err) {
      setErrorMsg(err.message);
      setStatus('error');
    }
  };

  const reset = () => { setStatus('idle'); setResult(null); setErrorMsg(''); setUrl(''); };

  return (
    <div className={styles.card}>
      <div className={styles.cardTitle}>
        <GithubIcon size={18} />
        Index GitHub Repository
      </div>

      <form onSubmit={handleSubmit} className={styles.inputRow}>
        <input
          className={styles.urlInput}
          placeholder="https://github.com/owner/repo"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={status === 'loading'}
        />
        <button
          type="submit"
          className={styles.indexBtn}
          disabled={status === 'loading' || !url.trim()}
        >
          {status === 'loading' ? (
            <><div className={styles.spinner} /> Indexing…</>
          ) : (
            <><GitBranch size={15} /> Index Repo</>
          )}
        </button>
      </form>

      {status === 'loading' && (
        <div className={styles.loadingRow}>
          <div className={styles.spinner} />
          Cloning and indexing repository — this may take a minute…
        </div>
      )}

      {status === 'success' && (
        <div className={styles.success}>
          <CheckCircle size={20} className={styles.successIcon} />
          <div>
            <div className={styles.successText}>Repository indexed: {result?.repository}</div>
            <div className={styles.successSub}>{result?.chunks_indexed ?? 0} chunks indexed</div>
            <button className={styles.resetBtn} onClick={reset}>Index another</button>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className={styles.error}>
          <XCircle size={18} />
          <div>
            <div>{errorMsg || 'Indexing failed'}</div>
            <button className={styles.resetBtn} onClick={reset}>Try again</button>
          </div>
        </div>
      )}

      <div className={styles.hint}>
        Public repositories only. Private repos require a GitHub token in the backend .env.
      </div>
    </div>
  );
}
