import { Database, FileText, Layers, Clock } from 'lucide-react';
import styles from './StatsBar.module.css';

function fmt(n) {
  if (n == null) return '—';
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return String(n);
}

function fmtUptime(s) {
  if (s == null) return '—';
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

export default function StatsBar({ stats, loading }) {
  if (loading && !stats) {
    return (
      <div className={styles.bar}>
        <span className={styles.loading}>Loading system stats…</span>
      </div>
    );
  }

  const t = stats?.telemetry || {};
  const online = stats?.status === 'healthy';

  return (
    <div className={styles.bar}>
      <div className={styles.stat}>
        <div className={styles.statIcon}><FileText size={16} /></div>
        <div className={styles.statInfo}>
          <div className={styles.statValue}>{fmt(t.total_documents)}</div>
          <div className={styles.statLabel}>Documents</div>
        </div>
      </div>

      <div className={styles.stat}>
        <div className={styles.statIcon}><Layers size={16} /></div>
        <div className={styles.statInfo}>
          <div className={styles.statValue}>{fmt(t.total_chunks)}</div>
          <div className={styles.statLabel}>Chunks Indexed</div>
        </div>
      </div>

      <div className={styles.stat}>
        <div className={styles.statIcon}><Database size={16} /></div>
        <div className={styles.statInfo}>
          <div className={styles.statValue}>{fmt(t.indexed_vectors)}</div>
          <div className={styles.statLabel}>Vectors</div>
        </div>
      </div>

      <div className={styles.stat}>
        <div className={styles.statIcon}><Clock size={16} /></div>
        <div className={styles.statInfo}>
          <div className={styles.statValue}>{fmtUptime(stats?.uptime_seconds)}</div>
          <div className={styles.statLabel}>Uptime</div>
        </div>
      </div>

      <div className={styles.statusDot}>
        <span className={`${styles.dot} ${!online ? styles.offline : ''}`} />
        {online ? 'Backend healthy' : 'Backend offline'}
      </div>
    </div>
  );
}
