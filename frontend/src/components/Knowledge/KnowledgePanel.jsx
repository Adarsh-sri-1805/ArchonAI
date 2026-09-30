import { BookOpen, FileCode, FolderGit2, Inbox } from 'lucide-react';
import UploadZone from './UploadZone';
import GithubIngest from './GithubIngest';
import StatsBar from './StatsBar';
import styles from './KnowledgePanel.module.css';

function getDocIcon(doc) {
  return doc.type === 'repository' ? FolderGit2 : FileCode;
}

export default function KnowledgePanel({ stats, statsLoading, onIngestSuccess }) {
  const documents = stats?.documents || [];

  return (
    <div className={styles.panel}>
      <StatsBar stats={stats} loading={statsLoading} />

      <div className={styles.scrollArea}>
        <div className={styles.pageHeader}>
          <h1 className={styles.pageTitle}>Knowledge Base</h1>
          <p className={styles.pageSub}>
            Index files or repositories to make them searchable and available in chat.
          </p>
        </div>

        {/* Ingest grid */}
        <div className={styles.grid}>
          <UploadZone onSuccess={onIngestSuccess} />
          <GithubIngest onSuccess={onIngestSuccess} />
        </div>

        {/* Documents list */}
        <div className={styles.sectionTitle}>
          <BookOpen size={16} />
          Indexed Documents
          {documents.length > 0 && (
            <span className={styles.badge}>{documents.length}</span>
          )}
        </div>

        {documents.length === 0 ? (
          <div className={styles.emptyDocs}>
            <Inbox size={36} color="var(--border-hover)" />
            <div className={styles.emptyDocsTitle}>No documents indexed yet</div>
            <div className={styles.emptyDocsSub}>
              Upload a file or index a GitHub repository above to get started.
              Once indexed, you can ask questions about your code in the Chat view.
            </div>
          </div>
        ) : (
          <div className={styles.docList}>
            {documents.map((doc) => {
              const Icon = getDocIcon(doc);
              return (
                <div key={doc.id} className={styles.docItem}>
                  <div className={styles.docIcon}><Icon size={16} /></div>
                  <span className={styles.docName}>{doc.name}</span>
                  <span className={styles.docMeta}>{doc.chunks} chunks</span>
                  <span className={styles.docStatusBadge}>{doc.status}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
