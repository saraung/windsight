import { useCallback, useState } from 'react';
import type { AnalysisFiltersState } from '../config/analysis';
import { ForecastHistorySkeleton } from '../components/LoadingState';
import { useAsyncData } from '../hooks/useAsyncData';
import { getForecastHistory, type ForecastVintage } from '../services/api';

function formatDateTime(value: string | null): string {
  if (!value) return '—';
  return new Date(value).toLocaleString('en-GB', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function formatMw(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(1)} MW`;
}

function VintageList({
  title,
  description,
  items,
  tone,
  selected,
}: {
  title: string;
  description: string;
  items: ForecastVintage[];
  tone: 'success' | 'accent';
  selected: ForecastVintage | null;
}) {
  const color = tone === 'success' ? 'var(--success)' : 'var(--accent-strong)';

  return (
    <div className="surface overflow-hidden rounded-3xl">
      <div className="border-b border-[var(--border)] px-5 py-4">
        <p className="text-sm font-bold text-[var(--text)]">{title}</p>
        <p className="mt-1 text-xs text-[var(--text-muted)]">
          {items.length} publications. {description}
        </p>
      </div>
      {items.length === 0 ? (
        <p className="p-5 text-sm text-[var(--text-muted)]">No publications in this category.</p>
      ) : (
        <div className="max-h-96 overflow-y-auto p-3">
          {items.map((item) => {
            const isSelected =
              selected !== null &&
              selected.publish_time === item.publish_time &&
              selected.start_time === item.start_time;
            return (
              <div
                key={`${item.publish_time}-${item.start_time}-${item.generation_mw}`}
                className={`flex items-center justify-between gap-3 rounded-2xl px-3 py-3 ${
                  isSelected ? 'bg-[var(--brand-soft)]' : 'hover:bg-[var(--surface-muted)]'
                }`}
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-xs font-semibold text-[var(--text)]">
                      {formatDateTime(item.publish_time)}
                    </p>
                    {isSelected && (
                      <span className="rounded-full bg-[var(--brand)] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                        Selected
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-[10px] text-[var(--text-muted)]">
                    Lead {item.lead_time_hours === null ? '—' : `${item.lead_time_hours.toFixed(1)} h`}
                  </p>
                </div>
                <span className="shrink-0 text-sm font-bold" style={{ color }}>
                  {formatMw(item.generation_mw)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function ForecastHistory({ filters }: { filters: AnalysisFiltersState }) {
  const [delivery, setDelivery] = useState('2026-01-15T12:00');
  const requestKey = `${delivery}|${JSON.stringify(filters)}`;
  const loadHistory = useCallback(
    () => getForecastHistory(delivery, filters),
    [delivery, filters],
  );
  const { data, loading, error } = useAsyncData(requestKey, loadHistory);

  return (
    <section className="space-y-6" aria-busy={loading}>
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold text-[var(--brand)]">Publication trace</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-[var(--text)]">
            Forecast history
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-muted)]">
            Inspect every vintage available for one delivery hour. Eligible publications are at or
            before the cutoff; excluded publications are later and would introduce look-ahead bias.
          </p>
        </div>
        <label className="text-xs font-semibold text-[var(--text-muted)]">
          Delivery hour (UTC)
          <input
            type="datetime-local"
            value={delivery}
            onChange={(event) => setDelivery(event.target.value)}
            className="field mt-1.5 block w-full rounded-xl px-3 py-2 text-sm sm:w-64"
          />
        </label>
      </div>

      {loading && !data ? <ForecastHistorySkeleton /> : null}

      {error ? (
        <div className="rounded-3xl border border-[var(--danger)] bg-[var(--danger-soft)] p-6">
          <p className="text-sm font-bold text-[var(--danger)]">
            Unable to load forecast history
          </p>
          <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{error}</p>
          <p className="mt-2 text-xs leading-5 text-[var(--text-muted)]">
            The delivery hour and cutoff must be valid UTC timestamps. An absolute cutoff cannot be
            after the delivery hour.
          </p>
        </div>
      ) : null}

      {!error && !data && !loading ? (
        <div className="surface rounded-3xl p-6 text-sm text-[var(--text-muted)]">
          No forecast history was returned.
        </div>
      ) : null}

      {!error && data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="metric-card rounded-3xl p-5">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
                Eligible vintages
              </p>
              <p className="mt-3 text-3xl font-bold text-[var(--success)]">
                {data.eligible_vintages.length}
              </p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">Published before cutoff</p>
            </div>
            <div className="metric-card rounded-3xl p-5">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
                Excluded vintages
              </p>
              <p className="mt-3 text-3xl font-bold text-[var(--accent-strong)]">
                {data.excluded_vintages.length}
              </p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">Published after cutoff</p>
            </div>
            <div className="metric-card rounded-3xl p-5">
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
                Decision cutoff
              </p>
              <p className="mt-3 text-sm font-bold text-[var(--brand)]">
                {formatDateTime(data.cutoff)}
              </p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                {data.cutoff_mode === 'absolute' ? 'Absolute timestamp' : data.cutoff_label}
              </p>
            </div>
          </div>

          <div className="surface rounded-3xl p-5 sm:p-6">
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
              <div>
                <p className="text-sm font-bold text-[var(--text)]">Selected forecast vintage</p>
                <p className="mt-1 max-w-2xl text-xs leading-5 text-[var(--text-muted)]">
                  {data.cutoff_description}
                </p>
              </div>
              <span className="shrink-0 rounded-full bg-[var(--success-soft)] px-3 py-1.5 text-xs font-bold text-[var(--success)]">
                Selected by backend
              </span>
            </div>
            {data.selected ? (
              <div className="mt-6 grid gap-4 sm:grid-cols-4">
                <Detail label="Publish time" value={formatDateTime(data.selected.publish_time)} />
                <Detail label="Delivery start" value={formatDateTime(data.selected.start_time)} />
                <Detail label="Generation" value={formatMw(data.selected.generation_mw)} />
                <Detail
                  label="Lead time"
                  value={
                    data.selected.lead_time_hours === null
                      ? '—'
                      : `${data.selected.lead_time_hours.toFixed(1)} h`
                  }
                />
              </div>
            ) : (
              <p className="mt-6 text-sm leading-6 text-[var(--text-muted)]">
                No eligible forecast vintage exists for this delivery hour. That is a missing
                forecast, not a zero forecast, and it is excluded from accuracy metrics.
              </p>
            )}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <VintageList
              title="Eligible publications"
              description="These could have been used at decision time."
              items={data.eligible_vintages}
              tone="success"
              selected={data.selected}
            />
            <VintageList
              title="Excluded publications"
              description="These were published later and are not used."
              items={data.excluded_vintages}
              tone="accent"
              selected={null}
            />
          </div>

          <div className="surface-muted rounded-3xl p-5">
            <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
              Reading this view
            </p>
            <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
              The selected vintage is the latest publication at or before the cutoff. The eligible
              count excludes later revisions, even when a later revision would have been more
              accurate. This is deliberate: the evaluation should reflect what a trader could
              actually know.
            </p>
          </div>
        </>
      ) : null}
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-[var(--surface-muted)] p-4">
      <p className="text-xs text-[var(--text-muted)]">{label}</p>
      <p className="mt-2 break-words text-sm font-bold text-[var(--text)]">{value}</p>
    </div>
  );
}
