# Handoff: DBC-43 -- fix(frontend): accessibility - keyboard nav and semantic HTML

## What was done
- `frontend/src/components/ConfirmDialog.tsx`: Refactored from `<div>` overlay to native `<dialog>` element. Uses `showModal()` for focus trapping, `aria-labelledby`/`aria-describedby` for screen readers, native `cancel` event for Escape key handling, backdrop click detection via `e.target === dialogRef.current`.
- `frontend/src/tokens.css`: Replaced `.confirm-dialog-overlay` styles with `.confirm-dialog-native` and `.confirm-dialog-native::backdrop` styles for the native dialog element.
- `frontend/src/components/MarkdownField.tsx`: Added `role="button"`, `tabIndex={0}`, `onKeyDown` (Enter/Space), and `aria-label` to the clickable preview div.
- `frontend/src/components/MessagesPanel/MessagesPanel.tsx`: Added `role="button"`, `tabIndex={0}`, `onKeyDown`, and `aria-label` to collapsed bar. Added conditional `role="button"`, `tabIndex={0}`, `onKeyDown`, and `aria-label` to clickable message items (only when navigable).
- `frontend/src/components/ConceptNode.tsx`: Added descriptive `aria-label` to root div with concept name, domain, model count, status, and validation info.
- `frontend/src/components/RelationshipEdge.tsx`: Added `aria-label` to SVG path, `<g>` group, and label div with verb, cardinality, status, and model count.

## What to verify (for Wardenstein)
- ConfirmDialog opens correctly via keyboard (Tab to trigger, then Tab between buttons)
- Pressing Escape in ConfirmDialog calls onStay (if available) or onCancel
- Clicking backdrop of ConfirmDialog dismisses correctly
- MarkdownField preview can be activated via Enter or Space key
- MessagesPanel collapsed bar can be expanded via Enter or Space key
- Message items with navigation targets can be activated via keyboard
- Screen reader announces ConceptNode and RelationshipEdge labels correctly
- Build passes: `cd frontend && npm run build`
- Lint passes: `cd frontend && npm run lint`

## Open questions for Architect
- None. All changes follow established patterns (Modal.tsx for dialog, standard ARIA attributes).
