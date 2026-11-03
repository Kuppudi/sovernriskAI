import { useQuery } from '@tanstack/react-query'
import { request } from '../services/api'
import { loadMapData, loadWorldShapes } from '../services/mapData'
import type {
  CountryPage,
  Freshness,
  Indicator,
  ModelStatus,
  ObservationPage,
} from '../types/api'

export const useCountries = () =>
  useQuery({
    queryKey: ['countries'],
    queryFn: () => request<CountryPage>('/api/countries?limit=250'),
  })
export const useIndicators = () =>
  useQuery({
    queryKey: ['indicators'],
    queryFn: () => request<Indicator[]>('/api/indicators'),
  })
export const useFreshness = () =>
  useQuery({
    queryKey: ['freshness'],
    queryFn: () => request<Freshness>('/api/data/freshness'),
  })
export const useModels = () =>
  useQuery({
    queryKey: ['models'],
    queryFn: () => request<ModelStatus>('/api/models/status'),
  })
export function useObservations(iso3: string, params = '') {
  return useQuery({
    queryKey: ['observations', iso3, params],
    enabled: Boolean(iso3),
    queryFn: () =>
      request<ObservationPage>(
        `/api/countries/${encodeURIComponent(iso3)}/indicators?limit=5000&${params}`,
      ),
  })
}

export function useMapData(indicator: string, year: number, enabled: boolean) {
  return useQuery({
    queryKey: ['map-data', indicator, year],
    queryFn: () => loadMapData(indicator, year),
    enabled,
  })
}

export function useWorldShapes() {
  return useQuery({
    queryKey: ['world-shapes'],
    queryFn: loadWorldShapes,
    staleTime: Infinity,
  })
}
