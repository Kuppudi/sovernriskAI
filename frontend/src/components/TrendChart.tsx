import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Observation } from '../types/api'
import { Empty } from './UI'

const colors = [
  '#1d8c77',
  '#527fc7',
  '#c58c42',
  '#875caa',
  '#be6373',
  '#57777c',
]
export function TrendChart({
  observations,
  series,
  height = 285,
}: {
  observations: Observation[]
  series?: { code: string; label: string }[]
  height?: number
}) {
  if (!observations.length || observations.every((item) => item.value === null))
    return (
      <Empty title="No reported values in this selection">
        No numeric observations were reported for this series and year range.
        Missing values have not been filled.
      </Empty>
    )
  const lines = series || [
    { code: observations[0].country_iso3, label: observations[0].country_iso3 },
  ]
  const years = new Map<string, Record<string, string | number | null>>()
  for (const observation of observations) {
    const year = observation.observation_date.slice(0, 4)
    const row = years.get(year) || { year }
    row[observation.country_iso3] = observation.value
    years.set(year, row)
  }
  const data = [...years.values()].sort((a, b) =>
    String(a.year).localeCompare(String(b.year)),
  )
  return (
    <div
      className="chart"
      role="img"
      aria-label={`Historical trend for ${observations[0].indicator_name}. Data also available in tables and CSV.`}
    >
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={{ top: 15, right: 12, left: 0, bottom: 6 }}
        >
          <CartesianGrid
            strokeDasharray="3 4"
            vertical={false}
            stroke="#e7edf1"
          />
          <XAxis
            dataKey="year"
            tickLine={false}
            axisLine={false}
            fontSize={11}
            tickMargin={12}
          />
          <YAxis tickLine={false} axisLine={false} fontSize={11} width={56} />
          <Tooltip
            contentStyle={{
              borderRadius: 10,
              border: '1px solid #e3e9ee',
              fontSize: 12,
            }}
          />
          {lines.length > 1 && <Legend />}
          {lines.map((line, index) => (
            <Line
              key={line.code}
              name={line.label}
              dataKey={line.code}
              type="monotone"
              stroke={colors[index % colors.length]}
              strokeWidth={2.5}
              dot={{ r: 3, strokeWidth: 0 }}
              activeDot={{ r: 5 }}
              connectNulls={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
