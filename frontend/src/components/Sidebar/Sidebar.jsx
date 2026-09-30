import { useState } from 'react';
import {
  PanelLeft, Plus, FolderOpen, BookOpen,
  MessageSquare, Settings, Trash2
} from 'lucide-react';
import styles from './Sidebar.module.css';

const navItems = [
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
  { id: 'chat',      label: 'Chat',      icon: MessageSquare },
  { id: 'settings',  label: 'Settings',  icon: Settings },
];

export default function Sidebar({
  collapsed, onToggle,
  activeView, onViewChange,
  sessions, activeChatId, onChatSelect, onNewChat, onDeleteChat,
}) {
  return (
    <aside className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}>
      {/* Logo row */}
      <div className={styles.logoRow}>
        <div className={styles.logoWrap}>
          <div className={styles.logoIcon}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className={styles.logoText}>Archon</span>
        </div>
        <button className={styles.collapseBtn} onClick={onToggle} title="Toggle sidebar">
          <PanelLeft size={18} />
        </button>
      </div>

      {/* New Chat button */}
      <div className={styles.newChatWrap}>
        <button className={styles.newChatBtn} onClick={onNewChat}>
          <Plus size={17} strokeWidth={2.5} />
          <span className={styles.newChatLabel}>New Chat</span>
        </button>
      </div>

      {/* Nav */}
      <nav className={styles.nav}>
        {navItems.map(({ id, label, icon: Icon }) => (
          <div
            key={id}
            className={`${styles.navItem} ${activeView === id ? styles.active : ''}`}
            onClick={() => onViewChange(id)}
            title={collapsed ? label : undefined}
          >
            <Icon size={17} strokeWidth={2} />
            <span className={styles.navLabel}>{label}</span>
          </div>
        ))}
      </nav>

      <div className={styles.divider} />

      {/* Chat history */}
      <div className={styles.scrollArea}>
        {sessions.length > 0 && (
          <>
            <div className={styles.sectionLabel}>Recent Chats</div>
            <div className={styles.chatList}>
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className={`${styles.chatItem} ${activeChatId === s.id ? styles.active : ''}`}
                  onClick={() => { onChatSelect(s.id); onViewChange('chat'); }}
                >
                  <span className={styles.chatTitle}>{s.title || 'New Chat'}</span>
                  <div className={styles.chatMeta}>
                    <span>{s.messages?.length ?? 0} messages</span>
                    {!collapsed && (
                      <button
                        className={styles.deleteBtn}
                        onClick={(e) => { e.stopPropagation(); onDeleteChat(s.id); }}
                        title="Delete chat"
                      >
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* User row */}
      <div className={styles.bottomNav}>
        <div className={styles.userRow}>
          <div className={styles.avatar}>A</div>
          <div className={styles.userInfo}>
            <div className={styles.userName}>Adarsh</div>
            <div className={styles.userEmail}>adarsh@archon.dev</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
