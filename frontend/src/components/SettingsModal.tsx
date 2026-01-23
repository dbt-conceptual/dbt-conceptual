import { useState, useEffect } from 'react';
import { Modal } from './Modal';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Settings {
  domains: Record<string, { name: string; color?: string }>;
  paths: {
    gold_paths: string[];
    silver_paths: string[];
    bronze_paths: string[];
  };
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
    }
  }, [isOpen]);

  const fetchSettings = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/settings');
      if (!response.ok) {
        throw new Error('Failed to fetch settings');
      }
      const data = await response.json();
      setSettings(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      if (!response.ok) {
        throw new Error('Failed to save settings');
      }
      setError(null);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  const addDomain = () => {
    if (!settings) return;
    const newId = `domain_${Date.now()}`;
    setSettings({
      ...settings,
      domains: {
        ...settings.domains,
        [newId]: { name: 'New Domain', color: '#4a9eff' },
      },
    });
  };

  const updateDomain = (id: string, field: 'name' | 'color', value: string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      domains: {
        ...settings.domains,
        [id]: { ...settings.domains[id], [field]: value },
      },
    });
  };

  const removeDomain = (id: string) => {
    if (!settings) return;
    const { [id]: removed, ...rest } = settings.domains;
    setSettings({
      ...settings,
      domains: rest,
    });
  };

  const updatePaths = (layer: 'gold_paths' | 'silver_paths' | 'bronze_paths', value: string) => {
    if (!settings) return;
    setSettings({
      ...settings,
      paths: {
        ...settings.paths,
        [layer]: value.split('\n').filter((p) => p.trim()),
      },
    });
  };

  if (isLoading && !settings) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title="Settings">
        <div className="settings-loading">Loading settings...</div>
      </Modal>
    );
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Settings"
      footer={
        <div className="modal-footer-actions">
          <button className="modal-btn modal-btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="modal-btn modal-btn-primary"
            onClick={handleSave}
            disabled={isLoading}
          >
            {isLoading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      }
    >
      {error && <div className="settings-error">{error}</div>}

      {settings && (
        <div className="settings-content">
          {/* Domains Section */}
          <div className="settings-section">
            <div className="settings-section-header">
              <h3 className="settings-section-title">Domains</h3>
              <button className="settings-add-btn" onClick={addDomain}>
                + Add Domain
              </button>
            </div>
            <div className="settings-domains">
              {Object.entries(settings.domains).map(([id, domain]) => (
                <div key={id} className="settings-domain">
                  <input
                    type="text"
                    className="settings-input settings-domain-name"
                    value={domain.name}
                    onChange={(e) => updateDomain(id, 'name', e.target.value)}
                    placeholder="Domain name"
                  />
                  <input
                    type="color"
                    className="settings-color"
                    value={domain.color || '#4a9eff'}
                    onChange={(e) => updateDomain(id, 'color', e.target.value)}
                  />
                  <button
                    className="settings-remove-btn"
                    onClick={() => removeDomain(id)}
                    title="Remove domain"
                    aria-label={`Remove domain ${domain.name}`}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Layer Paths Section */}
          <div className="settings-section">
            <h3 className="settings-section-title">Layer Paths</h3>
            <p className="settings-help">
              Define glob patterns for each layer. One pattern per line.
            </p>

            <div className="settings-path-group">
              <label className="settings-label">Gold Paths</label>
              <textarea
                className="settings-textarea"
                value={settings.paths.gold_paths.join('\n')}
                onChange={(e) => updatePaths('gold_paths', e.target.value)}
                placeholder="models/gold/**/*.sql"
                rows={3}
              />
            </div>

            <div className="settings-path-group">
              <label className="settings-label">Silver Paths</label>
              <textarea
                className="settings-textarea"
                value={settings.paths.silver_paths.join('\n')}
                onChange={(e) => updatePaths('silver_paths', e.target.value)}
                placeholder="models/silver/**/*.sql"
                rows={3}
              />
            </div>

            <div className="settings-path-group">
              <label className="settings-label">Bronze Paths</label>
              <textarea
                className="settings-textarea"
                value={settings.paths.bronze_paths.join('\n')}
                onChange={(e) => updatePaths('bronze_paths', e.target.value)}
                placeholder="models/bronze/**/*.sql"
                rows={3}
              />
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
