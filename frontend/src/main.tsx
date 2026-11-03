import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import { ErrorBoundary } from './components/UI'
import { Layout } from './components/Layout'
import { MapExplorer } from './pages/MapExplorer'
import { CountryAnalysis } from './pages/CountryAnalysis'
import { Comparison } from './pages/Comparison'
import { Explorer } from './pages/Explorer'
import { Reports } from './pages/Reports'
import './styles.css'

const client = new QueryClient({
  defaultOptions: { queries: { staleTime: 60_000, retry: 1 } },
})
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={client}>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<MapExplorer />} />
              <Route path="countries" element={<CountryAnalysis />} />
              <Route path="countries/:iso3" element={<CountryAnalysis />} />
              <Route path="compare" element={<Comparison />} />
              <Route path="reports" element={<Reports />} />
              <Route path="explorer" element={<Explorer />} />
              <Route
                path="*"
                element={
                  <>
                    <h1>Page not found</h1>
                    <Link to="/">Return to overview</Link>
                  </>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
