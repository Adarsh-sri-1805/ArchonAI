import { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar/Sidebar';
import TopBar from './components/UI/TopBar';
import ChatArea from './components/Chat/ChatArea';
import ContextPanel from './components/Context/ContextPanel';
import KnowledgePanel from './components/Knowledge/KnowledgePanel';
import SettingsPanel from './components/Settings/SettingsPanel';
import SearchModal from './components/UI/SearchModal';
import styles from './App.module.css';
import { useChat } from './hooks/useChat';
import { useStats } from './hooks/useStats';

export default function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [contextOpen, setContextOpen] = useState(true);
  const [activeView, setActiveView] = useState('knowledge'); // 'knowledge' | 'chat' | 'settings'
  const [searchOpen, setSearchOpen] = useState(false);
  const [activeSourceIdx, setActiveSourceIdx] = useState(null);

  const { sessions, activeChatId, messages, loading, error, newChat, selectChat, deleteChat, send } = useChat();
  const { stats, loading: statsLoading, refetch: refetchStats } = useStats();

  // ⌘K / Ctrl+K shortcut
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen((p) => !p);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const handleNewChat = useCallback(() => {
    newChat();
    setActiveView('chat');
    setActiveSourceIdx(null);
  }, [newChat]);

  const handleSelectChat = useCallback((id) => {
    selectChat(id);
    setActiveView('chat');
    setActiveSourceIdx(null);
  }, [selectChat]);

  const handleSend = useCallback(async (text) => {
    setActiveSourceIdx(null);
    await send(text);
    setContextOpen(true); // auto-open context panel when sending
  }, [send]);

  const handleSourceClick = useCallback((idx) => {
    setActiveSourceIdx(idx);
    setContextOpen(true);
  }, []);

  const handleSearchResult = useCallback((result) => {
    // Open a new chat with the search result as context
    handleNewChat();
    const filename = result.source || result.filename || 'result';
    send(`Tell me about this code from ${filename}:\n\n${result.excerpt}`);
  }, [handleNewChat, send]);

  const handleIngestSuccess = useCallback(() => {
    refetchStats();
  }, [refetchStats]);

  const handleSettingsUpdated = useCallback(() => {
    refetchStats();
  }, [refetchStats]);

  // Gather sources from the last assistant message
  const lastAiMsg = [...messages].reverse().find((m) => m.role === 'assistant');
  const currentSources = lastAiMsg?.sources || [];

  // Model info from stats
  const modelInfo = stats?.system
    ? `${stats.system.chat_provider} · ${stats.system.embedding_model}`
    : null;

  const chatTitle = activeChatId
    ? sessions.find((s) => s.id === activeChatId)?.title || 'Chat'
    : 'New Chat';

  const viewTitle = activeView === 'chat'
    ? chatTitle
    : activeView === 'settings'
    ? 'Settings'
    : 'Knowledge Base';

  return (
    <div className={styles.layout}>
      {/* Left sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((p) => !p)}
        activeView={activeView}
        onViewChange={setActiveView}
        sessions={sessions}
        activeChatId={activeChatId}
        onChatSelect={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={deleteChat}
      />

      {/* Center */}
      <div className={styles.center}>
        <TopBar
          title={viewTitle}
          modelInfo={modelInfo}
          contextOpen={contextOpen}
          onContextToggle={() => setContextOpen((p) => !p)}
          onSearchOpen={() => setSearchOpen(true)}
        />

        {activeView === 'knowledge' ? (
          <KnowledgePanel
            stats={stats}
            statsLoading={statsLoading}
            onIngestSuccess={handleIngestSuccess}
          />
        ) : activeView === 'settings' ? (
          <SettingsPanel
            onSettingsUpdated={handleSettingsUpdated}
          />
        ) : (
          <ChatArea
            messages={messages}
            loading={loading}
            error={error}
            onSend={handleSend}
            activeSourceIdx={activeSourceIdx}
            onSourceClick={handleSourceClick}
          />
        )}
      </div>

      {/* Right context panel — only shown in chat view */}
      {activeView === 'chat' && (
        <ContextPanel
          open={contextOpen}
          onClose={() => setContextOpen(false)}
          sources={currentSources}
          activeSourceIdx={activeSourceIdx}
          onSourceClick={setActiveSourceIdx}
        />
      )}

      {/* ⌘K Search Modal */}
      {searchOpen && (
        <SearchModal
          onClose={() => setSearchOpen(false)}
          onResultClick={handleSearchResult}
        />
      )}
    </div>
  );
}
