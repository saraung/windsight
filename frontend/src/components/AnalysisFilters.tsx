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
    <section className="surface rounded-2xl px-3 py-2.5" aria-label="Analysis window">
      <div className="flex flex-wrap items-end gap-x-3 gap-y-2">
        <div className="hidden self-center pr-1 lg:block">
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--text-muted)]">
            Window
          </p>
          <p className="text-[10px] text-[var(--text-subtle)]">UTC</p>
        </div>

        <label className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--text-muted)]">
          From
          <input
            type="date"
            value={filters.from}
            onChange={(event) => setFrom(event.target.value)}
            className="field mt-1 block h-8 w-[8.75rem] rounded-lg px-2 text-xs font-normal normal-case tracking-normal"
          />
        </label>

        <label className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--text-muted)]">
          To
          <input
            type="date"
            value={filters.to}
            onChange={(event) => setTo(event.target.value)}
            className="field mt-1 block h-8 w-[8.75rem] rounded-lg px-2 text-xs font-normal normal-case tracking-normal"
          />
        </label>

        <label className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--text-muted)]">
          Cutoff
          <select
            value={filters.preset}
            onChange={(event) => setPreset(event.target.value as CutoffPreset)}
            disabled={filters.mode === 'absolute'}
            title={selectedPreset.description}
            className="field mt-1 block h-8 w-[12.5rem] rounded-lg px-2 text-xs font-normal normal-case tracking-normal disabled:opacity-50"
          >
            {CUTOFF_OPTIONS.map((option) => (
              <option key={option.value} value={option.value} title={option.description}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {filters.mode === 'absolute' ? (
          <label className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[var(--text-muted)]">
            Absolute cutoff
            <input
              type="datetime-local"
              value={filters.absolute}
              max={`${filters.from}T00:00`}
              onChange={(event) => onChange({ ...filters, absolute: event.target.value })}
              className="field mt-1 block h-8 w-[12.5rem] rounded-lg px-2 text-xs font-normal normal-case tracking-normal"
            />
          </label>
        ) : null}

        <button
          type="button"
          onClick={filters.mode === 'preset' ? useAbsolute : usePreset}
          className="h-8 whitespace-nowrap rounded-lg border border-[var(--border-strong)] bg-[var(--surface)] px-2 text-[11px] font-semibold text-[var(--text)] transition hover:border-[var(--brand)] hover:text-[var(--brand)]"
        >
          {filters.mode === 'preset' ? 'Absolute cutoff' : 'Per-delivery'}
        </button>
      </div>

      {filters.mode === 'absolute' ? (
        <p className="mt-2 text-[11px] leading-4 text-[var(--text-muted)]">
          One cutoff for every delivery hour; must be at or before {filters.from} 00:00 UTC.
        </p>
      ) : null}
    </section>
  );
}
