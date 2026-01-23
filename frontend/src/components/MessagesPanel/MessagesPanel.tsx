import { useStore } from '../../store';
import type { MessageSeverity } from '../../types';

const severityIcons: Record<MessageSeverity, string> = {
  error: '\u2298', // ⊘
  warning: '\u26A0', // ⚠
  info: '\u2139', // ℹ
};

export function MessagesPanel() {
  const {
    messages,
    messageFilters,
    messagesPanelExpanded,
    messageCounts,
    isSyncing,
    toggleMessageFilter,
    toggleMessagesPanel,
    sync,
    selectConcept,
    selectRelationship,
  } = useStore();

  // Filter messages based on active filters
  const filteredMessages = messages.filter((msg) => messageFilters[msg.severity]);

  // Handle clicking on a message to navigate to the element
  const handleMessageClick = (elementType?: string, elementId?: string) => {
    if (!elementType || !elementId) return;
    if (elementType === 'concept') {
      selectConcept(elementId);
    } else if (elementType === 'relationship') {
      selectRelationship(elementId);
    }
  };

  // Collapsed bar view
  if (!messagesPanelExpanded) {
    const totalCount = messages.length;
    const hasErrors = messageCounts.error > 0;
    const hasWarnings = messageCounts.warning > 0;

    // Handle click on collapsed bar - expand panel, but not if clicking sync button
    const handleBarClick = (e: React.MouseEvent) => {
      // Don't expand if clicking the sync button
      if ((e.target as HTMLElement).closest('.messages-bar-sync')) {
        return;
      }
      toggleMessagesPanel();
    };

    return (
      <div
        className="messages-bar"
        onClick={handleBarClick}
        title="Click to expand messages panel"
      >
        <div className="messages-bar-actions">
          <button
            className="icon-btn"
            onClick={toggleMessagesPanel}
            title="Expand messages panel"
            aria-label="Expand messages panel"
          >
            {'\u25B6'} {/* ▶ */}
          </button>
          <button
            className="icon-btn messages-bar-sync"
            onClick={(e) => {
              e.stopPropagation();
              sync();
            }}
            disabled={isSyncing}
            title="Sync with dbt project"
            aria-label={isSyncing ? 'Syncing with dbt project' : 'Sync with dbt project'}
          >
            {isSyncing ? '\u23F3' : '\u21BB'} {/* ⏳ or ↻ */}
          </button>
        </div>
        {totalCount > 0 && (
          <span className={`messages-bar-count ${!hasErrors && !hasWarnings ? 'muted' : ''}`}>
            {totalCount}
          </span>
        )}
        {hasErrors && (
          <div className="messages-bar-badge error">!</div>
        )}
        {!hasErrors && hasWarnings && (
          <div className="messages-bar-badge warning">!</div>
        )}
      </div>
    );
  }

  // Expanded panel view
  return (
    <div className="messages-panel">
      <div className="messages-panel-header">
        <h3>Messages</h3>
        <div className="messages-panel-header-actions">
          <button
            className="icon-btn"
            onClick={sync}
            disabled={isSyncing}
            title="Sync with dbt project"
            aria-label={isSyncing ? 'Syncing with dbt project' : 'Sync with dbt project'}
          >
            {isSyncing ? '\u23F3' : '\u21BB'} {/* ⏳ or ↻ */}
          </button>
          <button
            className="icon-btn"
            onClick={toggleMessagesPanel}
            title="Collapse messages panel"
            aria-label="Collapse messages panel"
          >
            {'\u25C0'} {/* ◀ */}
          </button>
        </div>
      </div>

      <div className="messages-filters" role="group" aria-label="Message filters">
        <button
          className={`filter-toggle ${messageFilters.error ? 'selected error' : 'unselected'}`}
          onClick={() => toggleMessageFilter('error')}
          aria-label={`${messageFilters.error ? 'Hide' : 'Show'} errors (${messageCounts.error})`}
          aria-pressed={messageFilters.error}
        >
          <span className="filter-toggle-icon" aria-hidden="true">{severityIcons.error}</span>
          <span className="filter-toggle-count">{messageCounts.error}</span>
        </button>
        <button
          className={`filter-toggle ${messageFilters.warning ? 'selected warning' : 'unselected'}`}
          onClick={() => toggleMessageFilter('warning')}
          aria-label={`${messageFilters.warning ? 'Hide' : 'Show'} warnings (${messageCounts.warning})`}
          aria-pressed={messageFilters.warning}
        >
          <span className="filter-toggle-icon" aria-hidden="true">{severityIcons.warning}</span>
          <span className="filter-toggle-count">{messageCounts.warning}</span>
        </button>
        <button
          className={`filter-toggle ${messageFilters.info ? 'selected info' : 'unselected'}`}
          onClick={() => toggleMessageFilter('info')}
          aria-label={`${messageFilters.info ? 'Hide' : 'Show'} info messages (${messageCounts.info})`}
          aria-pressed={messageFilters.info}
        >
          <span className="filter-toggle-icon" aria-hidden="true">{severityIcons.info}</span>
          <span className="filter-toggle-count">{messageCounts.info}</span>
        </button>
      </div>

      <div className="messages-list">
        {filteredMessages.length === 0 ? (
          <div className="message-item" style={{ justifyContent: 'center', color: 'var(--text-muted)' }}>
            {messages.length === 0 ? 'Click sync to validate' : 'No messages match filters'}
          </div>
        ) : (
          filteredMessages.map((msg) => (
            <div
              key={msg.id}
              className="message-item"
              onClick={() => handleMessageClick(msg.elementType, msg.elementId)}
            >
              <span className={`message-icon ${msg.severity}`}>
                {severityIcons[msg.severity]}
              </span>
              <span
                className="message-text"
                dangerouslySetInnerHTML={{
                  __html: msg.text.replace(
                    /'([^']+)'/g,
                    '<span class="highlight">$1</span>'
                  ),
                }}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
