import styles from './ProjectCard.module.css';

export default function ProjectCard({ project, active, onClick }) {
  return (
    <div
      className={`${styles.card} ${active ? styles.active : ''}`}
      onClick={onClick}
    >
      <div className={styles.topRow}>
        <span className={styles.name}>{project.name}</span>
        {project.indexed
          ? <span className={styles.indexedBadge}>Indexed</span>
          : <span className={styles.pendingBadge}>Pending</span>
        }
      </div>
      <p className={styles.description}>{project.description}</p>
      <div className={styles.meta}>
        <span className={styles.langDot} style={{ background: project.languageColor }} />
        <span className={styles.lang}>{project.language}</span>
        <span className={styles.dot} />
        <span className={styles.files}>{project.files} files</span>
        <span className={styles.time}>{project.lastActive}</span>
      </div>
    </div>
  );
}
