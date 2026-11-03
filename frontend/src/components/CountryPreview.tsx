import { Link } from 'react-router-dom'
import { useObservations } from '../hooks/useData'
import {
  formatIndicatorValue,
  getIndicatorLabel,
} from '../services/indicatorLabels'
import type { MapPlace } from '../services/mapData'
import type { MapCountry } from '../types/api'
import { TrendChart } from './TrendChart'
import { ErrorState, formatDate, Icon, Loading } from './UI'

interface CountryPreviewProps {
  place: MapPlace | null
  country: MapCountry | undefined
  indicator: string
  year: number
}

export function CountryPreview({
  place,
  country,
  indicator,
  year,
}: CountryPreviewProps) {
  const history = useObservations(country?.iso3 || '', `indicator=${indicator}`)
  const label = getIndicatorLabel(indicator)

  if (!place) {
    return (
      <aside className="country-preview country-preview-empty">
        <span className="preview-globe">
          <Icon name="globe" size={30} />
        </span>
        <h2>Country</h2>
        <p>Select country</p>
      </aside>
    )
  }

  return (
    <aside
      className="country-preview"
      aria-label="Selected country"
      aria-live="polite"
    >
      <div className="preview-heading">
        <h2>{country?.name || place.name}</h2>
        <p>{country?.region || 'No data'}</p>
      </div>
      <div className="preview-value">
        <strong>
          {formatIndicatorValue(country?.value ?? null, indicator)}
        </strong>
        <span>
          {label.name} · {year}
        </span>
      </div>
      {!country || country.value === null ? (
        <p className="preview-missing">No data · {year}</p>
      ) : null}
      {country ? (
        <>
          <div className="preview-trend">
            <h3>History</h3>
            <span>{label.unit}</span>
          </div>
          {history.isPending ? (
            <Loading />
          ) : history.error ? (
            <ErrorState error={history.error} />
          ) : (
            <TrendChart observations={history.data?.items || []} height={190} />
          )}
          <Link
            to={`/countries/${country.iso3}`}
            className="button preview-details"
          >
            Details
            <Icon name="arrow" size={16} />
          </Link>
          <details className="preview-source">
            <summary>Source</summary>
            <p>World Bank WDI</p>
            <p>
              Observation year: {country.observation_year || 'Not reported'}
            </p>
            <p>Collected: {formatDate(country.retrieved_at)}</p>
            <p>{country.income_group}</p>
            {country.dataset_version && (
              <p className="snapshot-reference">
                Dataset version: {country.dataset_version}
              </p>
            )}
          </details>
        </>
      ) : (
        <p className="preview-missing">Not imported</p>
      )}
    </aside>
  )
}
