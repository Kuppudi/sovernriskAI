import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useCountries } from '../hooks/useData'
import { request } from '../services/api'
import type { Report } from '../types/api'
import {
  CountrySelect,
  Empty,
  ErrorState,
  formatDate,
  Icon,
  Loading,
  ModelUnavailable,
  ObservationTable,
  PageHeading,
  Panel,
} from '../components/UI'

export function Reports() {
  const countries = useCountries()
  const [params, setParams] = useSearchParams()
  const country = params.get('country') || ''
  const report = useQuery({
    queryKey: ['report', country],
    enabled: Boolean(country),
    queryFn: () =>
      request<Report>(`/api/countries/${encodeURIComponent(country)}/report`),
  })
  return (
    <>
      <PageHeading
        title={
          report.data
            ? `${report.data.country.name} · Country report`
            : 'Country reports'
        }
        action={
          report.data ? (
            <button
              className="button secondary print-hide"
              onClick={() => window.print()}
            >
              <Icon name="download" />
              Print / save PDF
            </button>
          ) : undefined
        }
      />
      <div className="filter-bar print-hide">
        <CountrySelect
          countries={countries.data?.items || []}
          value={country}
          onChange={(value) => setParams(value ? { country: value } : {})}
        />
      </div>
      {countries.error ? (
        <ErrorState error={countries.error} />
      ) : !country ? (
        <Empty title="Select country" />
      ) : report.isPending ? (
        <Loading />
      ) : report.error ? (
        <ErrorState error={report.error} />
      ) : report.data ? (
        <>
          <div className="report-meta">
            {report.data.country.iso3} · {report.data.country.region} ·{' '}
            {report.data.country.income_group}
            <span>Generated {formatDate(report.data.generated_at)}</span>
          </div>
          <Panel
            title="Executive summary"
            subtitle="Generated from database values; no language model"
          >
            <p className="report-summary">{report.data.executive_summary}</p>
          </Panel>
          <Panel
            title="Latest available economic indicators"
            subtitle="Latest non-missing observation for each available series"
          >
            <ObservationTable items={report.data.latest_indicators} />
          </Panel>
          <Panel title="Sovereign risk outlook">
            <ModelUnavailable />
          </Panel>
          <Panel title="Missing data & limitations">
            <ul className="limitations">
              {report.data.limitations.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <p className="definition">
              Each observation links to its provider and includes its
              observation year and retrieval date. Public API responses also
              include the dataset version and source revision date, when
              provided.
            </p>
          </Panel>
        </>
      ) : null}
    </>
  )
}
