import { useStore } from '../store';

interface ModelsTabProps {
  conceptId: string;
}

export function ModelsTab({ conceptId }: ModelsTabProps) {
  const { concepts } = useStore();
  const concept = concepts[conceptId];

  if (!concept) return null;

  // Helper to check if a model is inferred (discovered via lineage)
  const isInferred = (modelName: string) =>
    (concept.inferred_models || []).includes(modelName);

  // Render a model item with optional inferred indicator
  const renderModelItem = (model: string, layer: 'bronze' | 'silver' | 'gold') => {
    const inferred = isInferred(model);
    return (
      <div
        key={model}
        className={`model-item model-item-${layer}${inferred ? ' model-item-inferred' : ''}`}
        title={inferred ? 'Inferred from lineage (not explicitly tagged)' : undefined}
      >
        {inferred && <span className="model-item-lock" aria-label="Inferred">{'\u{1F512}'}</span>}
        <span className="model-item-name">{model}</span>
      </div>
    );
  };

  return (
    <div className="models-tab">
      {/* Bronze Models */}
      <div className="model-section">
        <div className="model-section-header">
          <span className="model-section-icon model-section-icon-bronze">{'\u2B21'}</span>
          <span className="model-section-title">Bronze Models</span>
          <span className="model-section-count">{concept.bronze_models.length}</span>
        </div>
        {concept.bronze_models.length > 0 ? (
          <div className="model-list">
            {concept.bronze_models.map((model) => renderModelItem(model, 'bronze'))}
          </div>
        ) : (
          <div className="model-empty">No bronze models (source tables)</div>
        )}
      </div>

      {/* Silver Models */}
      <div className="model-section">
        <div className="model-section-header">
          <span className="model-section-icon model-section-icon-silver">{'\u25C7'}</span>
          <span className="model-section-title">Silver Models</span>
          <span className="model-section-count">{concept.silver_models.length}</span>
        </div>
        {concept.silver_models.length > 0 ? (
          <div className="model-list">
            {concept.silver_models.map((model) => renderModelItem(model, 'silver'))}
          </div>
        ) : (
          <div className="model-empty">
            No silver models
            <div className="model-empty-hint">
              Add <code>meta.concept: {conceptId}</code> to a silver model
            </div>
          </div>
        )}
      </div>

      {/* Gold Models */}
      <div className="model-section">
        <div className="model-section-header">
          <span className="model-section-icon model-section-icon-gold">{'\u25C6'}</span>
          <span className="model-section-title">Gold Models</span>
          <span className="model-section-count">{concept.gold_models.length}</span>
        </div>
        {concept.gold_models.length > 0 ? (
          <div className="model-list">
            {concept.gold_models.map((model) => renderModelItem(model, 'gold'))}
          </div>
        ) : (
          <div className="model-empty">
            No gold models
            <div className="model-empty-hint">
              Add <code>meta.concept: {conceptId}</code> to a gold model
            </div>
          </div>
        )}
      </div>

      {/* Legend for inferred models */}
      {(concept.inferred_models || []).length > 0 && (
        <div className="model-legend">
          <span className="model-legend-icon">{'\u{1F512}'}</span>
          <span className="model-legend-text">Inferred from lineage</span>
        </div>
      )}

      {/* Help text */}
      <div className="model-help">
        <div className="model-help-title">How to associate models</div>
        <div className="model-help-text">
          Add the <code>meta</code> key to your dbt model's YAML:
        </div>
        <pre className="model-help-code">
{`models:
  - name: my_model
    meta:
      concept: ${conceptId}`}
        </pre>
      </div>
    </div>
  );
}
