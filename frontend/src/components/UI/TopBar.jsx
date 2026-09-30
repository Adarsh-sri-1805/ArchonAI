import { Search, ChevronDown, PanelRight, MoreHorizontal } from 'lucide-react';
import styles from './TopBar.module.css';

export default function TopBar({ title, modelInfo, contextOpen, onContextToggle, onSearchOpen }) {
  return (
    <div className={styles.topBar}>
      {/* Title / breadcrumb */}
      <div className={styles.titleArea}>
        <span className={styles.title}>{title || 'Archon'}</span>
      </div>

      {/* Search bar — opens modal on click */}
      <button className={styles.searchBar} onClick={onSearchOpen}>
        <Search size={16} color="var(--secondary)" />
        <span className={styles.searchPlaceholder}>Search codebase…</span>
        <span className={styles.searchShortcut}>⌘K</span>
      </button>

      {/* Right controls */}
      <div className={styles.controls}>
        {modelInfo && (
          <div className={styles.modelBadge}>
            <span className={styles.pulseDot} />
            {modelInfo}
          </div>
        )}
        <button
          className={styles.iconBtn}
          onClick={onContextToggle}
          title="Toggle context panel"
        >
          <PanelRight size={18} />
        </button>
        <button className={styles.iconBtn}>
          <MoreHorizontal size={18} />
        </button>
      </div>
    </div>
  );
}
