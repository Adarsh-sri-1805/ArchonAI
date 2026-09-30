import { useEffect, useRef, useState } from 'react';
import { Search } from 'lucide-react';
import { useSearch } from '../../hooks/useSearch';
import styles from './SearchModal.module.css';

export default function SearchModal({ onClose, onResultClick }) {
  const inputRef = useRef(null);
  const { results, loading, error, search, clear } = useSearch();
  const [value, setValue] = useState('');
  const debounceRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const handleChange = (e) => {
    const v = e.target.value;
    setValue(v);
    clearTimeout(debounceRef.current);
    if (v.trim().length < 2) { clear(); return; }
    debounceRef.current = setTimeout(() => search(v), 400);
  };

  const handleResult = (r) => {
    onResultClick?.(r);
    onClose();
  };

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <div className={styles.searchRow}>
          <Search size={18} color="var(--secondary)" />
          <input
            ref={inputRef}
            className={styles.searchInput}
            placeholder="Search across your codebase…"
            value={value}
            onChange={handleChange}
          />
          <span className={styles.escHint}>Esc</span>
        </div>

        <div className={styles.results}>
          {loading && (
            <div className={styles.loading}>
              <div className={styles.spinner} />
              Searching…
            </div>
          )}

          {!loading && error && (
            <div className={styles.empty}>{error}</div>
          )}

          {!loading && !error && value.trim().length >= 2 && results.length === 0 && (
            <div className={styles.empty}>No results found for "{value}"</div>
          )}

          {!loading && results.map((r, i) => (
            <div key={i} className={styles.resultItem} onClick={() => handleResult(r)}>
              <div className={styles.resultHeader}>
                <span className={styles.resultFile}>
                  {r.source || r.filename || 'Unknown'}
                </span>
                <span className={styles.resultScore}>
                  {Math.round((r.score || 0) * 100)}% match
                </span>
              </div>
              <div className={styles.resultExcerpt}>
                {(r.excerpt || '').slice(0, 200)}
              </div>
            </div>
          ))}

          {!value.trim() && (
            <div className={styles.empty}>
              Type to search across all indexed files and repositories
            </div>
          )}
        </div>

        <div className={styles.footer}>
          {results.length > 0 ? `${results.length} results` : 'Powered by hybrid vector + BM25 search'}
        </div>
      </div>
    </div>
  );
}
