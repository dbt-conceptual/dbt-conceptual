import './IframeView.css'

export default function BusMatrixView() {
  return (
    <div className="iframe-container">
      <iframe
        src="/api/bus-matrix"
        title="Bus Matrix"
        className="full-iframe"
      />
    </div>
  )
}
