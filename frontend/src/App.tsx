import { useEffect, useState } from 'react';
import Overview from './pages/Overview';
import Timeline from './pages/Timeline';
import ForecastHistory from './pages/ForecastHistory';

type PageKey = 'overview' | 'timeline' | 'forecast-history';
type Theme = 'light' | 'dark';

const NAV_ITEMS: Array<{ key: PageKey; label: string; caption: string; icon: string }> = [
  { key: 'overview', label: 'Overview', caption: 'Decision snapshot', icon: '⌂' },
  { key: 'timeline', label: 'Timeline', caption: 'Actual vs forecast', icon: '⌁' },
  { key: 'forecast-history', label: 'Forecast history', caption: 'Vintage inspection', icon: '◷' },
];

function getInitialTheme(): Theme {
  const saved = window.localStorage.getItem('windsight-theme');
  if (saved === 'light' || saved === 'dark') return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export default function App() {
  const [page, setPage] = useState<PageKey>('overview');
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    window.localStorage.setItem('windsight-theme', theme);
  }, [theme]);

  const activeItem = NAV_ITEMS.find((item) => item.key === page) ?? NAV_ITEMS[0];

  return (
    <div className="app-shell flex min-h-screen">
      <aside className="sidebar hidden w-72 shrink-0 flex-col px-5 py-6 lg:flex">
        <div className="flex items-center gap-3 px-2">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--brand)] text-xl text-white shadow-lg shadow-[color-mix(in_srgb,var(--brand)_25%,transparent)]">
            ↗
          </div>
          <div>
            <p className="text-lg font-bold tracking-tight text-[var(--text)]">WindSight</p>
            <p className="text-xs text-[var(--text-muted)]">Forecast intelligence</p>
          </div>
        </div>

        <div className="mt-12">
          <p className="px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-[var(--text-subtle)]">
            Workspace
          </p>
          <nav className="mt-3 space-y-2" aria-label="Primary navigation">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setPage(item.key)}
                className={`flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition ${
                  page === item.key
                    ? 'bg-[var(--brand-soft)] text-[var(--brand-strong)]'
                    : 'text-[var(--text-muted)] hover:bg-[var(--surface-muted)] hover:text-[var(--text)]'
                }`}
              >
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--surface-raised)] text-lg shadow-sm">
                  {item.icon}
                </span>
                <span>
                  <span className="block text-sm font-semibold">{item.label}</span>
                  <span className="mt-0.5 block text-xs text-[var(--text-subtle)]">{item.caption}</span>
                </span>
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-auto rounded-2xl border border-[var(--border)] bg-[var(--surface-muted)] p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-[var(--success)]">
            <span className="h-2 w-2 rounded-full bg-[var(--success)]" />
            Elexon source connected
          </div>
          <p className="mt-2 text-xs leading-5 text-[var(--text-muted)]">
            Historical wind data is cached locally for reproducible analysis.
          </p>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_80%,transparent)] px-4 py-4 backdrop-blur-xl sm:px-8 lg:px-10">
          <div className="content-shell flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                <span>WindSight</span>
                <span>/</span>
                <span className="truncate">{activeItem.label}</span>
              </div>
              <h1 className="mt-1 truncate text-xl font-bold tracking-tight text-[var(--text)] sm:text-2xl">
                {activeItem.label}
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <span className="hidden rounded-full bg-[var(--success-soft)] px-3 py-1.5 text-xs font-semibold text-[var(--success)] sm:inline-flex">
                ● Live analysis
              </span>
              <button
                type="button"
                aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--surface)] text-lg text-[var(--text-muted)] shadow-sm transition hover:border-[var(--brand)] hover:text-[var(--brand)]"
              >
                {theme === 'dark' ? '☼' : '☾'}
              </button>
            </div>
          </div>
          <nav className="content-shell mt-4 flex gap-2 overflow-x-auto lg:hidden" aria-label="Mobile navigation">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => setPage(item.key)}
                className={`whitespace-nowrap rounded-xl px-3 py-2 text-xs font-semibold ${
                  page === item.key
                    ? 'bg-[var(--brand)] text-white'
                    : 'bg-[var(--surface-muted)] text-[var(--text-muted)]'
                }`}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </header>

        <main className="content-shell px-4 py-6 sm:px-8 sm:py-8 lg:px-10">
          {page === 'overview' && <Overview />}
          {page === 'timeline' && <Timeline />}
          {page === 'forecast-history' && <ForecastHistory />}
        </main>
      </div>
    </div>
  );
}
