import { CUTOFF_OPTIONS, type AnalysisFiltersState } from '../config/analysis';
import type { CutoffPreset } from '../services/api';

interface AnalysisFiltersProps {
  filters: AnalysisFiltersState;
  onChange: (filters: AnalysisFiltersState) => void;
}

export default function AnalysisFilters({ filters, onChange }: AnalysisFiltersProps) {
  const selectedPreset =
    CUTOFF_OPTIONS.find((option) => option.value === filters.preset) ?? CUTOFF_OPTIONS[0];

  const setFrom = (from: string) => {
    const absolute =
      filters.mode === 'absolute' && filters.absolute > `${from}T00:00`
        ? `${from}T00:00`
        : filters.absolute;
    onChange({ ...filters, from, absolute });
  };

  const setTo = (to: string) => {
    onChange({ ...filters, to });
  };

  const setPreset = (preset: CutoffPreset) => {
    onChange({ ...filters, mode: 'preset', preset });
  };

  const useAbsolute = () => {
    onChange({ ...filters, mode: 'absolute', absolute: `${filters.from}T00:00` });
  };

  const usePreset = () => {
    onChange({ ...filters, mode: 'preset' });
  };

  return (
    <section className="surface rounded-3xl p-4 sm:p-5" aria-labelledby="analysis-filters-heading">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h2 id="analysis-filters-heading" className="text-sm font-bold text-[var(--text)]">
            Analysis window
          </h2>
          <p className="mt-1 text-xs text-[var(--text-muted)]">
            Delivery period and forecast decision cutoff. All timestamps are UTC.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="text-xs font-semibold text-[var(--text-muted)]">
            From
            <input
              type="date"
              value={filters.from}
              onChange={(event) => setFrom(event.target.value)}
              className="field mt-1.5 block w-full rounded-xl px-3 py-2 text-sm"
            />
          </label>
          <label className="text-xs font-semibold text-[var(--text-muted)]">
            To
            <input
              type="date"
              value={filters.to}
              onChange={(event) => setTo(event.target.value)}
              className="field mt-1.5 block w-full rounded-xl px-3 py-2 text-sm"
            />
          </label>
          <label className="text-xs font-semibold text-[var(--text-muted)]">
            Cutoff rule
            <select
              value={filters.preset}
              onChange={(event) => setPreset(event.target.value as CutoffPreset)}
              disabled={filters.mode === 'absolute'}
              className="field mt-1.5 block w-full rounded-xl px-3 py-2 text-sm disabled:opacity-60"
            >
              {CUTOFF_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3 border-t border-[var(--border)] pt-4 lg:flex-row lg:items-start lg:justify-between">
        {filters.mode === 'preset' ? (
          <p className="max-w-3xl text-xs leading-5 text-[var(--text-muted)]">
            <span className="font-semibold text-[var(--text)]">How a vintage is chosen:</span>{' '}
            {selectedPreset.description} Forecasts published after the cutoff are excluded, so the
            analysis does not use information unavailable at decision time.
          </p>
        ) : (
          <div className="flex-1">
            <label className="text-xs font-semibold text-[var(--text-muted)]">
              Absolute cutoff (UTC)
              <input
                type="datetime-local"
                value={filters.absolute}
                max={`${filters.from}T00:00`}
                onChange={(event) => onChange({ ...filters, absolute: event.target.value })}
                className="field mt-1.5 block w-full max-w-xs rounded-xl px-3 py-2 text-sm"
              />
            </label>
            <p className="mt-2 max-w-3xl text-xs leading-5 text-[var(--text-muted)]">
              A single cutoff must be at or before {filters.from} 00:00 UTC. A later cutoff would
              let forecasts published during the delivery period leak into the evaluation.
            </p>
          </div>
        )}
        <button
          type="button"
          onClick={filters.mode === 'preset' ? useAbsolute : usePreset}
          className="shrink-0 self-start rounded-xl border border-[var(--border-strong)] bg-[var(--surface)] px-3 py-2 text-xs font-semibold text-[var(--text)] transition hover:border-[var(--brand)] hover:text-[var(--brand)]"
        >
          {filters.mode === 'preset' ? 'Use a single absolute cutoff' : 'Back to per-delivery preset'}
        </button>
      </div>
    </section>
  );
}
