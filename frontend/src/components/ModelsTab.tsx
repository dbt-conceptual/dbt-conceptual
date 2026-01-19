import { useStore } from '../store';

interface ModelsTabProps {
  conceptId: string;
}

export function ModelsTab({ conceptId }: ModelsTabProps) {
  const { concepts } = useStore();
  const concept = concepts[conceptId];

  if (!concept) return null;

  return (
    <div className="models-tab">
      {/* Bronze Models */}
      <div className="model-section">
        <div className="model-section-header">
          <span className="model-section-icon model-section-icon-bronze">⬡</span>
          <span className="model-section-title">Bronze Models</span>
          <span className="model-section-count">{concept.bronze_models.length}</span>
        </div>
        {concept.bronze_models.length > 0 ? (
          <div className="model-list">
            {concept.bronze_models.map((model) => (
              <div key={model} className="model-item model-item-bronze">
                <span className="model-item-name">{model}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="model-empty">No bronze models (source tables)</div>
        )}
      </div>

      {/* Silver Models */}
      <div className="model-section">
        <div className="model-section-header">
          <span className="model-section-icon model-section-icon-silver">◇</span>
          <span className="model-section-title">Silver Models</span>
          <span className="model-section-count">{concept.silver_models.length}</span>
        </div>
        {concept.silver_models.length > 0 ? (
          <div className="model-list">
            {concept.silver_models.map((model) => (
              <div key={model} className="model-item model-item-silver">
                <span className="model-item-name">{model}</span>
              </div>
            ))}
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
          <span className="model-section-icon model-section-icon-gold">◆</span>
          <span className="model-section-title">Gold Models</span>
          <span className="model-section-count">{concept.gold_models.length}</span>
        </div>
        {concept.gold_models.length > 0 ? (
          <div className="model-list">
            {concept.gold_models.map((model) => (
              <div key={model} className="model-item model-item-gold">
                <span className="model-item-name">{model}</span>
              </div>
            ))}
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
