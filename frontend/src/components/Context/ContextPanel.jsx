import { X, FileSearch, FileCode, FolderGit2 } from 'lucide-react';
import styles from './ContextPanel.module.css';

function getFilename(src) {
  const s = src?.source || src?.filename || '';
  return s.split('/').pop().split('\\').pop() || s || 'Unknown';
}

function getFilepath(src) {
  return src?.source || src?.filename || '';
}

export default function ContextPanel({ open, onClose, sources, activeSourceIdx, onSourceClick }) {
  return (
    <aside className={`${styles.panel} ${!open ? styles.hidden : ''}`}>
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <span className={styles.title}>Retrieved Context</span>
          {sources?.length > 0 && (
            <span className={styles.countBadge}>{sources.length}</span>
          )}
        </div>
        <button className={styles.closeBtn} onClick={onClose}>
          <X size={15} />
        </button>
      </div>

      <div className={styles.scrollArea}>
        {!sources || sources.length === 0 ? (
          <div className={styles.emptyContext}>
            <FileSearch size={32} color="var(--border-hover)" />
            <span>No context yet.<br />Sources appear after your first chat message.</span>
          </div>
        ) : (
          sources.map((src, i) => {
            const name = getFilename(src);
            const path = getFilepath(src);
            const score = Math.round((src.score || 0) * 100);
            const isRepo = path.includes('/') || path.includes('\\');

            return (
              <div
                key={i}
                className={`${styles.fileCard} ${activeSourceIdx === i ? styles.active : ''}`}
                onClick={() => onSourceClick(i)}
              >
                {/* Header */}
                <div className={styles.cardHeader}>
                  <div className={styles.cardIcon}>
                    {isRepo ? <FolderGit2 size={14} /> : <FileCode size={14} />}
                  </div>
                  <div className={styles.cardInfo}>
                    <div className={styles.cardName}>{name}</div>
                    <div className={styles.cardPath}>{path}</div>
                  </div>
                  <span className={styles.scoreBadge}>{score}%</span>
                </div>

                {/* Relevance bar */}
                <div className={styles.bar}>
                  <div className={styles.barFill} style={{ width: `${score}%` }} />
                </div>

                {/* Excerpt */}
                {src.excerpt && (
                  <div className={styles.excerpt}>{src.excerpt}</div>
                )}

                {/* Index badge */}
                <div className={styles.cardFooter}>
                  <span className={styles.indexBadge}>Source [{i + 1}]</span>
                  {src.chunk_index != null && (
                    <span className={styles.chunkBadge}>chunk #{src.chunk_index}</span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
