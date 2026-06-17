import { useEffect, useMemo, useState } from 'react';
import type { GaiaState, Talisman } from '../shared/gaia-state';

const API_BASE = '';

export function useGaiaState(pollMs = 30000) {
  const [state, setState] = useState<GaiaState | null>(null);
  const [talismans, setTalismans] = useState<Talisman[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setError(null);
      const [stateRes, talismansRes] = await Promise.all([
        fetch(`${API_BASE}/gaia/state`),
        fetch(`${API_BASE}/gaia/talismans`),
      ]);
      if (!stateRes.ok) throw new Error(`state request failed: ${stateRes.status}`);
      if (!talismansRes.ok) throw new Error(`talisman request failed: ${talismansRes.status}`);
      const stateJson = await stateRes.json();
      const talismanJson = await talismansRes.json();
      setState(stateJson);
      setTalismans(talismanJson);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown GAIAState error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, pollMs);
    return () => window.clearInterval(id);
  }, [pollMs]);

  const activeTalismans = useMemo(
    () => talismans.filter((t) => t.status === 'active'),
    [talismans]
  );

  return {
    state,
    talismans,
    activeTalismans,
    loading,
    error,
    refresh,
  };
}
