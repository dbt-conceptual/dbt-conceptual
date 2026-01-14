import './IframeView.css'

export default function CoverageView() {
  return (
    <div className="iframe-container">
      <iframe
        src="/api/coverage"
        title="Coverage Report"
        className="full-iframe"
      />
    </div>
  )
}
