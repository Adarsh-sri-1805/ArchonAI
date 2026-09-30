import { useEffect, useRef, useState } from 'react';
import hljs from 'highlight.js';
import { Copy, Check } from 'lucide-react';
import styles from './CodeBlock.module.css';

export default function CodeBlock({ code, language }) {
  const codeRef = useRef(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (codeRef.current) {
      hljs.highlightElement(codeRef.current);
    }
  }, [code]);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <span className={styles.lang}>{language || 'code'}</span>
        <button
          className={`${styles.copyBtn} ${copied ? styles.copied : ''}`}
          onClick={handleCopy}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className={styles.pre}>
        <code ref={codeRef} className={`${styles.code} language-${language || 'text'}`}>
          {code}
        </code>
      </pre>
    </div>
  );
}
