import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeBlock from './CodeBlock';
import styles from './Message.module.css';

function SourceChip({ source, index, active, onClick }) {
  const name = source?.source || source?.filename || `Source ${index + 1}`;
  const short = name.split('/').pop().split('\\').pop();
  return (
    <span
      className={`${styles.sourceChip} ${active ? styles.sourceChipActive : ''}`}
      onClick={() => onClick(index)}
      title={name}
    >
      [{index + 1}] {short}
    </span>
  );
}

export default function Message({ message, activeSourceIdx, onSourceClick }) {
  if (message.role === 'user') {
    return (
      <div className={styles.messageWrap}>
        <div className={styles.userWrap}>
          <div className={styles.userBubble}>{message.content}</div>
          <div className={styles.userAvatar}>A</div>
        </div>
        <div className={styles.timestampUser}>{message.timestamp}</div>
      </div>
    );
  }

  return (
    <div className={styles.messageWrap}>
      <div className={styles.assistantWrap}>
        <div className={styles.aiIcon}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>

        <div className={styles.assistantCard}>
          <div className={styles.markdown}>
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  const lang = match ? match[1] : '';
                  const code = String(children).replace(/\n$/, '');
                  if (!inline && (lang || code.includes('\n'))) {
                    return <CodeBlock code={code} language={lang} />;
                  }
                  return <code className={className} {...props}>{children}</code>;
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Real sources from API */}
          {message.sources && message.sources.length > 0 && (
            <div className={styles.citationRow}>
              <span className={styles.citationLabel}>Sources:</span>
              {message.sources.map((src, i) => (
                <SourceChip
                  key={i}
                  source={src}
                  index={i}
                  active={activeSourceIdx === i}
                  onClick={onSourceClick}
                />
              ))}
            </div>
          )}
        </div>
      </div>
      <div className={styles.timestamp}>{message.timestamp}</div>
    </div>
  );
}
