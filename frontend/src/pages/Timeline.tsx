import { useCallback } from 'react';
import type { AnalysisFiltersState } from '../config/analysis';
import { TimelineSkeleton } from '../components/LoadingState';
import { useAsyncData } from '../hooks/useAsyncData';
import { getTimeseries, type ForecastPoint } from '../services/api';

const CHART_WIDTH = 960;
const CHART_HEIGHT = 320;
const CHART_MARGIN = { top: 20, right: 24, bottom: 48, left: 68 };
const CHART_INNER_W = CHART_WIDTH - CHART_MARGIN.left - CHART_MARGIN.right;
const CHART_INNER_H = CHART_HEIGHT - CHART_MARGIN.top - CHART_MARGIN.bottom;

function formatMw(value: number | null): string {
  return value === null ? '—' : `${value.toFixed(1)} MW`;
}

function formatDateTime(value: string | null): string {
  if (!value) return '—';
  return new Date(value).toLocaleString('en-GB', {
    timeZone: 'UTC',
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

function formatTick(value: string): string {
  return new Date(value).toLocaleString('en-GB', {
    timeZone: 'UTC',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function lineSegments(
  points: ForecastPoint[],
  key: 'forecast_mw' | 'actual_mw',
  x: (index: number) => number,
  y: (value: number) => number,
): string[] {
  const segments: string[] = [];
  let current: string[] = [];

  points.forEach((point, index) => {
    const value = point[key];
    if (value === null) {
      if (current.length > 0) {
        segments.push(current.join(' '));
        current = [];
      }
      return;
    }
    current.push(`${current.length === 0 ? 'M' : 'L'}${x(index).toFixed(1)},${y(value).toFixed(1)}`);
  });

  if (current.length > 0) segments.push(current.join(' '));
  return segments;
}

function ForecastActualChart({ points }: { points: ForecastPoint[] }) {
  const values = points.flatMap((point) => [point.forecast_mw, point.actual_mw]).filter(
    (value): value is number => value !== null,
  );
  const maxVal = Math.max(1, ...values);
  const x = (index: number) =>
    points.length <= 1
      ? CHART_MARGIN.left + CHART_INNER_W / 2
      : CHART_MARGIN.left + (index / (points.length - 1)) * CHART_INNER_W;
  const y = (value: number) =>
    CHART_MARGIN.top + CHART_INNER_H - (Math.max(0, value) / maxVal) * CHART_INNER_H;

  const forecastSegments = lineSegments(points, 'forecast_mw', x, y);
  const actualSegments = lineSegments(points, 'actual_mw', x, y);
  const tickIndices = Array.from(
    new Set([0, Math.floor((points.length - 1) * 0.25), Math.floor((points.length - 1) * 0.5), Math.floor((points.length - 1) * 0.75), points.length - 1]),
  );

  return (
    <svg
      viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
      className="w-full"
      role="img"
      aria-labelledby="timeline-chart-title timeline-chart-description"
    >
      <title id="timeline-chart-title">Forecast versus actual wind generation</title>
      <desc id="timeline-chart-description">
        Hourly line chart comparing the selected forecast vintage with metered wind output. Gaps
        indicate missing data and are not drawn as zero.
      </desc>
      {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
        const gridY = CHART_MARGIN.top + CHART_INNER_H - fraction * CHART_INNER_H;
        return (
          <g key={fraction}>
            <line
              className="chart-grid"
              x1={CHART_MARGIN.left}
              x2={CHART_WIDTH - CHART_MARGIN.right}
              y1={gridY}
              y2={gridY}
              strokeWidth={1}
            />
            <text
              className="chart-label"
              x={CHART_MARGIN.left - 10}
              y={gridY + 4}
              textAnchor="end"
              fontSize={11}
            >
              {(maxVal * fraction).toFixed(0)}
            </text>
          </g>
        );
      })}
      {forecastSegments.map((segment, index) => (
        <path
          key={`forecast-${index}`}
          d={segment}
          fill="none"
          stroke="var(--chart-forecast)"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}
      {actualSegments.map((segment, index) => (
        <path
          key={`actual-${index}`}
          d={segment}
          fill="none"
          stroke="var(--chart-actual)"
          strokeWidth={2.5}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}
      {points.map((point, index) =>
        point.actual_mw === null ? null : (
          <circle
            key={`actual-${point.delivery_time}`}
            cx={x(index)}
            cy={y(point.actual_mw)}
            r={2.5}
            fill="var(--chart-actual)"
          >
            <title>{`${formatDateTime(point.delivery_time)}: actual ${formatMw(point.actual_mw)}`}</title>
          </circle>
        ),
      )}
      {tickIndices.map((index) => (
        <text
          key={`tick-${index}`}
          className="chart-label"
          x={x(index)}
          y={CHART_HEIGHT - 16}
          textAnchor={index === 0 ? 'start' : index === points.length - 1 ? 'end' : 'middle'}
          fontSize={10}
        >
          {formatTick(points[index].delivery_time)}
        </text>
      ))}
      <text
        className="chart-label"
        x={CHART_MARGIN.left - 10}
        y={CHART_MARGIN.top - 8}
        textAnchor="end"
        fontSize={10}
      >
        MW
      </text>
    </svg>
  );
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="metric-card rounded-3xl p-5">
      <p className="text-xs font-bold uppercase tracking-[0.12em] text-[var(--text-muted)]">
        {label}
      </p>
      <p className="mt-3 text-2xl font-bold tracking-tight text-[var(--text)]">{value}</p>
      <p className="mt-1 text-xs text-[var(--text-muted)]">{detail}</p>
    </div>
  );
}

export default function Timeline({ filters }: { filters: AnalysisFiltersState }) {
  const requestKey = JSON.stringify(filters);
  const loadTimeseries = useCallback(
    () => getTimeseries(filters.from, filters.to, filters),
    [filters],
  );
  const { data, loading, error } = useAsyncData(requestKey, loadTimeseries);

  if (loading && !data) return <TimelineSkeleton />;
  if (error) {
    return (
      <section className="rounded-3xl border border-[var(--danger)] bg-[var(--danger-soft)] p-6">
        <p className="text-sm font-bold text-[var(--danger)]">Unable to load the timeline</p>
        <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{error}</p>
      </section>
    );
  }
  if (!data) {
    return (
      <section className="surface rounded-3xl p-8 text-sm text-[var(--text-muted)]">
        No timeline data was returned.
      </section>
    );
  }

  const leadTimes = data.points
    .map((point) => point.lead_time_hours)
    .filter((value): value is number => value !== null);
  const averageLead =
    leadTimes.length > 0 ? leadTimes.reduce((sum, value) => sum + value, 0) / leadTimes.length : null;
  const signedErrors = data.points
    .map((point) => point.error_mw)
    .filter((value): value is number => value !== null);
  const maxAbsoluteError =
    signedErrors.length > 0
      ? Math.max(...signedErrors.map((value) => Math.abs(value)))
      : null;

  return (
    <section className="space-y-6" aria-busy={loading}>
      <div>
        <p className="text-sm font-semibold text-[var(--brand)]">Generation profile</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-[var(--text)] sm:text-3xl">
          Actual versus forecast timeline
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-muted)]">
          {data.from_date} to {data.to_date}. Latest eligible vintage per hour; gaps are missing
          data.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          label="Matched hours"
          value={`${data.coverage.matched_pairs}`}
          detail={`of ${data.coverage.total_delivery_intervals} expected hours`}
        />
        <SummaryCard
          label="Coverage"
          value={
            data.coverage.coverage_percentage === null
              ? 'Not available'
              : `${data.coverage.coverage_percentage.toFixed(1)}%`
          }
          detail="Share of hours with a valid forecast and actual"
        />
        <SummaryCard
          label="Average lead time"
          value={averageLead === null ? 'Not available' : `${averageLead.toFixed(1)} h`}
          detail="Time between publication and delivery"
        />
        <SummaryCard
          label="Largest absolute miss"
          value={maxAbsoluteError === null ? 'Not available' : `${maxAbsoluteError.toFixed(1)} MW`}
          detail="Maximum |forecast minus actual| in the window"
        />
      </div>

      <div className="surface rounded-3xl p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-bold text-[var(--text)]">Hourly generation in MW</p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              {data.cutoff_label}
            </p>
          </div>
          <div className="flex gap-4 text-xs font-semibold text-[var(--text-muted)]">
            <span className="flex items-center gap-2">
              <i className="h-2.5 w-2.5 rounded-full bg-[var(--chart-forecast)]" aria-hidden="true" />
              Forecast
            </span>
            <span className="flex items-center gap-2">
              <i className="h-2.5 w-2.5 rounded-full bg-[var(--chart-actual)]" aria-hidden="true" />
              Actual
            </span>
          </div>
        </div>
        <div className="mt-6 overflow-x-auto">
          <div className="min-w-[720px]">
            <ForecastActualChart points={data.points} />
          </div>
        </div>
      </div>

      {data.points.length === 0 ? (
        <div className="surface rounded-3xl p-8 text-sm text-[var(--text-muted)]">
          No delivery intervals were returned for this selection. Adjust the period or cutoff rule.
        </div>
      ) : (
        <div className="surface overflow-hidden rounded-3xl">
          <div className="border-b border-[var(--border)] px-5 py-4">
            <p className="text-sm font-bold text-[var(--text)]">Delivery interval detail</p>
            <p className="mt-1 text-xs text-[var(--text-muted)]">
              {data.points.length} hourly points returned by the API
            </p>
          </div>
          <div className="max-h-[32rem] overflow-auto">
            <table className="w-full min-w-[860px] text-left text-sm">
              <caption className="sr-only">
                Hourly forecast, actual, signed error, lead time, and publication time
              </caption>
              <thead className="sticky top-0 bg-[var(--surface-muted)] text-[10px] uppercase tracking-[0.12em] text-[var(--text-muted)]">
                <tr>
                  <th scope="col" className="px-5 py-3">
                    Delivery UTC
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Forecast
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Actual
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Error
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Lead
                  </th>
                  <th scope="col" className="px-5 py-3">
                    Published UTC
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {data.points.map((point) => (
                  <tr
                    key={point.delivery_time}
                    className="text-[var(--text-muted)] transition hover:bg-[var(--surface-muted)]"
                  >
                    <th
                      scope="row"
                      className="whitespace-nowrap px-5 py-3 font-mono text-xs font-semibold text-[var(--text)]"
                    >
                      {formatDateTime(point.delivery_time)}
                    </th>
                    <td className="px-5 py-3 font-semibold text-[var(--accent-strong)]">
                      {formatMw(point.forecast_mw)}
                    </td>
                    <td className="px-5 py-3 font-semibold text-[var(--chart-actual)]">
                      {formatMw(point.actual_mw)}
                    </td>
                    <td className="px-5 py-3">{formatMw(point.error_mw)}</td>
                    <td className="px-5 py-3">
                      {point.lead_time_hours === null
                        ? '—'
                        : `${point.lead_time_hours.toFixed(1)} h`}
                    </td>
                    <td className="px-5 py-3 font-mono text-xs">
                      {formatDateTime(point.publish_time)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
