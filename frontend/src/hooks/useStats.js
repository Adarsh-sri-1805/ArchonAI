/**
 * src/hooks/useStats.js
 * Polls GET /stats on mount and on demand.
 */
import { useState, useEffect, useCallback } from 'react';
import { getStats } from '../api/client';

export function useStats(pollIntervalMs = 15000) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch_ = useCallback(async () => {
    try {
      const data = await getStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch_();
    const id = setInterval(fetch_, pollIntervalMs);
    return () => clearInterval(id);
  }, [fetch_, pollIntervalMs]);

  return { stats, loading, error, refetch: fetch_ };
}
