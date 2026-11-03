import { Component, type ErrorInfo, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Country, Observation } from '../types/api'

export const formatNumber = (value: number | null, digits = 2) =>
  value === null
    ? 'Not reported'
    : value.toLocaleString(undefined, { maximumFractionDigits: digits })
export const formatDate = (value: string | null | undefined) =>
  value
    ? new Date(value).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : 'Not refreshed'

export function Icon({
  name = 'grid',
  size = 19,
}: {
  name?: string
  size?: number
}) {
  const paths: Record<string, ReactNode> = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    globe: (
      <>
        <circle cx="12" cy="12" r="9" />
        <ellipse cx="12" cy="12" rx="4" ry="9" />
        <path d="M3 12h18M5 7h14M5 17h14" />
      </>
    ),
    chart: (
      <>
        <path d="M4 3v17h17M8 16v-5M13 16V6M18 16V9" />
      </>
    ),
    report: (
      <>
        <path d="M6 3h9l4 4v14H6zM14 3v5h5M9 12h7M9 16h7" />
      </>
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 5 5" />
      </>
    ),
    arrow: <path d="M5 12h14m-5-5 5 5-5 5" />,
    download: (
      <>
        <path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5" />
      </>
    ),
    shield: (
      <>
        <path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z" />
        <path d="M12 8v5m0 3h.01" />
      </>
    ),
  }
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.chart}
    </svg>
  )
}

export function PageHeading({
  title,
  action,
}: {
  title: string
  action?: ReactNode
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
      </div>
      {action}
    </div>
  )
}
export function Panel({
  title,
  subtitle,
  children,
  className = '',
}: {
  title: string
  subtitle?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <h2>{title}</h2>
        {subtitle && <p>{subtitle}</p>}
      </div>
      {children}
    </section>
  )
}
export function Empty({
  title = 'No data',
  children,
}: {
  title?: string
  children?: ReactNode
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon name="globe" size={28} />
      </span>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
    </div>
  )
}
export function Loading() {
  return (
    <div className="skeleton-grid" role="status" aria-label="Loading data">
      {[1, 2, 3].map((i) => (
        <div key={i} className="skeleton" />
      ))}
      <span className="sr-only">Loading data…</span>
    </div>
  )
}
export function ErrorState({ error }: { error: Error | null }) {
  const client = useQueryClient()
  return (
    <div className="error-state" role="alert">
      <h3>Data could not be loaded</h3>
      <p>{error?.message || 'An unexpected error occurred.'}</p>
      <button
        className="button secondary"
        onClick={() => void client.invalidateQueries()}
      >
        Try again
      </button>
    </div>
  )
}
export function CountrySelect({
  countries,
  value,
  onChange,
  label = 'Country',
}: {
  countries: Country[]
  value: string
  onChange: (value: string) => void
  label?: string
}) {
  return (
    <label className="field">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={!countries.length}
      >
        <option value="">Select a country</option>
        {countries.map((c) => (
          <option key={c.iso3} value={c.iso3}>
            {c.name} · {c.iso3}
          </option>
        ))}
      </select>
    </label>
  )
}
export function ModelUnavailable() {
  return (
    <div className="model-state">
      <span className="empty-icon">
        <Icon name="shield" size={25} />
      </span>
      <div>
        <span className="badge neutral">Model Not Trained</span>
        <h3>Predictions need a validated foundation.</h3>
        <p>
          Risk scores, twelve-month downgrade probabilities, risk rankings, and
          feature contributions will appear after supervised models are trained
          and validated using authorized rating data.
        </p>
        <div className="model-facts">
          <span>
            Risk score <b>Unavailable</b>
          </span>
          <span>
            Downgrade probability <b>Unavailable</b>
          </span>
          <span>
            Model version <b>Not available</b>
          </span>
        </div>
      </div>
    </div>
  )
}
export function ObservationTable({ items }: { items: Observation[] }) {
  if (!items.length) return <Empty title="No observations for this selection" />
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Indicator</th>
            <th>Year</th>
            <th>Value</th>
            <th>Unit</th>
            <th>Source / retrieved</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={`${item.country_iso3}-${item.indicator_code}-${item.observation_date}`}
            >
              <td>
                <strong>{item.indicator_name}</strong>
                <small>{item.indicator_code}</small>
              </td>
              <td>{item.observation_date.slice(0, 4)}</td>
              <td className="numeric">{formatNumber(item.value)}</td>
              <td>{item.unit}</td>
              <td>
                <a href={item.source_url} target="_blank" rel="noreferrer">
                  {item.source}
                </a>
                <small>{formatDate(item.retrieved_at)}</small>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
export class ErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false }
  static getDerivedStateFromError() {
    return { failed: true }
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI rendering failed', error, info.componentStack)
  }
  render() {
    return this.state.failed ? (
      <main className="content">
        <h1>This view could not be displayed</h1>
        <p>Reload the page to try again.</p>
        <button className="button" onClick={() => window.location.reload()}>
          Reload
        </button>
      </main>
    ) : (
      this.props.children
    )
  }
}
