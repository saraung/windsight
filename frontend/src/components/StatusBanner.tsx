import type { DataStatusResponse, SourceStatus } from '../services/api';

interface StatusBannerProps {
  status: DataStatusResponse | null;
  loading: boolean;
  error: string | null;
}

function sourceLabel(source: SourceStatus): string {
  if (!source.cached) return `${source.source}: not cached`;
  if (source.stale) return `${source.source}: stale`;
  if (source.age_hours === null) return `${source.source}: cached`;
  if (source.age_hours < 1) return `${source.source}: cached <1h ago`;
  return `${source.source}: cached ${Math.round(source.age_hours)}h ago`;
}

export default function StatusBanner({ status, loading, error }: StatusBannerProps) {
  const sources = status ? Object.values(status.sources) : [];
  const allCached = sources.length > 0 && sources.every((source) => source.cached);
  const anyStale = sources.some((source) => source.stale);

  let headline = 'Checking the backend cache';
  let detail = 'Status is requested directly from the API, not assumed.';
  let tone = 'muted';

  if (error) {
    headline = 'Cache status unavailable';
    detail = 'Analysis requests may still work. The backend did not return status metadata.';
    tone = 'warning';
  } else if (status) {
    headline = allCached ? 'Backend cache available' : 'Backend cache not yet populated';
    detail = sources.map(sourceLabel).join('  /  ');
    tone = anyStale ? 'warning' : allCached ? 'success' : 'muted';
  }

  const toneClass = {
    success: 'border-[var(--success)] bg-[var(--success-soft)] text-[var(--success)]',
    warning: 'border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent-strong)]',
    muted: 'border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-muted)]',
  }[tone];

  return (
    <div className="space-y-3">
      <div
        className={`flex flex-col gap-2 rounded-2xl border px-4 py-3 sm:flex-row sm:items-center sm:justify-between ${toneClass}`}
        role="status"
        aria-live="polite"
      >
        <div className="flex items-center gap-2 text-xs font-semibold">
          <span className="inline-block h-2 w-2 rounded-full bg-current" aria-hidden="true" />
          {loading && !status ? 'Checking the backend cache' : headline}
        </div>
        <p className="text-xs leading-5 opacity-90">
          {loading && !status ? 'Status is requested directly from the API, not assumed.' : detail}
        </p>
      </div>
      <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-muted)]">
          Scope and limitations
        </p>
        <p className="mt-1.5 text-xs leading-5 text-[var(--text-muted)]">
          FUELHH reports transmission-metered wind output, while WINDFOR forecasts total wind. This
          is the closest public forecast/actual pair available, but it is not an exact like-for-like
          settlement calculation. Demand, thermal procurement, and imbalance prices are out of
          scope.
        </p>
      </div>
    </div>
  );
}
