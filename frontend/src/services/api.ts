export type CutoffPreset =
  | 'day_ahead_noon'
  | 'day_ahead_midnight'
  | 'hours_24'
  | 'hours_12'
  | 'hours_2'
  | 'hours_1';

export interface AnalysisCutoff {
  mode: 'preset' | 'absolute';
  preset: CutoffPreset;
  absolute: string;
}

export interface CutoffMetadata {
  decision_cutoff: string | null;
  cutoff_mode: string;
  cutoff_preset: string | null;
  cutoff_label: string;
  cutoff_description: string;
  cutoff_start: string | null;
  cutoff_end: string | null;
}

export interface AccuracyMetrics {
  n: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  overforecast_percentage: number | null;
  underforecast_percentage: number | null;
  error_p10: number | null;
  error_p50: number | null;
  error_p90: number | null;
}

export interface DailyAccuracy extends AccuracyMetrics {
  date: string;
}

export interface AccuracyCoverage {
  total_delivery_intervals: number;
  matched_pairs: number;
  missing_forecast: number;
  missing_actual: number;
  missing_both: number;
  invalid_forecast: number;
  invalid_actual: number;
  incomplete_actual: number;
  coverage_percentage: number | null;
}

export interface PeriodMetadata extends CutoffMetadata {
  from_date: string;
  to_date: string;
}

export interface OverviewResponse extends PeriodMetadata {
  delivery_intervals: number;
  matched_pairs: number;
  metrics: AccuracyMetrics;
  daily: DailyAccuracy[];
  coverage: AccuracyCoverage;
}

export interface AccuracyResponse extends PeriodMetadata {
  metrics: AccuracyMetrics;
  daily: DailyAccuracy[];
  coverage: AccuracyCoverage;
}

export interface ForecastPoint {
  delivery_time: string;
  forecast_mw: number | null;
  actual_mw: number | null;
  error_mw: number | null;
  lead_time_hours: number | null;
  publish_time: string | null;
  cutoff: string | null;
  forecast_source: string | null;
  forecast_dataset: string | null;
}

export interface TimeseriesResponse extends PeriodMetadata {
  points: ForecastPoint[];
  coverage: AccuracyCoverage;
}

export interface ForecastVintage {
  publish_time: string;
  start_time: string;
  generation_mw: number | null;
  lead_time_hours: number | null;
}

export interface ForecastHistoryResponse extends CutoffMetadata {
  delivery_time: string;
  cutoff: string;
  selected: ForecastVintage | null;
  eligible_vintages: ForecastVintage[];
  excluded_vintages: ForecastVintage[];
}

export interface SourceStatus {
  source: string;
  cached: boolean;
  files: number;
  last_retrieved_utc: string | null;
  age_hours: number | null;
  stale: boolean;
  row_count: number | null;
  normalized_count: number | null;
}

export interface DataStatusResponse {
  status: string;
  checked_at_utc: string;
  cache_dir: string;
  cache_writable: boolean;
  cache_ttl_hours: number;
  sources: Record<string, SourceStatus>;
}

const DEFAULT_API_BASE = import.meta.env.PROD
  ? 'https://windsight-lpuk.onrender.com/api'
  : 'http://localhost:8000/api';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE).replace(/\/$/, '');

function toUtcIso(value: string): string {
  if (/(?:Z|[+-]\d{2}:\d{2})$/i.test(value)) return value;
  return `${value.length === 16 ? `${value}:00` : value}Z`;
}

function addCutoffParams(params: URLSearchParams, cutoff: AnalysisCutoff): void {
  if (cutoff.mode === 'absolute' && cutoff.absolute) {
    params.set('decision_cutoff', toUtcIso(cutoff.absolute));
    return;
  }
  params.set('cutoff_preset', cutoff.preset);
}

async function getJson<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 60_000);
  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    });
    if (!response.ok) {
      let detail = `Request failed with status ${response.status}`;
      try {
        const payload = (await response.json()) as { detail?: string | unknown[] };
        if (typeof payload.detail === 'string') {
          detail = payload.detail;
        } else if (Array.isArray(payload.detail)) {
          detail = payload.detail
            .map((item) =>
              typeof item === 'object' && item !== null && 'msg' in item
                ? String((item as { msg: unknown }).msg)
                : String(item),
            )
            .join('; ');
        }
      } catch {
        const text = await response.text().catch(() => '');
        if (text) detail = text;
      }
      throw new Error(detail);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('The analysis request timed out. Please retry.');
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function getOverview(
  from: string,
  to: string,
  cutoff: AnalysisCutoff,
): Promise<OverviewResponse> {
  const params = new URLSearchParams({ from, to });
  addCutoffParams(params, cutoff);
  return getJson<OverviewResponse>(`/overview?${params.toString()}`);
}

export async function getAccuracy(
  from: string,
  to: string,
  cutoff: AnalysisCutoff,
): Promise<AccuracyResponse> {
  const params = new URLSearchParams({ from, to });
  addCutoffParams(params, cutoff);
  return getJson<AccuracyResponse>(`/accuracy?${params.toString()}`);
}

export async function getTimeseries(
  from: string,
  to: string,
  cutoff: AnalysisCutoff,
): Promise<TimeseriesResponse> {
  const params = new URLSearchParams({ from, to });
  addCutoffParams(params, cutoff);
  return getJson<TimeseriesResponse>(`/timeseries?${params.toString()}`);
}

export async function getForecastHistory(
  deliveryTime: string,
  cutoff: AnalysisCutoff,
): Promise<ForecastHistoryResponse> {
  const params = new URLSearchParams({ delivery_time: toUtcIso(deliveryTime) });
  addCutoffParams(params, cutoff);
  return getJson<ForecastHistoryResponse>(`/forecast-history?${params.toString()}`);
}

export async function getDataStatus(): Promise<DataStatusResponse> {
  return getJson<DataStatusResponse>('/data-status');
}
