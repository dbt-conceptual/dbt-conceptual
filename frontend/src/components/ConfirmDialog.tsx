import { useEffect, useRef, useCallback } from 'react';

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
  const dialogRef = useRef<HTMLDialogElement>(null);
  const confirmBtnRef = useRef<HTMLButtonElement>(null);

  // Open dialog as modal on mount
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    dialog.showModal();

    // Focus the confirm button initially for quick keyboard action
    confirmBtnRef.current?.focus();

    return () => {
      if (dialog.open) {
        dialog.close();
      }
    };
  }, []);

  // Handle backdrop click (click on <dialog> itself, not its children)
  const handleDialogClick = useCallback(
    (e: React.MouseEvent<HTMLDialogElement>) => {
      // Only handle clicks directly on the <dialog> element (the backdrop area)
      if (e.target === dialogRef.current) {
        if (onStay) {
          onStay();
        } else {
          onCancel();
        }
      }
    },
    [onStay, onCancel],
  );

  // Handle Escape key via the native dialog cancel event
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    const handleCancel = (e: Event) => {
      e.preventDefault(); // Prevent default close so we control the flow
      if (onStay) {
        onStay();
      } else {
        onCancel();
      }
    };

    dialog.addEventListener('cancel', handleCancel);
    return () => {
      dialog.removeEventListener('cancel', handleCancel);
    };
  }, [onStay, onCancel]);

  return (
    <dialog
      ref={dialogRef}
      className="confirm-dialog-native"
      onClick={handleDialogClick}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
    >
      <div className="confirm-dialog">
        <div className="confirm-dialog-title" id="confirm-dialog-title">
          {title}
        </div>
        <div className="confirm-dialog-message" id="confirm-dialog-message">
          {message}
        </div>
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
            ref={confirmBtnRef}
            className={`confirm-dialog-btn ${variant === 'danger' ? 'danger' : 'primary'}`}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </dialog>
  );
}
