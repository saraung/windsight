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

  let label = 'Checking data';
  let detail = 'Fetching source status.';
  let tone = 'muted';

  if (error) {
    label = 'Data status unavailable';
    detail = 'Analysis requests may still work.';
    tone = 'warning';
  } else if (status) {
    label = anyStale ? 'Data stale' : allCached ? 'Data cached' : 'Data pending';
    detail = sources.map(sourceLabel).join(' · ');
    tone = anyStale ? 'warning' : allCached ? 'success' : 'muted';
  }

  const toneClass = {
    success: 'border-[var(--success)] bg-[var(--success-soft)] text-[var(--success)]',
    warning: 'border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent-strong)]',
    muted: 'border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-muted)]',
  }[tone];

  return (
    <div
      className={`flex items-center gap-2 rounded-full border px-2.5 py-1.5 text-[11px] font-semibold ${toneClass}`}
      role="status"
      aria-live="polite"
      aria-label={`${label}. ${detail}`}
      title={detail}
    >
      <span className="inline-block h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {loading && !status ? 'Checking data' : label}
    </div>
  );
}
