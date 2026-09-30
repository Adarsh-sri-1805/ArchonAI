import { useRef, useState } from 'react';
import { Upload, CheckCircle, XCircle, FileCode } from 'lucide-react';
import { uploadFile } from '../../api/client';
import styles from './UploadZone.module.css';

export default function UploadZone({ onSuccess }) {
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState('idle'); // idle | uploading | success | error
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const inputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    setStatus('uploading');
    setResult(null);
    setErrorMsg('');
    try {
      const data = await uploadFile(file);
      setResult(data);
      setStatus('success');
      onSuccess?.();
    } catch (err) {
      setErrorMsg(err.message);
      setStatus('error');
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  };

  const onInputChange = (e) => handleFile(e.target.files?.[0]);

  const reset = () => { setStatus('idle'); setResult(null); setErrorMsg(''); };

  return (
    <div className={styles.card}>
      <div className={styles.cardTitle}>
        <FileCode size={18} />
        Upload File
      </div>

      {status === 'idle' && (
        <div
          className={`${styles.zone} ${dragging ? styles.dragging : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input ref={inputRef} type="file" onChange={onInputChange} accept=".py,.js,.ts,.jsx,.tsx,.java,.go,.rs,.cpp,.c,.h,.md,.txt,.json,.yaml,.yml" />
          <div className={styles.zoneIcon}><Upload size={22} /></div>
          <div className={styles.zoneTitle}>Drop a file here</div>
          <div className={styles.zoneSub}>
            or <span className={styles.browseLink}>browse</span> to choose · .py, .js, .ts, .go, .rs, .md and more
          </div>
        </div>
      )}

      {status === 'uploading' && (
        <div className={styles.uploading}>
          <div className={styles.spinner} />
          <span className={styles.uploadingLabel}>Uploading and indexing…</span>
        </div>
      )}

      {status === 'success' && (
        <div className={styles.success}>
          <CheckCircle size={20} className={styles.successIcon} />
          <div>
            <div className={styles.successText}>File indexed successfully</div>
            <div className={styles.successSub}>{result?.chunks ?? 0} chunks added to knowledge base</div>
          </div>
          <button className={styles.resetBtn} onClick={reset}>Upload another</button>
        </div>
      )}

      {status === 'error' && (
        <div className={styles.error}>
          <XCircle size={18} />
          <div>
            <div>{errorMsg || 'Upload failed'}</div>
            <button className={styles.resetBtn} onClick={reset}>Try again</button>
          </div>
        </div>
      )}
    </div>
  );
}
