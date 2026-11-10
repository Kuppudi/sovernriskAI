import { useMemo, useState } from 'react'
import { geoNaturalEarth1, geoPath } from 'd3-geo'
import { formatIndicatorValue } from '../services/indicatorLabels'
import {
  getMapColor,
  getValueRange,
  mapColors,
  type MapPlace,
  type WorldShapes,
} from '../services/mapData'

interface WorldMapProps {
  shapes: WorldShapes
  countries: { iso3: string; value: number | null }[]
  indicator: string
  unit?: string
  year: number
  selectedCountry: string | null
  onSelectCountry: (country: MapPlace) => void
  mode?: 'risk' | 'indicators'
}

export function WorldMap({
  shapes,
  countries,
  indicator,
  unit,
  year,
  selectedCountry,
  onSelectCountry,
  mode = 'indicators',
}: WorldMapProps) {
  const [hoveredCountry, setHoveredCountry] = useState<MapPlace | null>(null)
  const countryValues = new Map(
    countries.map((country) => [country.iso3, country.value]),
  )
  const range = getValueRange(countries.map((country) => country.value))

  function valueLabel(value: number | null) {
    if (mode === 'risk') return 'Score unavailable'
    return formatIndicatorValue(value, indicator, unit)
  }

  // Country outlines are static. Recalculate their SVG paths only when the shapes change.
  const countryPaths = useMemo(() => {
    const projection = geoNaturalEarth1().fitExtent(
      [
        [16, 12],
        [984, 488],
      ],
      shapes,
    )
    const drawPath = geoPath(projection)
    return shapes.features.map((feature) => ({
      country: feature.properties,
      path: drawPath(feature) || '',
    }))
  }, [shapes])

  return (
    <div className="world-map">
      {hoveredCountry && (
        <div className="map-tooltip" role="status">
          <strong>{hoveredCountry.name}</strong>
          <span>
            {valueLabel(countryValues.get(hoveredCountry.iso3) ?? null)}
            {mode === 'indicators' ? ` · ${year}` : ''}
          </span>
        </div>
      )}
      <svg
        viewBox="0 0 1000 500"
        role="group"
        aria-label={
          mode === 'risk' ? 'Sovereign risk map' : `Indicator map for ${year}`
        }
      >
        {countryPaths.map(({ country, path }, index) => {
          const value = countryValues.get(country.iso3) ?? null
          const isSelected = selectedCountry === country.iso3

          function selectCountry() {
            onSelectCountry(country)
          }

          return (
            <path
              key={`${country.iso3}-${index}`}
              d={path}
              fill={getMapColor(value, range)}
              className={isSelected ? 'map-country selected' : 'map-country'}
              role="button"
              tabIndex={countryValues.has(country.iso3) ? 0 : -1}
              aria-label={`${country.name}: ${valueLabel(value)}${mode === 'indicators' ? ` in ${year}` : ''}`}
              aria-pressed={isSelected}
              onClick={selectCountry}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  selectCountry()
                }
              }}
              onMouseEnter={() => setHoveredCountry(country)}
              onMouseLeave={() => setHoveredCountry(null)}
              onFocus={() => setHoveredCountry(country)}
              onBlur={() => setHoveredCountry(null)}
            >
              <title>
                {country.name}: {valueLabel(value)}
              </title>
            </path>
          )
        })}
      </svg>
      <div className="map-legend" aria-label="Map color legend">
        {mode === 'risk' ? (
          <span>Scores unavailable</span>
        ) : range ? (
          <div className="legend-scale">
            <div className="legend-colors">
              {mapColors.map((color) => (
                <span key={color} style={{ background: color }} />
              ))}
            </div>
            <div className="legend-values">
              <span>{formatIndicatorValue(range.minimum, indicator, unit)}</span>
              <span>{formatIndicatorValue(range.maximum, indicator, unit)}</span>
            </div>
          </div>
        ) : (
          <span>No reported values for this year</span>
        )}
        {mode === 'indicators' && (
          <div className="legend-missing">
            <i />
            No data
          </div>
        )}
      </div>
    </div>
  )
}
