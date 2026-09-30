/**
 * src/hooks/useSearch.js
 * POST /search — semantic search across indexed knowledge base.
 */
import { useState, useCallback } from 'react';
import { searchCode } from '../api/client';

export function useSearch() {
  const [results, setResults] = useState([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (q) => {
    if (!q.trim()) return;
    setQuery(q);
    setLoading(true);
    setError(null);
    try {
      const data = await searchCode(q);
      setResults(data.results || []);
    } catch (err) {
      setError(err.message);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults([]);
    setQuery('');
    setError(null);
  }, []);

  return { results, query, loading, error, search, clear };
}
