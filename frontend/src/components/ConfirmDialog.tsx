interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  stayLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  onStay?: () => void;
  variant?: 'default' | 'danger';
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  stayLabel,
  onConfirm,
  onCancel,
  onStay,
  variant = 'default',
}: ConfirmDialogProps) {
  // Click on overlay dismisses (stay) if available, otherwise cancels
  const handleOverlayClick = onStay || onCancel;

  return (
    <div className="confirm-dialog-overlay" onClick={handleOverlayClick}>
      <div className="confirm-dialog" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-dialog-title">{title}</div>
        <div className="confirm-dialog-message">{message}</div>
        <div className="confirm-dialog-actions">
          {onStay && stayLabel && (
            <button
              className="confirm-dialog-btn tertiary"
              onClick={onStay}
            >
              {stayLabel}
            </button>
          )}
          <button
            className="confirm-dialog-btn secondary"
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button
            className={`confirm-dialog-btn ${variant === 'danger' ? 'danger' : 'primary'}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
