import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from '../components/Modal';

describe('Modal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    title: 'Settings',
    children: <p>Modal content here</p>,
  };

  it('renders title and children when open', () => {
    render(<Modal {...defaultProps} />);

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Modal content here')).toBeInTheDocument();
  });

  it('renders a close button', () => {
    render(<Modal {...defaultProps} />);

    expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<Modal {...defaultProps} onClose={onClose} />);

    await user.click(screen.getByRole('button', { name: /close/i }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('renders footer when provided', () => {
    render(
      <Modal {...defaultProps} footer={<button>Save</button>} />,
    );

    expect(screen.getByRole('button', { name: 'Save' })).toBeInTheDocument();
  });

  it('does not render footer when not provided', () => {
    render(<Modal {...defaultProps} />);

    const footer = document.querySelector('.modal-footer');
    expect(footer).toBeNull();
  });

  it('opens dialog element when isOpen is true', () => {
    render(<Modal {...defaultProps} isOpen={true} />);

    const dialog = document.querySelector('dialog');
    expect(dialog).not.toBeNull();
    expect(dialog?.hasAttribute('open')).toBe(true);
  });

  it('closes dialog element when isOpen is false', () => {
    const { rerender } = render(<Modal {...defaultProps} isOpen={true} />);

    const dialog = document.querySelector('dialog');
    expect(dialog?.hasAttribute('open')).toBe(true);

    rerender(<Modal {...defaultProps} isOpen={false} />);

    expect(dialog?.hasAttribute('open')).toBe(false);
  });

  it('renders the title as an h2', () => {
    render(<Modal {...defaultProps} />);

    const heading = screen.getByRole('heading', { level: 2 });
    expect(heading).toHaveTextContent('Settings');
  });
});
