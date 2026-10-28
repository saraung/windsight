export interface AccuracyMetrics {
  n: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  overforecast_percentage: number | null;
}

export interface AccuracyCoverage {
  total_delivery_intervals: number;
  matched_pairs: number;
  missing_forecast: number;
  missing_actual: number;
  invalid_forecast: number;
  invalid_actual: number;
}

export interface OverviewResponse {
  from_date: string;
  to_date: string;
  decision_cutoff: string | null;
  delivery_intervals: number;
  matched_pairs: number;
  metrics: AccuracyMetrics;
  coverage: AccuracyCoverage;
}

export interface AccuracyResponse {
  from_date: string;
  to_date: string;
  decision_cutoff: string | null;
  metrics: AccuracyMetrics;
  coverage: AccuracyCoverage;
}

export interface ForecastPoint {
  delivery_time: string;
  forecast_mw: number | null;
  actual_mw: number | null;
  publish_time: string | null;
  forecast_source: string | null;
  forecast_dataset: string | null;
}

export interface TimeseriesResponse {
  from_date: string;
  to_date: string;
  decision_cutoff: string | null;
  points: ForecastPoint[];
  coverage: AccuracyCoverage;
}

export interface ForecastVintage {
  publish_time: string;
  start_time: string;
  generation_mw: number | null;
}

export interface ForecastHistoryResponse {
  delivery_time: string;
  cutoff: string;
  selected: ForecastVintage | null;
  eligible_vintages: ForecastVintage[];
  excluded_vintages: ForecastVintage[];
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) {
    throw new Error(`Request failed with status ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function getOverview(
  from: string,
  to: string,
  decisionCutoff?: string,
): Promise<OverviewResponse> {
  const params = new URLSearchParams({ from, to });
  if (decisionCutoff) params.set('decision_cutoff', decisionCutoff);
  return getJson<OverviewResponse>(`/overview?${params.toString()}`);
}

export async function getAccuracy(
  from: string,
  to: string,
  decisionCutoff?: string,
): Promise<AccuracyResponse> {
  const params = new URLSearchParams({ from, to });
  if (decisionCutoff) params.set('decision_cutoff', decisionCutoff);
  return getJson<AccuracyResponse>(`/accuracy?${params.toString()}`);
}

export async function getTimeseries(
  from: string,
  to: string,
  decisionCutoff?: string,
): Promise<TimeseriesResponse> {
  const params = new URLSearchParams({ from, to });
  if (decisionCutoff) params.set('decision_cutoff', decisionCutoff);
  return getJson<TimeseriesResponse>(`/timeseries?${params.toString()}`);
}

export async function getForecastHistory(
  deliveryTime: string,
  decisionCutoff?: string,
): Promise<ForecastHistoryResponse> {
  const params = new URLSearchParams({ delivery_time: deliveryTime });
  if (decisionCutoff) params.set('decision_cutoff', decisionCutoff);
  return getJson<ForecastHistoryResponse>(`/forecast-history?${params.toString()}`);
}
