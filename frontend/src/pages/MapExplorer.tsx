import { useState } from 'react'
import { CountryPreview } from '../components/CountryPreview'
import { RiskAssessment } from '../components/RiskAssessment'
import { WorldMap } from '../components/WorldMap'
import { ErrorState, Loading } from '../components/UI'
import {
  useCountries,
  useFreshness,
  useIndicators,
  useMapData,
  useWorldShapes,
} from '../hooks/useData'
import { getIndicatorLabel } from '../services/indicatorLabels'
import {
  getAvailableYears,
  getCountryChoices,
  type MapPlace,
} from '../services/mapData'

type View = 'risk' | 'indicators'

export function MapExplorer() {
  const countries = useCountries()
  const indicators = useIndicators()
  const freshness = useFreshness()
  const shapes = useWorldShapes()
  const [view, setView] = useState<View>('risk')
  const [indicator, setIndicator] = useState('NY.GDP.MKTP.KD.ZG')
  const [chosenYear, setChosenYear] = useState<number | null>(null)
  const [selectedPlace, setSelectedPlace] = useState<MapPlace | null>(null)

  const year =
    chosenYear ??
    freshness.data?.latest_observation_year ??
    new Date().getFullYear() - 1
  const importedCountries = countries.data?.items || []
  const showIndicators = view === 'indicators'
  const mapData = useMapData(
    indicator,
    year,
    showIndicators && Boolean(indicators.data?.length),
  )
  const availablePlaces = getCountryChoices(shapes.data, importedCountries)
  const availableYears = getAvailableYears(
    year,
    mapData.data?.available_years || [],
  )
  const selectedCountry = mapData.data?.countries.find(
    (country) => country.iso3 === selectedPlace?.iso3,
  )
  const selectedIndicator = indicators.data?.find((item) => item.code === indicator)
  const label = getIndicatorLabel(indicator, selectedIndicator)

  // Economic values are used only in the indicator view. They are never risk scores.
  const riskCountries = importedCountries.map((country) => ({
    iso3: country.iso3,
    value: null,
  }))
  const mapCountries = showIndicators
    ? mapData.data?.countries || []
    : riskCountries

  function chooseCountry(code: string) {
    const place = availablePlaces.find((country) => country.iso3 === code)
    setSelectedPlace(place || null)
  }

  if (countries.isPending || shapes.isPending) return <Loading />
  const error = countries.error || shapes.error
  if (error) return <ErrorState error={error} />

  return (
    <>
      <div className="risk-page-heading">
        <h1>Sovereign Credit Risk</h1>
      </div>
      <div className="risk-controls">
        <div className="view-toggle" role="group" aria-label="Map view">
          <button
            aria-pressed={!showIndicators}
            className={!showIndicators ? 'active' : ''}
            onClick={() => setView('risk')}
          >
            ML risk
          </button>
          <button
            aria-pressed={showIndicators}
            className={showIndicators ? 'active' : ''}
            onClick={() => setView('indicators')}
          >
            Indicators
          </button>
        </div>
        <label className="map-field risk-country-field">
          Country
          <select
            value={selectedPlace?.iso3 || ''}
            onChange={(event) => chooseCountry(event.target.value)}
          >
            <option value="">Select country</option>
            {availablePlaces.map((place) => (
              <option key={place.iso3} value={place.iso3}>
                {place.name}
              </option>
            ))}
          </select>
        </label>
        {showIndicators && (
          <>
            <label className="map-field risk-indicator-field">
              Indicator
              <select
                value={indicator}
                onChange={(event) => setIndicator(event.target.value)}
              >
                {indicators.data?.map((item) => (
                  <option key={item.code} value={item.code}>
                    {getIndicatorLabel(item.code, item).name}
                  </option>
                ))}
              </select>
            </label>
            <label className="map-field risk-year-field">
              Year
              <select
                value={year}
                onChange={(event) => setChosenYear(Number(event.target.value))}
              >
                {availableYears.map((availableYear) => (
                  <option key={availableYear} value={availableYear}>
                    {availableYear}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
      </div>
      {showIndicators && (
        <div className="indicator-caption">
          <strong>{label.name}</strong>
          <span>{label.unit}</span>
        </div>
      )}
      {showIndicators && indicators.error ? (
        <ErrorState error={indicators.error} />
      ) : showIndicators && mapData.error ? (
        <ErrorState error={mapData.error} />
      ) : showIndicators && mapData.isPending ? (
        <Loading />
      ) : (
        <div
          className={
            showIndicators ? 'map-and-country' : 'map-and-country risk-layout'
          }
        >
          <section
            className="map-surface"
            aria-label={
              showIndicators ? 'Economic indicators' : 'Sovereign risk map'
            }
          >
            <WorldMap
              shapes={shapes.data!}
              countries={mapCountries}
              indicator={indicator}
              unit={selectedIndicator?.unit}
              year={year}
              selectedCountry={selectedPlace?.iso3 || null}
              onSelectCountry={setSelectedPlace}
              mode={view}
            />
            <div className="map-source-line">
              <span>{importedCountries.length} countries loaded</span>
              <span>{showIndicators ? mapData.data?.source_name : 'ML risk'}</span>
            </div>
          </section>
          {showIndicators ? (
            <CountryPreview
              place={selectedPlace}
              country={selectedCountry}
              indicator={indicator}
              metadata={selectedIndicator}
              sourceName={mapData.data?.source_name}
              sourceUrl={mapData.data?.source_url}
              year={year}
            />
          ) : (
            <RiskAssessment country={selectedPlace} />
          )}
        </div>
      )}
    </>
  )
}
