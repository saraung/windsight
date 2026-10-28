import { useEffect, useState } from 'react';
import AnalysisFilters from './components/AnalysisFilters';
import { DEFAULT_FILTERS, type AnalysisFiltersState } from './config/analysis';
import {
  BrandIcon,
  HistoryIcon,
  MoonIcon,
  OverviewIcon,
  SunIcon,
  TimelineIcon,
} from './components/Icons';
import StatusBanner from './components/StatusBanner';
import ForecastHistory from './pages/ForecastHistory';
import Overview from './pages/Overview';
import Timeline from './pages/Timeline';
import { getDataStatus, type DataStatusResponse } from './services/api';

type PageKey = 'overview' | 'timeline' | 'forecast-history';
type Theme = 'light' | 'dark';

const NAV_ITEMS = [
  { key: 'overview', label: 'Overview', Icon: OverviewIcon },
  { key: 'timeline', label: 'Timeline', Icon: TimelineIcon },
  { key: 'forecast-history', label: 'Forecast history', Icon: HistoryIcon },
] satisfies Array<{
  key: PageKey;
  label: string;
  Icon: typeof OverviewIcon;
}>;

function getInitialTheme(): Theme {
  const saved = window.localStorage.getItem('windsight-theme');
  if (saved === 'light' || saved === 'dark') return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export default function App() {
  const [page, setPage] = useState<PageKey>('overview');
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [filters, setFilters] = useState<AnalysisFiltersState>(DEFAULT_FILTERS);
  const [status, setStatus] = useState<DataStatusResponse | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [statusError, setStatusError] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    window.localStorage.setItem('windsight-theme', theme);
  }, [theme]);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [page]);

  useEffect(() => {
    let cancelled = false;

    const loadStatus = () => {
      getDataStatus()
        .then((result) => {
          if (!cancelled) {
            setStatus(result);
            setStatusError(null);
            setStatusLoading(false);
          }
        })
        .catch((error: unknown) => {
          if (!cancelled) {
            setStatusError(error instanceof Error ? error.message : 'Status request failed');
            setStatusLoading(false);
          }
        });
    };

    loadStatus();
    const interval = window.setInterval(loadStatus, 60_000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="app-shell flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_94%,transparent)] backdrop-blur-xl">
        <div className="content-shell flex h-16 items-center gap-4 px-4 sm:px-8 lg:px-10">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--brand)] text-white shadow-sm">
              <BrandIcon className="h-5 w-5" />
            </div>
            <div className="hidden sm:block">
              <p className="text-base font-bold leading-tight tracking-tight text-[var(--text)]">
                WindSight
              </p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-[var(--text-muted)]">
                Elexon BMRS
              </p>
            </div>
          </div>

          <nav className="hidden items-center gap-1 md:flex" aria-label="Primary navigation">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setPage(item.key)}
                aria-current={page === item.key ? 'page' : undefined}
                className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition ${
                  page === item.key
                    ? 'bg-[var(--brand-soft)] text-[var(--brand-strong)]'
                    : 'text-[var(--text-muted)] hover:bg-[var(--surface-muted)] hover:text-[var(--text)]'
                }`}
              >
                <item.Icon className="h-4 w-4" />
                {item.label}
              </button>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <StatusBanner status={status} loading={statusLoading} error={statusError} />
            <button
              type="button"
              aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface)] text-[var(--text-muted)] shadow-sm transition hover:border-[var(--brand)] hover:text-[var(--brand)]"
            >
              {theme === 'dark' ? <SunIcon className="h-4 w-4" /> : <MoonIcon className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <nav
          className="content-shell flex gap-1 overflow-x-auto border-t border-[var(--border)] px-4 py-2 md:hidden"
          aria-label="Mobile navigation"
        >
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setPage(item.key)}
              aria-current={page === item.key ? 'page' : undefined}
              className={`flex whitespace-nowrap items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold ${
                page === item.key
                  ? 'bg-[var(--brand)] text-white'
                  : 'text-[var(--text-muted)] hover:bg-[var(--surface-muted)]'
              }`}
            >
              <item.Icon className="h-3.5 w-3.5" />
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="content-shell w-full flex-1 space-y-5 px-4 py-5 sm:px-8 sm:py-6 lg:px-10">
        <AnalysisFilters filters={filters} onChange={setFilters} />
        <div key={page} className="page-view">
          {page === 'overview' && <Overview filters={filters} />}
          {page === 'timeline' && <Timeline filters={filters} />}
          {page === 'forecast-history' && <ForecastHistory filters={filters} />}
        </div>
      </main>

      <footer className="content-shell w-full px-4 pb-6 text-[11px] text-[var(--text-muted)] sm:px-8 lg:px-10">
        Source: Elexon BMRS. Scope: WINDFOR total wind vs FUELHH transmission-metered wind.
      </footer>
    </div>
  );
}
