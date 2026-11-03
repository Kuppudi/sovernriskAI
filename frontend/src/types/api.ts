export interface Country {
  iso3: string
  name: string
  region: string
  income_group: string
}
export interface CountryPage {
  items: Country[]
  total: number
  limit: number
  offset: number
}
export interface Indicator {
  code: string
  name: string
  category: string
  unit: string
  source_id: number
  definition: string
}
export interface Observation {
  country_iso3: string
  indicator_code: string
  indicator_name: string
  unit: string
  observation_date: string
  value: number | null
  publication_date: string | null
  source_revision_date: string | null
  retrieved_at: string
  dataset_version: string
  source: string
  source_url: string
}
export interface ObservationPage {
  items: Observation[]
  total: number
  limit: number
  offset: number
}
export interface Freshness {
  latest_successful_refresh: string | null
  latest_observation_year: number | null
  countries_with_data: number
  observation_count: number
  failed_runs: number
  frequency: string
}
export interface ModelStatus {
  status: 'unavailable'
  risk_model: string
  downgrade_model: string
  predictions_available: number
  reason: string
}
export interface Report {
  country: Country
  generated_at: string
  executive_summary: string
  latest_indicators: Observation[]
  limitations: string[]
  model_status: ModelStatus
}
export interface Comparison {
  countries: Country[]
  items: Observation[]
  model_status: string
}

export interface MapCountry extends Country {
  value: number | null
  observation_year: number | null
  retrieved_at: string | null
  dataset_version: string | null
}

export interface MapData {
  indicator: Indicator
  year: number
  available_years: number[]
  countries: MapCountry[]
  source_name: string
  source_url: string
}
