import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useCountries, useIndicators } from '../hooks/useData'
import { request } from '../services/api'
import type { Comparison as ComparisonData } from '../types/api'
import {
  Empty,
  ErrorState,
  Loading,
  ModelUnavailable,
  ObservationTable,
  PageHeading,
  Panel,
} from '../components/UI'
import { TrendChart } from '../components/TrendChart'

export function Comparison() {
  const countries = useCountries()
  const indicators = useIndicators()
  const [selected, setSelected] = useState<string[]>([])
  const [indicator, setIndicator] = useState('NY.GDP.MKTP.KD.ZG')
  const comparison = useQuery({
    queryKey: ['compare', selected, indicator],
    enabled: selected.length >= 2,
    queryFn: () =>
      request<ComparisonData>('/api/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ countries: selected, indicators: [indicator] }),
      }),
  })
  return (
    <>
      <PageHeading title="Country comparison" />
      {countries.error || indicators.error ? (
        <ErrorState error={countries.error || indicators.error} />
      ) : countries.isPending || indicators.isPending ? (
        <Loading />
      ) : (
        <>
          <Panel title="Countries" subtitle="Choose two to six countries">
            <div className="country-checks">
              {countries.data?.items.map((country) => (
                <label
                  key={country.iso3}
                  className={selected.includes(country.iso3) ? 'checked' : ''}
                >
                  <input
                    type="checkbox"
                    checked={selected.includes(country.iso3)}
                    disabled={
                      selected.length >= 6 && !selected.includes(country.iso3)
                    }
                    onChange={(e) =>
                      setSelected(
                        e.target.checked
                          ? [...selected, country.iso3]
                          : selected.filter((code) => code !== country.iso3),
                      )
                    }
                  />
                  {country.name}
                  <small>{country.iso3}</small>
                </label>
              ))}
            </div>
            <label className="field inline-field">
              Indicator
              <select
                value={indicator}
                onChange={(e) => setIndicator(e.target.value)}
              >
                {indicators.data?.map((item) => (
                  <option key={item.code} value={item.code}>
                    {item.name} ({item.unit})
                  </option>
                ))}
              </select>
            </label>
          </Panel>
          {selected.length < 2 ? (
            <Empty title="Choose at least two countries" />
          ) : comparison.isPending ? (
            <Loading />
          ) : comparison.error ? (
            <ErrorState error={comparison.error} />
          ) : (
            <>
              <Panel
                title={
                  indicators.data?.find((item) => item.code === indicator)
                    ?.name || 'Historical comparison'
                }
                subtitle={comparison.data?.items[0]?.source || 'Annual series'}
              >
                <TrendChart
                  observations={comparison.data?.items || []}
                  series={comparison.data?.countries.map((country) => ({
                    code: country.iso3,
                    label: country.name,
                  }))}
                />
              </Panel>
              {comparison.data?.countries.map((country) => (
                <Panel
                  key={country.iso3}
                  title={country.name}
                  subtitle={country.iso3}
                >
                  <ObservationTable
                    items={comparison.data.items.filter(
                      (item) => item.country_iso3 === country.iso3,
                    )}
                  />
                </Panel>
              ))}
            </>
          )}
        </>
      )}
      <Panel title="Model outputs">
        <ModelUnavailable />
      </Panel>
    </>
  )
}
