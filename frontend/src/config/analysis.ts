import type { AnalysisCutoff, CutoffPreset } from '../services/api';

export interface AnalysisFiltersState extends AnalysisCutoff {
  from: string;
  to: string;
}

export const CUTOFF_OPTIONS: Array<{
  value: CutoffPreset;
  label: string;
  description: string;
}> = [
  {
    value: 'day_ahead_noon',
    label: 'Day-ahead 12:00 UTC (D-1)',
    description: 'Latest forecast published by noon UTC on the day before delivery.',
  },
  {
    value: 'day_ahead_midnight',
    label: 'Day-ahead 00:00 UTC (D-1)',
    description: 'Latest forecast published by midnight UTC on the day before delivery.',
  },
  {
    value: 'hours_24',
    label: '24 hours before delivery',
    description: 'Exactly 24 hours before each hourly delivery interval starts.',
  },
  {
    value: 'hours_12',
    label: '12 hours before delivery',
    description: 'Exactly 12 hours before each hourly delivery interval starts.',
  },
  {
    value: 'hours_2',
    label: '2 hours before delivery',
    description: 'Exactly 2 hours before each hourly delivery interval starts.',
  },
  {
    value: 'hours_1',
    label: '1 hour before delivery',
    description: 'Exactly 1 hour before each hourly delivery interval starts.',
  },
];

export const DEFAULT_FILTERS: AnalysisFiltersState = {
  from: '2026-01-01',
  to: '2026-01-31',
  mode: 'preset',
  preset: 'day_ahead_noon',
  absolute: '2026-01-01T00:00',
};
