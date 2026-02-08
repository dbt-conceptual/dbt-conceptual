import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfirmDialog } from '../components/ConfirmDialog';

describe('ConfirmDialog', () => {
  const defaultProps = {
    title: 'Discard changes?',
    message: 'You have unsaved changes that will be lost.',
    onConfirm: vi.fn(),
    onCancel: vi.fn(),
  };

  it('renders title and message', () => {
    render(<ConfirmDialog {...defaultProps} />);

    expect(screen.getByText('Discard changes?')).toBeInTheDocument();
    expect(screen.getByText('You have unsaved changes that will be lost.')).toBeInTheDocument();
  });

  it('renders default button labels', () => {
    render(<ConfirmDialog {...defaultProps} />);

    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('renders custom button labels', () => {
    render(
      <ConfirmDialog
        {...defaultProps}
        confirmLabel="Yes, discard"
        cancelLabel="Go back"
      />,
    );

    expect(screen.getByRole('button', { name: 'Yes, discard' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back' })).toBeInTheDocument();
  });

  it('calls onConfirm when confirm button is clicked', async () => {
    const onConfirm = vi.fn();
    const user = userEvent.setup();
    render(<ConfirmDialog {...defaultProps} onConfirm={onConfirm} />);

    await user.click(screen.getByRole('button', { name: 'Confirm' }));

    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when cancel button is clicked', async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    render(<ConfirmDialog {...defaultProps} onCancel={onCancel} />);

    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('renders three-button variant when onStay is provided', () => {
    const onStay = vi.fn();
    render(
      <ConfirmDialog
        {...defaultProps}
        stayLabel="Keep editing"
        onStay={onStay}
      />,
    );

    expect(screen.getByRole('button', { name: 'Keep editing' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument();
  });

  it('calls onStay when stay button is clicked', async () => {
    const onStay = vi.fn();
    const user = userEvent.setup();
    render(
      <ConfirmDialog
        {...defaultProps}
        stayLabel="Keep editing"
        onStay={onStay}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Keep editing' }));

    expect(onStay).toHaveBeenCalledTimes(1);
  });

  it('opens as a dialog element', () => {
    render(<ConfirmDialog {...defaultProps} />);

    const dialog = document.querySelector('dialog');
    expect(dialog).not.toBeNull();
    // showModal was called (our mock sets the "open" attribute)
    expect(dialog?.hasAttribute('open')).toBe(true);
  });

  it('applies danger variant styling to confirm button', () => {
    render(<ConfirmDialog {...defaultProps} variant="danger" />);

    const confirmBtn = screen.getByRole('button', { name: 'Confirm' });
    expect(confirmBtn.className).toContain('danger');
  });

  it('applies primary styling to confirm button by default', () => {
    render(<ConfirmDialog {...defaultProps} />);

    const confirmBtn = screen.getByRole('button', { name: 'Confirm' });
    expect(confirmBtn.className).toContain('primary');
  });
});
