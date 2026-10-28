import { useEffect, useState } from 'react';
import { getForecastHistory, type ForecastHistoryResponse } from '../services/api';
import { ForecastHistorySkeleton } from '../components/LoadingState';

const DELIVERY_TIME = '2026-01-15T12:00Z';

export default function ForecastHistory() {
  const [data, setData] = useState<ForecastHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getForecastHistory(DELIVERY_TIME)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load forecast history');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <ForecastHistorySkeleton />;
  if (error || !data) return <section className="rounded-3xl border border-[var(--danger)] bg-[var(--danger-soft)] p-6 text-sm text-[var(--danger)]">{error ?? 'No forecast history returned'}</section>;

  const selected = data.selected;

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-[var(--brand)]">Publication trace</p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight text-[var(--text)]">Forecast history</h2>
        <p className="mt-3 text-sm text-[var(--text-muted)]">
          Inspect every vintage available for delivery at {data.delivery_time} UTC.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="metric-card rounded-3xl p-5"><p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">Eligible vintages</p><p className="mt-3 text-3xl font-bold text-[var(--success)]">{data.eligible_vintages.length}</p><p className="mt-1 text-xs text-[var(--text-subtle)]">Published before cutoff</p></div>
        <div className="metric-card rounded-3xl p-5"><p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">Excluded vintages</p><p className="mt-3 text-3xl font-bold text-[var(--accent)]">{data.excluded_vintages.length}</p><p className="mt-1 text-xs text-[var(--text-subtle)]">Published after cutoff</p></div>
        <div className="metric-card rounded-3xl p-5"><p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">Decision cutoff</p><p className="mt-3 text-sm font-bold text-[var(--brand)]">{data.cutoff}</p><p className="mt-1 text-xs text-[var(--text-subtle)]">Inclusive eligibility rule</p></div>
      </div>

      <div className="surface rounded-3xl p-5 sm:p-6">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
          <div>
            <p className="text-sm font-bold text-[var(--text)]">Selected forecast vintage</p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">The latest eligible publication at the configured cutoff.</p>
          </div>
          <span className="rounded-full bg-[var(--success-soft)] px-3 py-1.5 text-xs font-bold text-[var(--success)]">Selected by backend</span>
        </div>
        {selected ? (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <Detail label="Publish time" value={selected.publish_time} />
            <Detail label="Delivery start" value={selected.start_time} />
            <Detail label="Generation" value={selected.generation_mw === null ? '—' : `${selected.generation_mw.toFixed(1)} MW`} />
          </div>
        ) : <p className="mt-6 text-sm text-[var(--text-muted)]">No eligible forecast vintage found.</p>}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <VintageList title="Eligible publications" items={data.eligible_vintages} tone="success" />
        <VintageList title="Excluded publications" items={data.excluded_vintages} tone="accent" />
      </div>
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="rounded-2xl bg-[var(--surface-muted)] p-4"><p className="text-xs text-[var(--text-muted)]">{label}</p><p className="mt-2 break-all text-sm font-bold text-[var(--text)]">{value}</p></div>;
}

function VintageList({ title, items, tone }: { title: string; items: ForecastHistoryResponse['eligible_vintages']; tone: 'success' | 'accent' }) {
  const color = tone === 'success' ? 'var(--success)' : 'var(--accent)';
  return (
    <div className="surface overflow-hidden rounded-3xl">
      <div className="border-b border-[var(--border)] px-5 py-4"><p className="text-sm font-bold text-[var(--text)]">{title}</p><p className="mt-1 text-xs text-[var(--text-muted)]">{items.length} publications</p></div>
      <div className="max-h-80 overflow-y-auto p-3">
        {items.map((item) => <div key={`${item.publish_time}-${item.start_time}`} className="flex items-center justify-between gap-3 rounded-2xl px-3 py-3 transition hover:bg-[var(--surface-muted)]"><div className="min-w-0"><p className="truncate text-xs font-semibold text-[var(--text)]">{item.publish_time}</p><p className="mt-1 text-[10px] text-[var(--text-muted)]">Delivery {item.start_time}</p></div><span className="shrink-0 text-sm font-bold" style={{ color }}>{item.generation_mw === null ? '—' : `${item.generation_mw.toFixed(0)} MW`}</span></div>)}
      </div>
    </div>
  );
}
