import { useState } from 'react';
import { SettingsModal } from './SettingsModal';
import { SearchBar } from './SearchBar';
import { LogoMark } from './LogoMark';
import { useStore } from '../store';

interface ToolbarProps {
  onNavigateToNode?: (id: string, type: 'concept' | 'relationship') => void;
}

export function Toolbar({ onNavigateToNode }: ToolbarProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { isLoading, isSyncing } = useStore();

  const showSpinner = isLoading || isSyncing;

  return (
    <>
      <div className="toolbar">
        <div className="toolbar-left">
          <div className="logo">
            <LogoMark size={26} />
            <span className="logo-text">dbt-conceptual</span>
            {showSpinner && (
              <span className="toolbar-spinner" aria-label="Loading">
                <span className="spinner" />
              </span>
            )}
          </div>
        </div>
        <div className="toolbar-center">
          <SearchBar onNavigate={onNavigateToNode} />
        </div>
        <div className="toolbar-actions">
          <button
            className="toolbar-btn"
            onClick={() => setIsSettingsOpen(true)}
            title="Settings"
            aria-label="Open settings"
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
