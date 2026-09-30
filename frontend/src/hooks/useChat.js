/**
 * src/hooks/useChat.js
 * Manages chat sessions: history in localStorage, real /chat API calls.
 */
import { useState, useCallback } from 'react';
import { sendChat } from '../api/client';

const STORAGE_KEY = 'archon_chats';

function loadHistory() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveHistory(sessions) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

let _msgId = Date.now();
const uid = () => `m_${_msgId++}`;

export function useChat() {
  const [sessions, setSessions] = useState(loadHistory); // [{ id, title, messages: [] }]
  const [activeChatId, setActiveChatId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const activeSession = sessions.find((s) => s.id === activeChatId) || null;
  const messages = activeSession?.messages || [];

  const newChat = useCallback(() => {
    const id = `chat_${Date.now()}`;
    setSessions((prev) => {
      const next = [{ id, title: 'New Chat', messages: [] }, ...prev];
      saveHistory(next);
      return next;
    });
    setActiveChatId(id);
    setError(null);
    return id;
  }, []);

  const selectChat = useCallback((id) => {
    setActiveChatId(id);
    setError(null);
  }, []);

  const deleteChat = useCallback((id) => {
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id);
      saveHistory(next);
      return next;
    });
    setActiveChatId((prev) => (prev === id ? null : prev));
  }, []);

  const send = useCallback(
    async (text) => {
      setError(null);
      let chatId = activeChatId;

      // Auto-create session if none active
      if (!chatId) {
        chatId = `chat_${Date.now()}`;
        setSessions((prev) => {
          const next = [{ id: chatId, title: text.slice(0, 50), messages: [] }, ...prev];
          saveHistory(next);
          return next;
        });
        setActiveChatId(chatId);
      }

      const userMsg = {
        id: uid(),
        role: 'user',
        content: text,
        timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      };

      // Append user message immediately
      setSessions((prev) => {
        const next = prev.map((s) =>
          s.id === chatId
            ? {
                ...s,
                title: s.messages.length === 0 ? text.slice(0, 60) : s.title,
                messages: [...s.messages, userMsg],
              }
            : s
        );
        saveHistory(next);
        return next;
      });

      setLoading(true);
      try {
        const data = await sendChat(text);

        const aiMsg = {
          id: uid(),
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
        };

        setSessions((prev) => {
          const next = prev.map((s) =>
            s.id === chatId ? { ...s, messages: [...s.messages, aiMsg] } : s
          );
          saveHistory(next);
          return next;
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [activeChatId]
  );

  return {
    sessions,
    activeChatId,
    activeSession,
    messages,
    loading,
    error,
    newChat,
    selectChat,
    deleteChat,
    send,
  };
}
