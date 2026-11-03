import { useModels } from '../hooks/useData'
import type { MapPlace } from '../services/mapData'

interface RiskAssessmentProps {
  country: MapPlace | null
}

export function RiskAssessment({ country }: RiskAssessmentProps) {
  const model = useModels()

  let status = 'Not trained'
  if (model.isPending) status = 'Loading'
  if (model.isError) status = 'Unavailable'

  return (
    <aside className="risk-assessment" aria-label="ML risk assessment">
      <div className="risk-card-heading">
        <span className="risk-ml-label">ML</span>
        <span className="risk-model-status" role="status">
          {status}
        </span>
      </div>
      <h2>Sovereign risk score</h2>
      <div className="risk-score" aria-label="Risk score unavailable">
        —
      </div>
      <span className="risk-score-state">Unavailable</span>
      <dl className="risk-summary">
        <div>
          <dt>Country</dt>
          <dd>{country?.name || '—'}</dd>
        </div>
        <div>
          <dt>12m downgrade</dt>
          <dd>Unavailable</dd>
        </div>
        <div>
          <dt>Model</dt>
          <dd>{model.isSuccess ? 'Not trained' : '—'}</dd>
        </div>
      </dl>
      <details className="risk-model-details">
        <summary>Model details</summary>
        <p>{model.data?.reason || 'Model status unavailable.'}</p>
        <p>
          Loan repayment risk requires a validated target and repayment or
          default history. Downgrade probability is a separate measure.
        </p>
      </details>
    </aside>
  )
}
