import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MarkdownField } from '../components/MarkdownField';

describe('MarkdownField', () => {
  it('renders in view mode by default', () => {
    render(<MarkdownField value="Hello **world**" onChange={vi.fn()} label="Definition" />);

    // Should show the Edit button (the actual button element, not the preview clickable area)
    const editBtn = screen.getByRole('button', { name: 'Edit' });
    expect(editBtn).toBeInTheDocument();
    // Should render markdown content
    expect(screen.getByText('world')).toBeInTheDocument();
  });

  it('shows placeholder when value is empty', () => {
    render(<MarkdownField value="" onChange={vi.fn()} placeholder="Enter text..." label="Notes" />);

    expect(screen.getByText('Enter text...')).toBeInTheDocument();
  });

  it('switches to edit mode when Edit button is clicked', async () => {
    const user = userEvent.setup();
    render(<MarkdownField value="Some text" onChange={vi.fn()} label="Definition" />);

    // Click the explicit Edit button (not the preview area)
    await user.click(screen.getByRole('button', { name: 'Edit' }));

    // Should show textarea
    const textarea = screen.getByRole('textbox');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveValue('Some text');

    // Should show Done and Cancel buttons
    expect(screen.getByRole('button', { name: 'Done' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  it('switches to edit mode when preview area is clicked', async () => {
    const user = userEvent.setup();
    render(<MarkdownField value="Click me" onChange={vi.fn()} label="Def" />);

    // Click the preview area (has a specific aria-label with "activate to modify")
    const preview = screen.getByRole('button', { name: /activate to modify/i });
    await user.click(preview);

    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('calls onChange with updated value when Done is clicked', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MarkdownField value="original" onChange={onChange} label="Def" />);

    // Enter edit mode via preview click (only one "Edit" button issue avoided)
    await user.click(screen.getByRole('button', { name: 'Edit' }));

    // Clear and type new value
    const textarea = screen.getByRole('textbox');
    await user.clear(textarea);
    await user.type(textarea, 'updated value');

    // Click Done
    await user.click(screen.getByRole('button', { name: 'Done' }));

    expect(onChange).toHaveBeenCalledWith('updated value');
  });

  it('discards changes when Cancel is clicked', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MarkdownField value="original" onChange={onChange} label="Def" />);

    // Enter edit mode
    await user.click(screen.getByRole('button', { name: 'Edit' }));

    // Type something
    const textarea = screen.getByRole('textbox');
    await user.clear(textarea);
    await user.type(textarea, 'changed');

    // Click Cancel
    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    // onChange should NOT have been called
    expect(onChange).not.toHaveBeenCalled();
    // Should be back in view mode
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('saves on Cmd+Enter keyboard shortcut', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MarkdownField value="original" onChange={onChange} label="Def" />);

    // Enter edit mode
    await user.click(screen.getByRole('button', { name: 'Edit' }));

    const textarea = screen.getByRole('textbox');
    await user.clear(textarea);
    await user.type(textarea, 'shortcut save');

    // Cmd+Enter
    await user.keyboard('{Meta>}{Enter}{/Meta}');

    expect(onChange).toHaveBeenCalledWith('shortcut save');
    // Should exit edit mode
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('cancels on Escape keyboard shortcut', async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<MarkdownField value="original" onChange={onChange} label="Def" />);

    // Enter edit mode
    await user.click(screen.getByRole('button', { name: 'Edit' }));

    const textarea = screen.getByRole('textbox');
    await user.type(textarea, ' extra');

    // Escape
    await user.keyboard('{Escape}');

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('shows markdown hint in edit mode', async () => {
    const user = userEvent.setup();
    render(<MarkdownField value="text" onChange={vi.fn()} label="Def" />);

    // Enter edit mode via the preview area
    const preview = screen.getByRole('button', { name: /activate to modify/i });
    await user.click(preview);

    expect(screen.getByText(/markdown supported/i)).toBeInTheDocument();
  });

  it('renders empty preview as clickable with placeholder', () => {
    render(<MarkdownField value="" onChange={vi.fn()} placeholder="Write here..." label="Notes" />);

    const preview = screen.getByRole('button', { name: /edit notes/i });
    expect(preview).toBeInTheDocument();
  });
});
