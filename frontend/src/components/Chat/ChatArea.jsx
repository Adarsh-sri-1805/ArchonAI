import { useEffect, useRef } from 'react';
import Message from './Message';
import InputBar from '../UI/InputBar';
import styles from './ChatArea.module.css';

const SUGGESTIONS = [
  'How does the retrieval pipeline work?',
  'Explain the chunking strategy',
  'What LLM providers are supported?',
  'Walk me through the indexing flow',
];

export default function ChatArea({ messages, loading, error, onSend, activeSourceIdx, onSourceClick }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className={styles.chatArea}>
      <div className={styles.thread}>
        {messages.length === 0 ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary-hover)" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h2 className={styles.emptyTitle}>Ask Archon anything</h2>
            <p className={styles.emptySubtitle}>
              Semantically search your indexed codebase, get explanations, trace dependencies, and more.
            </p>
            <div className={styles.suggestions}>
              {SUGGESTIONS.map((s) => (
                <button key={s} className={styles.suggestion} onClick={() => onSend(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className={styles.threadInner}>
            {messages.map((msg, i) => (
              <Message
                key={msg.id}
                message={msg}
                activeSourceIdx={activeSourceIdx}
                onSourceClick={onSourceClick}
              />
            ))}

            {loading && (
              <div className={styles.typingWrap}>
                <div className={styles.typingIcon}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
                    <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                    <path d="M2 17l10 5 10-5"/>
                    <path d="M2 12l10 5 10-5"/>
                  </svg>
                </div>
                <div className={styles.typingCard}>
                  <span className={styles.dot} />
                  <span className={styles.dot} />
                  <span className={styles.dot} />
                </div>
              </div>
            )}

            {error && (
              <div className={styles.errorBanner}>
                ⚠ {error}
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <InputBar onSend={onSend} disabled={loading} />
    </div>
  );
}
