import { useEffect, useState } from 'react';
import { getTimeseries, type ForecastPoint, type TimeseriesResponse } from '../services/api';
import { TimelineSkeleton } from '../components/LoadingState';

const PERIOD_FROM = '2026-01-01';
const PERIOD_TO = '2026-01-31';
const CHART_WIDTH = 900;
const CHART_HEIGHT = 300;
const CHART_MARGIN = { top: 20, right: 20, bottom: 42, left: 64 };
const CHART_INNER_W = CHART_WIDTH - CHART_MARGIN.left - CHART_MARGIN.right;
const CHART_INNER_H = CHART_HEIGHT - CHART_MARGIN.top - CHART_MARGIN.bottom;

function ForecastActualChart({ points }: { points: ForecastPoint[] }) {
  const n = points.length;
  const values = points.flatMap((p) => [p.forecast_mw ?? 0, p.actual_mw ?? 0]);
  const maxVal = Math.max(1, ...values);
  const x = (i: number) => CHART_MARGIN.left + (n <= 1 ? CHART_INNER_W / 2 : (i / (n - 1)) * CHART_INNER_W);
  const y = (v: number) => CHART_MARGIN.top + CHART_INNER_H - (v / maxVal) * CHART_INNER_H;
  const pathFor = (key: 'forecast_mw' | 'actual_mw') =>
    points
      .map((point, index) => {
        const value = point[key];
        return value === null ? null : `${index === 0 ? 'M' : 'L'}${x(index).toFixed(1)},${y(value).toFixed(1)}`;
      })
      .filter((path): path is string => path !== null)
      .join(' ');

  return (
    <svg viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} className="w-full" role="img" aria-label="Forecast versus actual generation chart">
      {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
        const gridY = CHART_MARGIN.top + CHART_INNER_H - fraction * CHART_INNER_H;
        return (
          <g key={fraction}>
            <line className="chart-grid" x1={CHART_MARGIN.left} x2={CHART_WIDTH - CHART_MARGIN.right} y1={gridY} y2={gridY} strokeWidth={1} />
            <text className="chart-label" x={CHART_MARGIN.left - 10} y={gridY + 4} textAnchor="end" fontSize={11}>
              {(maxVal * fraction).toFixed(0)}
            </text>
          </g>
        );
      })}
      <path d={pathFor('forecast_mw')} fill="none" stroke="var(--chart-forecast)" strokeWidth={2.5} />
      <path d={pathFor('actual_mw')} fill="none" stroke="var(--chart-actual)" strokeWidth={2.5} />
      {points.filter((point) => point.actual_mw !== null).map((point, index) => (
        <circle key={`actual-${point.delivery_time}`} cx={x(index)} cy={y(point.actual_mw ?? 0)} r={2.5} fill="var(--chart-actual)" />
      ))}
      <text className="chart-label" x={CHART_MARGIN.left} y={CHART_HEIGHT - 12} fontSize={11}>
        {points[0]?.delivery_time ?? ''} UTC
      </text>
      <text className="chart-label" x={CHART_WIDTH - CHART_MARGIN.right} y={CHART_HEIGHT - 12} textAnchor="end" fontSize={11}>
        {points.at(-1)?.delivery_time ?? ''} UTC
      </text>
    </svg>
  );
}

export default function Timeline() {
  const [data, setData] = useState<TimeseriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getTimeseries(PERIOD_FROM, PERIOD_TO)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load timeseries');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <TimelineSkeleton />;
  if (error || !data) return <section className="rounded-3xl border border-[var(--danger)] bg-[var(--danger-soft)] p-6 text-sm text-[var(--danger)]">{error ?? 'No timeline data returned'}</section>;
  if (data.points.length === 0) return <section className="surface rounded-3xl p-8 text-sm text-[var(--text-muted)]">No delivery intervals were available.</section>;

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-[var(--brand)]">Generation profile</p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight text-[var(--text)]">Actual vs forecast timeline</h2>
        <p className="mt-3 text-sm text-[var(--text-muted)]">
          {data.from_date} → {data.to_date} · selected forecast cutoff {data.decision_cutoff ?? 'default'} · UTC
        </p>
      </div>

      <div className="surface rounded-3xl p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-bold text-[var(--text)]">Generation in MW</p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">Hourly delivery intervals</p>
          </div>
          <div className="flex gap-4 text-xs font-semibold text-[var(--text-muted)]">
            <span className="flex items-center gap-2"><i className="h-2.5 w-2.5 rounded-full bg-[var(--chart-forecast)]" /> Forecast</span>
            <span className="flex items-center gap-2"><i className="h-2.5 w-2.5 rounded-full bg-[var(--chart-actual)]" /> Actual</span>
          </div>
        </div>
        <div className="mt-6 overflow-x-auto">
          <div className="min-w-[700px]"><ForecastActualChart points={data.points} /></div>
        </div>
      </div>

      <div className="surface overflow-hidden rounded-3xl">
        <div className="border-b border-[var(--border)] px-5 py-4">
          <p className="text-sm font-bold text-[var(--text)]">Delivery interval detail</p>
          <p className="mt-1 text-xs text-[var(--text-muted)]">{data.points.length} points returned by the API</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-[var(--surface-muted)] text-[10px] uppercase tracking-[0.12em] text-[var(--text-muted)]">
              <tr><th className="px-5 py-3">Delivery UTC</th><th className="px-5 py-3">Forecast MW</th><th className="px-5 py-3">Actual MW</th><th className="px-5 py-3">Source</th><th className="px-5 py-3">Published UTC</th></tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {data.points.map((point) => (
                <tr key={point.delivery_time} className="text-[var(--text-muted)] transition hover:bg-[var(--surface-muted)]">
                  <td className="px-5 py-3 font-mono text-xs text-[var(--text)]">{point.delivery_time}</td>
                  <td className="px-5 py-3 font-semibold text-[var(--accent)]">{point.forecast_mw === null ? '—' : point.forecast_mw.toFixed(1)}</td>
                  <td className="px-5 py-3 font-semibold text-[var(--chart-actual)]">{point.actual_mw === null ? '—' : point.actual_mw.toFixed(1)}</td>
                  <td className="px-5 py-3">{point.forecast_source ?? '—'}</td>
                  <td className="px-5 py-3 font-mono text-xs">{point.publish_time ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
