function SkeletonBlock({ className }: { className: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function OverviewSkeleton() {
  return (
    <section className="space-y-5">
      <div>
        <SkeletonBlock className="h-3 w-28 rounded-full" />
        <SkeletonBlock className="mt-4 h-9 w-3/4 max-w-xl rounded-xl" />
        <SkeletonBlock className="mt-3 h-4 w-full max-w-2xl rounded-lg" />
      </div>
      <div className="surface rounded-3xl p-5">
        <SkeletonBlock className="h-4 w-40 rounded-full" />
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
          {Array.from({ length: 3 }, (_, index) => <SkeletonBlock key={index} className="h-10 rounded-xl" />)}
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <div key={index} className="surface rounded-3xl p-5">
            <SkeletonBlock className="h-3 w-28 rounded-full" />
            <SkeletonBlock className="mt-5 h-8 w-32 rounded-lg" />
            <SkeletonBlock className="mt-3 h-3 w-40 rounded-full" />
          </div>
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="surface rounded-3xl p-5 sm:p-6"><SkeletonBlock className="h-4 w-44 rounded-full" /><SkeletonBlock className="mt-6 h-28 w-full rounded-2xl" /></div>
        <div className="surface rounded-3xl p-5 sm:p-6"><SkeletonBlock className="h-4 w-32 rounded-full" /><div className="mt-6 space-y-4">{Array.from({ length: 4 }, (_, index) => <SkeletonBlock key={index} className="h-4 w-full rounded-full" />)}</div></div>
      </div>
    </section>
  );
}

export function TimelineSkeleton() {
  return (
    <section className="space-y-6">
      <div><SkeletonBlock className="h-3 w-32 rounded-full" /><SkeletonBlock className="mt-4 h-9 w-2/3 max-w-xl rounded-xl" /><SkeletonBlock className="mt-3 h-4 w-80 rounded-lg" /></div>
      <div className="surface rounded-3xl p-4 sm:p-6"><div className="flex justify-between"><SkeletonBlock className="h-4 w-40 rounded-full" /><SkeletonBlock className="h-4 w-32 rounded-full" /></div><SkeletonBlock className="mt-7 h-64 w-full rounded-2xl" /></div>
      <div className="surface overflow-hidden rounded-3xl"><div className="border-b border-[var(--border)] p-5"><SkeletonBlock className="h-4 w-48 rounded-full" /></div><div className="space-y-4 p-5">{Array.from({ length: 5 }, (_, index) => <SkeletonBlock key={index} className="h-5 w-full rounded-lg" />)}</div></div>
    </section>
  );
}

export function ForecastHistorySkeleton() {
  return (
    <section className="space-y-6">
      <div><SkeletonBlock className="h-3 w-32 rounded-full" /><SkeletonBlock className="mt-4 h-9 w-2/3 max-w-xl rounded-xl" /><SkeletonBlock className="mt-3 h-4 w-96 max-w-full rounded-lg" /></div>
      <div className="grid gap-4 sm:grid-cols-3">{Array.from({ length: 3 }, (_, index) => <div key={index} className="surface rounded-3xl p-5"><SkeletonBlock className="h-3 w-32 rounded-full" /><SkeletonBlock className="mt-5 h-8 w-24 rounded-lg" /><SkeletonBlock className="mt-3 h-3 w-36 rounded-full" /></div>)}</div>
      <div className="surface rounded-3xl p-5 sm:p-6"><SkeletonBlock className="h-4 w-52 rounded-full" /><div className="mt-6 grid gap-4 sm:grid-cols-3">{Array.from({ length: 3 }, (_, index) => <SkeletonBlock key={index} className="h-20 rounded-2xl" />)}</div></div>
      <div className="grid gap-6 lg:grid-cols-2">{Array.from({ length: 2 }, (_, index) => <div key={index} className="surface rounded-3xl p-5"><SkeletonBlock className="h-4 w-48 rounded-full" /><div className="mt-5 space-y-4">{Array.from({ length: 4 }, (_, row) => <SkeletonBlock key={row} className="h-10 rounded-2xl" />)}</div></div>)}</div>
    </section>
  );
}
