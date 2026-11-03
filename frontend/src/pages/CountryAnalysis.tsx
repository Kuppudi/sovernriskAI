import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useCountries, useIndicators, useObservations } from '../hooks/useData'
import {
  CountrySelect,
  Empty,
  ErrorState,
  formatNumber,
  Loading,
  ModelUnavailable,
  ObservationTable,
  PageHeading,
  Panel,
} from '../components/UI'
import { TrendChart } from '../components/TrendChart'

export function CountryAnalysis() {
  const { iso3: rawIso3 = '' } = useParams()
  const iso3 = rawIso3.toUpperCase()
  const navigate = useNavigate()
  const countries = useCountries()
  const indicators = useIndicators()
  const [indicator, setIndicator] = useState('NY.GDP.MKTP.KD.ZG')
  const data = useObservations(iso3)
  const country = countries.data?.items.find((c) => c.iso3 === iso3)
  if (countries.isPending) return <Loading />
  if (countries.error) return <ErrorState error={countries.error} />
  const latest = new Map<
    string,
    NonNullable<typeof data.data>['items'][number]
  >()
  for (const item of data.data?.items || [])
    if (item.value !== null) latest.set(item.indicator_code, item)
  return (
    <>
      <PageHeading
        title={country?.name || 'Country fundamentals'}
        action={
          iso3 ? (
            <Link className="button secondary" to={`/reports?country=${iso3}`}>
              Report
            </Link>
          ) : undefined
        }
      />
      <div className="filter-bar">
        <CountrySelect
          countries={countries.data?.items || []}
          value={iso3}
          onChange={(value) =>
            navigate(value ? `/countries/${value}` : '/countries')
          }
        />
      </div>
      {!iso3 ? (
        <Empty title="Select country" />
      ) : data.isPending ? (
        <Loading />
      ) : data.error ? (
        <ErrorState error={data.error} />
      ) : (
        <>
          <div className="indicator-grid">
            {[...latest.values()].map((item) => (
              <div className="indicator-card" key={item.indicator_code}>
                <span>{item.indicator_name}</span>
                <strong>{formatNumber(item.value)}</strong>
                <small>
                  {item.unit} · {item.observation_date.slice(0, 4)}
                </small>
              </div>
            ))}
          </div>
          <div className="notice">
            Latest available non-null values are shown above. Years may differ;
            later missing values remain visible in the table. Debt, reserves,
            governance, and corruption series have not yet been integrated.
          </div>
          <Panel
            title="History"
            subtitle="Annual observations · missing values are shown as gaps"
          >
            <label className="field inline-field">
              Indicator
              <select
                value={indicator}
                onChange={(e) => setIndicator(e.target.value)}
              >
                {(indicators.data || []).map((item) => (
                  <option key={item.code} value={item.code}>
                    {item.name} ({item.unit})
                  </option>
                ))}
              </select>
            </label>
            {indicators.error && <ErrorState error={indicators.error} />}
            <TrendChart
              observations={(data.data?.items || []).filter(
                (item) => item.indicator_code === indicator,
              )}
            />
          </Panel>
          <Panel title="Sovereign risk prediction">
            <ModelUnavailable />
          </Panel>
          <Panel
            title="Data & provenance"
            subtitle="Observation years, units, retrieval dates, and original source"
          >
            <ObservationTable items={data.data?.items || []} />
          </Panel>
        </>
      )}
    </>
  )
}
