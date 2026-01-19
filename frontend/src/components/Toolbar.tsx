import { useState } from 'react';
import { SettingsModal } from './SettingsModal';

export function Toolbar() {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <>
      <div className="toolbar">
        <div className="toolbar-title">dbt-conceptual</div>
        <div className="toolbar-actions">
          <button
            className="toolbar-btn"
            onClick={() => setIsSettingsOpen(true)}
            title="Settings"
          >
            ⚙
          </button>
        </div>
      </div>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </>
  );
}
