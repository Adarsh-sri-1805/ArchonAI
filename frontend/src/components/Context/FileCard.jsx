import styles from './FileCard.module.css';

export default function FileCard({ file, active, onClick }) {
  const score = Math.round(file.relevance * 100);

  return (
    <div
      className={`${styles.card} ${active ? styles.active : ''}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.fileInfo}>
          <div className={styles.filename}>{file.filename}</div>
          <div className={styles.filepath}>{file.filepath}</div>
        </div>
        <span className={styles.scoreBadge}>{score}%</span>
      </div>

      {/* Relevance bar */}
      <div className={styles.relevanceWrap}>
        <div className={styles.relevanceLabel}>
          <span>Relevance</span>
        </div>
        <div className={styles.bar}>
          <div className={styles.barFill} style={{ width: `${score}%` }} />
        </div>
      </div>

      {/* Snippet */}
      <div className={styles.snippet}>{file.snippet}</div>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.lines}>Lines {file.lines}</span>
        <span className={styles.langBadge}>{file.language}</span>
      </div>
    </div>
  );
}
