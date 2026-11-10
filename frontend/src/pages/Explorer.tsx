import { useState } from 'react'
import { useCountries, useIndicators, useObservations } from '../hooks/useData'
import {
  CountrySelect,
  Empty,
  ErrorState,
  Icon,
  Loading,
  ObservationTable,
  PageHeading,
  Panel,
} from '../components/UI'
import { TrendChart } from '../components/TrendChart'

export function Explorer() {
  const countries = useCountries()
  const indicators = useIndicators()
  const [country, setCountry] = useState('')
  const [indicator, setIndicator] = useState('NY.GDP.MKTP.KD.ZG')
  const [start, setStart] = useState(2015)
  const [end, setEnd] = useState(new Date().getFullYear() - 1)
  const valid =
    Number.isInteger(start) &&
    Number.isInteger(end) &&
    start >= 1960 &&
    end <= 2100 &&
    start <= end
  const params = new URLSearchParams({
    indicator,
    start_year: String(start),
    end_year: String(end),
  }).toString()
  const data = useObservations(valid ? country : '', params)
  const definition = indicators.data?.find((item) => item.code === indicator)
  return (
    <>
      <PageHeading
        title="Data"
        action={
          country && valid ? (
            <a
              className="button secondary"
              href={`/api/countries/${country}/indicators.csv?${params}`}
              download
            >
              <Icon name="download" />
              Export CSV
            </a>
          ) : undefined
        }
      />
      {countries.error || indicators.error ? (
        <ErrorState error={countries.error || indicators.error} />
      ) : (
        <div className="filter-bar">
          <CountrySelect
            countries={countries.data?.items || []}
            value={country}
            onChange={setCountry}
          />
          <label className="field">
            Indicator
            <select
              value={indicator}
              onChange={(e) => setIndicator(e.target.value)}
            >
              {indicators.data?.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field year-field">
            From
            <input
              type="number"
              min="1960"
              max="2100"
              value={start}
              onChange={(e) => setStart(Number(e.target.value))}
            />
          </label>
          <label className="field year-field">
            Through
            <input
              type="number"
              min="1960"
              max="2100"
              value={end}
              onChange={(e) => setEnd(Number(e.target.value))}
            />
          </label>
        </div>
      )}
      {!valid && (
        <div className="notice" role="alert">
          Choose an ordered year range between 1960 and 2100.
        </div>
      )}
      {!country ? (
        <Empty title="Select country" />
      ) : !valid ? null : data.isPending ? (
        <Loading />
      ) : data.error ? (
        <ErrorState error={data.error} />
      ) : (
        <>
          <Panel
            title={definition?.name || indicator}
            subtitle={definition?.unit}
          >
            <TrendChart observations={data.data?.items || []} />
          </Panel>
          <Panel
            title="Historical observations"
            subtitle={`${data.data?.total || 0} records · missing values remain empty in CSV`}
          >
            <ObservationTable items={data.data?.items || []} />
          </Panel>
          {definition && (
            <Panel title="Indicator definition" subtitle={definition.code}>
              <p className="definition">{definition.definition}</p>
            </Panel>
          )}
        </>
      )}
    </>
  )
}
