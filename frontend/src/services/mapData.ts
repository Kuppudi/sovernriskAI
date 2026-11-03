import type { FeatureCollection, Geometry } from 'geojson'
import type { Country, MapData } from '../types/api'
import { request } from './api'

export interface MapPlace {
  iso3: string
  name: string
}

export type WorldShapes = FeatureCollection<Geometry, MapPlace>

interface ValueRange {
  minimum: number
  maximum: number
}

export const mapColors = ['#d2e5f5', '#a5cce8', '#73add6', '#428ac0', '#1b5e97']
export const missingDataColor = '#e4e9ed'

export async function loadWorldShapes(): Promise<WorldShapes> {
  const response = await fetch('/maps/world-countries.json')
  if (!response.ok) throw new Error('The world map could not be loaded.')
  return response.json()
}

export function loadMapData(indicator: string, year: number): Promise<MapData> {
  const filters = new URLSearchParams({ indicator, year: String(year) })
  return request<MapData>(`/api/data/map?${filters}`)
}

export function getCountryChoices(
  shapes: WorldShapes | undefined,
  countries: Country[],
): MapPlace[] {
  const places = new Map<string, MapPlace>()

  for (const feature of shapes?.features || []) {
    places.set(feature.properties.iso3, feature.properties)
  }
  // Imported countries stay selectable even when too small for the map outline.
  for (const country of countries) {
    places.set(country.iso3, { iso3: country.iso3, name: country.name })
  }

  return Array.from(places.values()).sort((first, second) =>
    first.name.localeCompare(second.name),
  )
}

export function getAvailableYears(
  selectedYear: number,
  savedYears: number[],
): number[] {
  const years = new Set([selectedYear])
  for (const year of savedYears) years.add(year)
  return Array.from(years).sort((first, second) => second - first)
}

export function getValueRange(values: Array<number | null>): ValueRange | null {
  const reportedValues = values.filter((value) => value !== null)
  if (!reportedValues.length) return null
  return {
    minimum: Math.min(...reportedValues),
    maximum: Math.max(...reportedValues),
  }
}

export function getMapColor(
  value: number | null,
  range: ValueRange | null,
): string {
  if (value === null || range === null) return missingDataColor
  if (range.minimum === range.maximum) return mapColors[2]

  const position = (value - range.minimum) / (range.maximum - range.minimum)
  const colorIndex = Math.min(
    Math.floor(position * mapColors.length),
    mapColors.length - 1,
  )
  return mapColors[colorIndex]
}
