import { useEffect, useState } from 'react';
import { getOverview, type OverviewResponse } from '../services/api';
import { OverviewSkeleton } from '../components/LoadingState';

const DEFAULT_FROM = '2026-01-01';
const DEFAULT_TO = '2026-01-31';
const DEFAULT_CUTOFF = '2026-01-14T12:00';

function formatMw(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(1)} MW`;
}

function formatPct(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(1)}%`;
}

function StatCard({
  label,
  value,
  detail,
  accent = 'brand',
}: {
  label: string;
  value: string;
  detail: string;
  accent?: 'brand' | 'amber' | 'green';
}) {
  const accentClass = {
    brand: 'text-[var(--brand)]',
    amber: 'text-[var(--accent)]',
    green: 'text-[var(--success)]',
  }[accent];

  return (
    <div className="metric-card rounded-3xl p-5">
      <div className="relative z-10">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">{label}</p>
          <span className={`text-xl ${accentClass}`}>✦</span>
        </div>
        <p className={`mt-4 text-2xl font-bold tracking-tight ${accentClass}`}>{value}</p>
        <p className="mt-2 text-xs text-[var(--text-subtle)]">{detail}</p>
      </div>
    </div>
  );
}

export default function Overview() {
  const [from, setFrom] = useState(DEFAULT_FROM);
  const [to, setTo] = useState(DEFAULT_TO);
  const [cutoff, setCutoff] = useState(DEFAULT_CUTOFF);
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    getOverview(from, to, cutoff ? `${cutoff}:00Z` : undefined)
      .then((res) => {
        if (!cancelled) {
          setOverview(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load overview');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [from, to, cutoff]);

  if (loading) {
    return <OverviewSkeleton />;
  }

  if (error || !overview) {
    return <ErrorState message={error ?? 'No overview data returned'} />;
  }

  const metrics = overview.metrics;
  const coverage = overview.coverage;

  return (
    <section className="space-y-6">
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold text-[var(--brand)]">Decision intelligence</p>
          <h2 className="mt-2 max-w-2xl text-3xl font-bold tracking-tight text-[var(--text)] sm:text-4xl">
            How much can you trust the wind forecast?
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--text-muted)]">
            Review the latest eligible forecast vintage against measured generation for the selected delivery window.
          </p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-right shadow-sm">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--text-subtle)]">Analysis window</p>
          <p className="mt-1 text-sm font-semibold text-[var(--text)]">
            {overview.from_date} → {overview.to_date}
          </p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">All timestamps in UTC</p>
        </div>
      </div>

      <div className="surface rounded-3xl p-4 sm:p-5">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-sm font-bold text-[var(--text)]">Analysis controls</p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">Change the period or decision cutoff to recalculate every metric.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <label className="text-xs font-semibold text-[var(--text-muted)]">
              From
              <input type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="field mt-1.5 block w-full rounded-xl px-3 py-2 text-sm" />
            </label>
            <label className="text-xs font-semibold text-[var(--text-muted)]">
              To
              <input type="date" value={to} onChange={(e) => setTo(e.target.value)} className="field mt-1.5 block w-full rounded-xl px-3 py-2 text-sm" />
            </label>
            <label className="text-xs font-semibold text-[var(--text-muted)]">
              Decision cutoff
              <input type="datetime-local" value={cutoff} onChange={(e) => setCutoff(e.target.value)} className="field mt-1.5 block w-full rounded-xl px-3 py-2 text-sm" />
            </label>
          </div>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Matched intervals" value={`${overview.matched_pairs}`} detail={`of ${overview.delivery_intervals} delivery intervals`} accent="green" />
        <StatCard label="Mean absolute error" value={formatMw(metrics.mae)} detail="Average absolute forecast error" />
        <StatCard label="RMSE" value={formatMw(metrics.rmse)} detail="Penalizes larger misses more heavily" accent="amber" />
        <StatCard label="Forecast bias" value={formatMw(metrics.bias)} detail="Positive values indicate overforecasting" accent="brand" />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="surface rounded-3xl p-5 sm:p-6">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <p className="text-sm font-bold text-[var(--text)]">Forecast signal</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">A concise read on the selected forecast vintage.</p>
            </div>
            <span className="rounded-full bg-[var(--accent-soft)] px-3 py-1.5 text-xs font-bold text-[var(--accent)]">
              {formatPct(metrics.overforecast_percentage)} overforecast
            </span>
          </div>
          <div className="mt-7 flex items-end gap-3">
            <span className="text-5xl font-bold tracking-tight text-[var(--text)]">{metrics.n}</span>
            <span className="pb-1 text-sm text-[var(--text-muted)]">valid matched intervals</span>
          </div>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-[var(--text-muted)]">
            {metrics.n > 0
              ? `Across the selected window, the forecast averaged ${formatMw(metrics.bias)} versus actual generation.`
              : 'No matched delivery intervals were available for the selected period.'}
          </p>
        </div>

        <div className="surface rounded-3xl p-5 sm:p-6">
          <p className="text-sm font-bold text-[var(--text)]">Data coverage</p>
          <div className="mt-5 space-y-4">
            {[
              ['Matched pairs', coverage.matched_pairs, 'var(--success)'],
              ['Missing forecast', coverage.missing_forecast, 'var(--accent)'],
              ['Missing actual', coverage.missing_actual, 'var(--danger)'],
              ['Invalid records', coverage.invalid_forecast + coverage.invalid_actual, 'var(--text-subtle)'],
            ].map(([label, value, color]) => (
              <div key={label as string} className="flex items-center justify-between gap-4">
                <span className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color as string }} />
                  {label as string}
                </span>
                <span className="text-sm font-bold text-[var(--text)]">{value as number}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="surface-muted rounded-3xl p-5">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-subtle)]">Method note</p>
        <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
          Forecast error is calculated as forecast minus actual. The selected vintage is the latest publication available at or before the configured decision cutoff.
        </p>
      </div>
    </section>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <section className="rounded-3xl border border-[var(--danger)] bg-[var(--danger-soft)] p-6">
      <p className="text-sm font-bold text-[var(--danger)]">Unable to load analysis</p>
      <p className="mt-2 text-sm text-[var(--text-muted)]">{message}</p>
    </section>
  );
}
