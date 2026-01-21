import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownFieldProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  minRows?: number;
}

/**
 * A reusable markdown field with view/edit modes.
 * - View mode: renders markdown
 * - Edit mode: shows raw textarea
 * - Toggle via Edit/Done button
 */
export function MarkdownField({
  value,
  onChange,
  placeholder = 'Enter text...',
  label,
  minRows = 4,
}: MarkdownFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [localValue, setLocalValue] = useState(value);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync local value when external value changes (e.g., switching concepts)
  useEffect(() => {
    if (!isEditing) {
      setLocalValue(value);
    }
  }, [value, isEditing]);

  // Focus textarea when entering edit mode
  useEffect(() => {
    if (isEditing && textareaRef.current) {
      textareaRef.current.focus();
      // Move cursor to end
      const len = textareaRef.current.value.length;
      textareaRef.current.setSelectionRange(len, len);
    }
  }, [isEditing]);

  const handleEdit = () => {
    setLocalValue(value);
    setIsEditing(true);
  };

  const handleDone = () => {
    onChange(localValue);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setLocalValue(value);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Escape to cancel
    if (e.key === 'Escape') {
      handleCancel();
    }
    // Cmd/Ctrl + Enter to save
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleDone();
    }
  };

  const isEmpty = !value || value.trim() === '';

  return (
    <div className="markdown-field">
      {/* Header with label and action button */}
      <div className="markdown-field-header">
        {label && <label className="property-label">{label}</label>}
        <div className="markdown-field-actions">
          {isEditing ? (
            <>
              <button
                className="markdown-field-action secondary"
                onClick={handleCancel}
                type="button"
              >
                Cancel
              </button>
              <button
                className="markdown-field-action primary"
                onClick={handleDone}
                type="button"
              >
                Done
              </button>
            </>
          ) : (
            <button
              className="markdown-field-action"
              onClick={handleEdit}
              type="button"
            >
              Edit
            </button>
          )}
        </div>
      </div>

      {/* Content area */}
      <div className="markdown-field-content">
        {isEditing ? (
          <textarea
            ref={textareaRef}
            className="markdown-field-textarea"
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            rows={minRows}
          />
        ) : (
          <div
            className={`markdown-field-preview ${isEmpty ? 'empty' : ''}`}
            onClick={handleEdit}
          >
            {isEmpty ? (
              <span className="markdown-field-placeholder">{placeholder}</span>
            ) : (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{value}</ReactMarkdown>
            )}
          </div>
        )}
      </div>

      {/* Hint for edit mode */}
      {isEditing && (
        <div className="markdown-field-hint">
          Markdown supported. Press <kbd>Esc</kbd> to cancel, <kbd>Cmd+Enter</kbd> to save.
        </div>
      )}
    </div>
  );
}
