import { FileCode } from 'lucide-react';
import styles from './CitationChip.module.css';
import { retrievedFiles } from '../../data/mockData';

export default function CitationChip({ fileId, activeFileId, onFileClick }) {
  const file = retrievedFiles.find(f => f.id === fileId);
  if (!file) return null;

  return (
    <span
      className={`${styles.chip} ${activeFileId === fileId ? styles.active : ''}`}
      onClick={() => onFileClick(fileId)}
      title={file.filepath}
    >
      <FileCode size={10} className={styles.icon} />
      {file.filename}:{file.lines}
    </span>
  );
}
