import { useCallback } from 'react';
import type { AnalysisFiltersState } from '../config/analysis';
import { OverviewSkeleton } from '../components/LoadingState';
import { useAsyncData } from '../hooks/useAsyncData';
import { getOverview, type AccuracyMetrics } from '../services/api';

function formatMw(value: number | null): string {
  return value === null ? 'Not available' : `${value.toFixed(1)} MW`;
}

function formatPct(value: number | null): string {
  return value === null ? 'Not available' : `${value.toFixed(1)}%`;
}

function formatDateTime(value: string | null): string {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString('en-GB', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function interpretation(metrics: AccuracyMetrics): { headline: string; body: string } {
  if (metrics.n === 0 || metrics.bias === null) {
    return {
      headline: 'No usable matched intervals in this window.',
      body: 'Increase the date range, choose a later per-delivery cutoff, or inspect coverage to see whether forecasts or actuals are missing.',
    };
  }

  const direction =
    metrics.bias > 0
      ? `ran high by ${Math.abs(metrics.bias).toFixed(1)} MW on average`
      : metrics.bias < 0
        ? `ran low by ${Math.abs(metrics.bias).toFixed(1)} MW on average`
        : 'was centred on actual output on average';

  const spread =
    metrics.error_p10 !== null && metrics.error_p90 !== null
      ? `The central 80% of signed errors fell between ${metrics.error_p10.toFixed(1)} MW and ${metrics.error_p90.toFixed(1)} MW.`
      : 'Signed-error quantiles were not available.';

  return {
    headline: `The selected forecast ${direction}.`,
    body: `A typical hourly miss was ${formatMw(metrics.mae)}. ${spread} Positive values mean the forecast exceeded metered output.`,
  };
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
    amber: 'text-[var(--accent-strong)]',
    green: 'text-[var(--success)]',
  }[accent];

  return (
    <div className="metric-card rounded-3xl p-5">
      <div className="relative z-10">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
          {label}
        </p>
        <p className={`mt-4 text-2xl font-bold tracking-tight ${accentClass}`}>{value}</p>
        <p className="mt-2 text-xs leading-5 text-[var(--text-subtle)]">{detail}</p>
      </div>
    </div>
  );
}

export default function Overview({ filters }: { filters: AnalysisFiltersState }) {
  const requestKey = JSON.stringify(filters);
  const loadOverview = useCallback(
    () => getOverview(filters.from, filters.to, filters),
    [filters],
  );
  const { data: overview, loading, error } = useAsyncData(requestKey, loadOverview);

  if (loading && !overview) return <OverviewSkeleton />;

  if (error) {
    return (
      <section className="rounded-3xl border border-[var(--danger)] bg-[var(--danger-soft)] p-6">
        <p className="text-sm font-bold text-[var(--danger)]">Unable to load the overview</p>
        <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{error}</p>
        <p className="mt-2 text-xs leading-5 text-[var(--text-muted)]">
          Check that the selected period is valid. An absolute cutoff must be at or before the first
          delivery day at 00:00 UTC.
        </p>
      </section>
    );
  }

  if (!overview) {
    return (
      <section className="surface rounded-3xl p-6 text-sm text-[var(--text-muted)]">
        No overview data was returned.
      </section>
    );
  }

  const metrics = overview.metrics;
  const coverage = overview.coverage;
  const reading = interpretation(metrics);
  const coveragePct = coverage.coverage_percentage ?? 0;
  const daily = [...overview.daily].sort((a, b) => a.date.localeCompare(b.date));

  return (
    <section className="space-y-6">
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold text-[var(--brand)]">Decision snapshot</p>
          <h2 className="mt-2 max-w-2xl text-3xl font-bold tracking-tight text-[var(--text)] sm:text-4xl">
            How reliable was the wind forecast?
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--text-muted)]">
            The latest vintage available at the decision cutoff is compared with hourly metered wind
            output. Use the error range and bias to judge the forecast before committing to a trade.
          </p>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-right shadow-sm">
          <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--text-muted)]">
            Delivery window
          </p>
          <p className="mt-1 text-sm font-semibold text-[var(--text)]">
            {overview.from_date} to {overview.to_date}
          </p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            {overview.delivery_intervals} hourly intervals
          </p>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="surface rounded-3xl p-5 sm:p-6">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
                What this means for a trader
              </p>
              <h3 className="mt-2 text-xl font-bold tracking-tight text-[var(--text)]">
                {reading.headline}
              </h3>
            </div>
            <span className="shrink-0 rounded-full bg-[var(--brand-soft)] px-3 py-1.5 text-xs font-bold text-[var(--brand-strong)]">
              {metrics.n} valid pairs
            </span>
          </div>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[var(--text-muted)]">
            {reading.body}
          </p>
          <p className="mt-4 rounded-2xl border border-[var(--accent)] bg-[var(--accent-soft)] p-3 text-xs leading-5 text-[var(--text)]">
            <span className="font-bold">Scope caveat:</span> WINDFOR covers total wind, while
            FUELHH WIND reports transmission-metered output. Part of the measured gap is a
            measurement-scope difference, not forecast error. Treat the direction and the change
            across cutoffs as the signal, not the absolute bias alone.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-[var(--surface-muted)] p-4">
              <p className="text-xs text-[var(--text-muted)]">Overforecast frequency</p>
              <p className="mt-2 text-2xl font-bold text-[var(--accent-strong)]">
                {formatPct(metrics.overforecast_percentage)}
              </p>
              <p className="mt-1 text-xs text-[var(--text-subtle)]">
                Share of hours with forecast above actual
              </p>
            </div>
            <div className="rounded-2xl bg-[var(--surface-muted)] p-4">
              <p className="text-xs text-[var(--text-muted)]">Underforecast frequency</p>
              <p className="mt-2 text-2xl font-bold text-[var(--brand)]">
                {formatPct(metrics.underforecast_percentage)}
              </p>
              <p className="mt-1 text-xs text-[var(--text-subtle)]">
                Share of hours with forecast below actual
              </p>
            </div>
          </div>
        </div>

        <div className="surface rounded-3xl p-5 sm:p-6">
          <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
            Decision cutoff
          </p>
          <p className="mt-3 text-lg font-bold text-[var(--text)]">{overview.cutoff_label}</p>
          <p className="mt-2 text-xs leading-5 text-[var(--text-muted)]">
            {overview.cutoff_description}
          </p>
          <dl className="mt-5 space-y-3 border-t border-[var(--border)] pt-4 text-xs">
            <div className="flex items-start justify-between gap-4">
              <dt className="text-[var(--text-muted)]">Mode</dt>
              <dd className="text-right font-semibold text-[var(--text)]">
                {overview.cutoff_mode === 'absolute' ? 'One absolute timestamp' : 'Per delivery'}
              </dd>
            </div>
            <div className="flex items-start justify-between gap-4">
              <dt className="text-[var(--text-muted)]">Earliest cutoff</dt>
              <dd className="text-right font-semibold text-[var(--text)]">
                {formatDateTime(overview.cutoff_start)}
              </dd>
            </div>
            <div className="flex items-start justify-between gap-4">
              <dt className="text-[var(--text-muted)]">Latest cutoff</dt>
              <dd className="text-right font-semibold text-[var(--text)]">
                {formatDateTime(overview.cutoff_end)}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Typical miss (MAE)"
          value={formatMw(metrics.mae)}
          detail="Average absolute forecast error per matched hour"
          accent="green"
        />
        <StatCard
          label="Average bias"
          value={formatMw(metrics.bias)}
          detail="Positive means the forecast ran high; includes a measurement-scope gap"
          accent="brand"
        />
        <StatCard
          label="Central error range"
          value={
            metrics.error_p10 === null || metrics.error_p90 === null
              ? 'Not available'
              : `${metrics.error_p10.toFixed(0)} to ${metrics.error_p90.toFixed(0)} MW`
          }
          detail="P10 to P90 of signed errors (forecast minus actual)"
          accent="amber"
        />
        <StatCard
          label="Matched intervals"
          value={`${overview.matched_pairs}`}
          detail={`${formatPct(coveragePct)} of ${overview.delivery_intervals} expected hours`}
          accent="green"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
        <div className="surface rounded-3xl p-5 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-bold text-[var(--text)]">Data coverage</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                Missing values are never imputed as zero.
              </p>
            </div>
            <span className="text-sm font-bold text-[var(--brand)]">{formatPct(coveragePct)}</span>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-[var(--surface-muted)]">
            <div
              className="h-full rounded-full bg-[var(--success)]"
              style={{ width: `${Math.min(100, Math.max(0, coveragePct))}%` }}
            />
          </div>
          <dl className="mt-5 space-y-3 text-xs">
            {[
              ['Matched forecast and actual', coverage.matched_pairs],
              ['Missing forecast', coverage.missing_forecast],
              ['Missing actual', coverage.missing_actual],
              ['Missing both', coverage.missing_both],
              ['Incomplete half-hour actual', coverage.incomplete_actual],
              ['Invalid forecast record', coverage.invalid_forecast],
            ].map(([label, value]) => (
              <div key={label as string} className="flex items-center justify-between gap-4">
                <dt className="text-[var(--text-muted)]">{label as string}</dt>
                <dd className="font-bold text-[var(--text)]">{value as number}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="surface overflow-hidden rounded-3xl">
          <div className="flex items-start justify-between gap-3 border-b border-[var(--border)] px-5 py-4">
            <div>
              <p className="text-sm font-bold text-[var(--text)]">Daily accuracy</p>
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                Days with no valid pairs are kept visible rather than hidden.
              </p>
            </div>
            <span className="text-xs font-semibold text-[var(--text-muted)]">
              {daily.length} days
            </span>
          </div>
          {daily.length === 0 ? (
            <p className="p-5 text-sm text-[var(--text-muted)]">
              No daily breakdown was returned for this period.
            </p>
          ) : (
            <div className="max-h-80 overflow-auto">
              <table className="w-full min-w-[560px] text-left text-sm">
                <caption className="sr-only">
                  Daily forecast accuracy for the selected delivery period
                </caption>
                <thead className="sticky top-0 bg-[var(--surface-muted)] text-[10px] uppercase tracking-[0.12em] text-[var(--text-muted)]">
                  <tr>
                    <th scope="col" className="px-5 py-3">
                      Date (UTC)
                    </th>
                    <th scope="col" className="px-5 py-3">
                      Pairs
                    </th>
                    <th scope="col" className="px-5 py-3">
                      MAE
                    </th>
                    <th scope="col" className="px-5 py-3">
                      Bias
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {daily.map((day) => (
                    <tr key={day.date} className="text-[var(--text-muted)]">
                      <th scope="row" className="px-5 py-3 font-mono text-xs font-semibold text-[var(--text)]">
                        {day.date}
                      </th>
                      <td className="px-5 py-3">{day.n}</td>
                      <td className="px-5 py-3">{formatMw(day.mae)}</td>
                      <td className="px-5 py-3">{formatMw(day.bias)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="surface-muted rounded-3xl p-5">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
          Method note
        </p>
        <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">
          Forecast error is forecast minus actual. For each delivery hour, the selected vintage is
          the latest WINDFOR publication at or before the cutoff. Half-hourly FUELHH actuals are
          averaged to hourly values only when both half-hours are present and valid. MAE, RMSE, and
          bias use only matched pairs; coverage counts show the data that was excluded.
        </p>
      </div>
    </section>
  );
}
