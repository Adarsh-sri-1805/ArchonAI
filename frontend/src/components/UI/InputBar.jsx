import { useRef, useState } from 'react';
import { Paperclip, Code2, ArrowUp } from 'lucide-react';
import styles from './InputBar.module.css';

export default function InputBar({ onSend }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleInput = (e) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 200) + 'px';
  };

  return (
    <div className={styles.wrap}>
      <div className={styles.container}>
        <textarea
          ref={textareaRef}
          className={styles.textarea}
          placeholder="Ask anything about your codebase…"
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          rows={1}
        />
        <div className={styles.actions}>
          <button className={styles.actionBtn} title="Attach file">
            <Paperclip size={15} />
          </button>
          <button className={styles.actionBtn} title="Insert code">
            <Code2 size={15} />
          </button>
          <button
            className={styles.sendBtn}
            onClick={handleSend}
            disabled={!value.trim()}
            title="Send (Enter)"
          >
            <ArrowUp size={15} strokeWidth={2.5} />
          </button>
        </div>
      </div>
      <div className={styles.hint}>
        <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
      </div>
    </div>
  );
}
