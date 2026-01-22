import { useState } from 'react';
import { SettingsModal } from './SettingsModal';
import { SearchBar } from './SearchBar';
import { LogoMark } from './LogoMark';

interface ToolbarProps {
  onNavigateToNode?: (id: string, type: 'concept' | 'relationship') => void;
}

export function Toolbar({ onNavigateToNode }: ToolbarProps) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <>
      <div className="toolbar">
        <div className="toolbar-left">
          <div className="logo">
            <LogoMark size={26} />
            <span className="logo-text">dbt-conceptual</span>
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
