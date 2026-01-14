import { useState, useEffect } from 'react'
import { State } from './types'
import GraphEditor from './components/GraphEditor'
import CoverageView from './components/CoverageView'
import BusMatrixView from './components/BusMatrixView'
import './App.css'

type Tab = 'editor' | 'coverage' | 'bus-matrix'

function App() {
  const [state, setState] = useState<State | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('editor')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // Load initial state
  useEffect(() => {
    loadState()
  }, [])

  const loadState = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch('/api/state')
      if (!response.ok) {
        throw new Error('Failed to load state')
      }
      const data = await response.json()
      setState(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const saveState = async () => {
    if (!state) return

    try {
      setSaving(true)
      setError(null)
      const response = await fetch('/api/state', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(state),
      })

      if (!response.ok) {
        throw new Error('Failed to save state')
      }

      const result = await response.json()
      console.log('Saved:', result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <p>Loading conceptual model...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={loadState}>Retry</button>
      </div>
    )
  }

  if (!state) {
    return <div className="error-container">No state loaded</div>
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>dbt-conceptual UI</h1>
        <div className="header-actions">
          <button
            onClick={saveState}
            disabled={saving}
            className="save-button"
          >
            {saving ? 'Saving...' : 'Save to conceptual.yml'}
          </button>
          <button onClick={loadState} className="reload-button">
            Reload
          </button>
        </div>
      </header>

      <nav className="tabs">
        <button
          className={activeTab === 'editor' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('editor')}
        >
          Editor
        </button>
        <button
          className={activeTab === 'coverage' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('coverage')}
        >
          Coverage Report
        </button>
        <button
          className={activeTab === 'bus-matrix' ? 'tab active' : 'tab'}
          onClick={() => setActiveTab('bus-matrix')}
        >
          Bus Matrix
        </button>
      </nav>

      <main className="tab-content">
        {activeTab === 'editor' && (
          <GraphEditor state={state} setState={setState} />
        )}
        {activeTab === 'coverage' && <CoverageView />}
        {activeTab === 'bus-matrix' && <BusMatrixView />}
      </main>
    </div>
  )
}

export default App
