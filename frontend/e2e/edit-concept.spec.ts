import { test, expect } from '@playwright/test';

/**
 * E2E Test: Edit concept properties
 *
 * Tests that:
 * 1. Concepts can be selected from the canvas
 * 2. The property panel opens with editable fields
 * 3. Changes can be made to concept properties
 * 4. Changes can be saved and persist
 */

test.describe('Edit Concept Properties', () => {
  test('should open property panel when concept is clicked', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for concepts to render
    const conceptNodes = page.locator('.concept-node');
    await expect(conceptNodes.first()).toBeVisible({ timeout: 10000 });

    // Get the name of the first concept before clicking
    const firstConceptName = await conceptNodes.first().locator('.concept-name').textContent();

    // Click on the first concept to select it
    await conceptNodes.first().click();

    // Property panel should become visible
    const propertyPanel = page.locator('.property-panel');
    await expect(propertyPanel).toBeVisible({ timeout: 2000 });

    // Panel should show the concept name
    await expect(propertyPanel).toContainText(firstConceptName || '');

    // Should have a properties tab (may be active by default)
    const propertiesTab = propertyPanel.locator('.properties-tab, [role="tabpanel"]');
    await expect(propertiesTab).toBeVisible();
  });

  test('should edit concept name and save', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for concepts to render
    const conceptNodes = page.locator('.concept-node');
    await expect(conceptNodes.first()).toBeVisible({ timeout: 10000 });

    // Click on a concept to select it
    await conceptNodes.first().click();

    // Wait for property panel to open
    const propertyPanel = page.locator('.property-panel');
    await expect(propertyPanel).toBeVisible({ timeout: 2000 });

    // Find the name input field
    const nameInput = propertyPanel.locator('input[type="text"]').first();
    await expect(nameInput).toBeVisible();

    // Get the original name
    const originalName = await nameInput.inputValue();

    // Edit the name by appending a suffix
    const newName = originalName + ' (Edited)';
    await nameInput.fill(newName);

    // Wait a moment for state to update
    await page.waitForTimeout(500);

    // Look for a save button and click it
    // The save button might be in the properties tab or panel header
    const saveButton = propertyPanel.locator('button:has-text("Save"), button[aria-label*="save" i]');
    await expect(saveButton).toBeVisible({ timeout: 2000 });
    await saveButton.click();

    // Wait for save to complete (button might be disabled during save)
    await page.waitForTimeout(1000);

    // Close the panel by clicking outside or pressing Escape
    await page.keyboard.press('Escape');

    // Verify the concept name updated on the canvas
    await expect(conceptNodes.first().locator('.concept-name')).toContainText('(Edited)');
  });

  test('should edit concept definition (markdown field)', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for concepts to render
    const conceptNodes = page.locator('.concept-node');
    await expect(conceptNodes.first()).toBeVisible({ timeout: 10000 });

    // Click on a concept to select it
    await conceptNodes.first().click();

    // Wait for property panel to open
    const propertyPanel = page.locator('.property-panel');
    await expect(propertyPanel).toBeVisible({ timeout: 2000 });

    // Find the definition/description field (likely a textarea or markdown field)
    // Look for textarea or a field labeled "Definition"
    const definitionField = propertyPanel.locator('textarea, .markdown-field textarea').first();

    // Check if definition field exists (some concepts may not have one initially)
    const hasDefinitionField = await definitionField.count() > 0;
    if (!hasDefinitionField) {
      // Skip if no definition field found
      test.skip();
      return;
    }

    await expect(definitionField).toBeVisible();

    // Get original definition
    const originalDefinition = await definitionField.inputValue();

    // Edit the definition
    const newDefinition = originalDefinition + '\n\nUpdated via E2E test.';
    await definitionField.fill(newDefinition);

    // Wait for state to update
    await page.waitForTimeout(500);

    // Save changes
    const saveButton = propertyPanel.locator('button:has-text("Save"), button[aria-label*="save" i]');
    await expect(saveButton).toBeVisible({ timeout: 2000 });
    await saveButton.click();

    // Wait for save to complete
    await page.waitForTimeout(1000);

    // Verify the save button is no longer highlighted or showing "unsaved changes"
    // After save, the button might be disabled or the panel state changes
    await expect(saveButton).toBeDisabled({ timeout: 2000 });
  });

  test('should close property panel with Escape key', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for concepts to render
    const conceptNodes = page.locator('.concept-node');
    await expect(conceptNodes.first()).toBeVisible({ timeout: 10000 });

    // Click on a concept to select it
    await conceptNodes.first().click();

    // Wait for property panel to open
    const propertyPanel = page.locator('.property-panel');
    await expect(propertyPanel).toBeVisible({ timeout: 2000 });

    // Press Escape to close the panel
    await page.keyboard.press('Escape');

    // Property panel should no longer be visible
    await expect(propertyPanel).not.toBeVisible({ timeout: 2000 });
  });

  test('should warn about unsaved changes when closing panel', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for concepts to render
    const conceptNodes = page.locator('.concept-node');
    await expect(conceptNodes.first()).toBeVisible({ timeout: 10000 });

    // Click on a concept to select it
    await conceptNodes.first().click();

    // Wait for property panel to open
    const propertyPanel = page.locator('.property-panel');
    await expect(propertyPanel).toBeVisible({ timeout: 2000 });

    // Make a change to the name without saving
    const nameInput = propertyPanel.locator('input[type="text"]').first();
    await expect(nameInput).toBeVisible();
    const originalName = await nameInput.inputValue();
    await nameInput.fill(originalName + ' (Modified)');

    // Wait for state to update
    await page.waitForTimeout(500);

    // Try to close the panel by pressing Escape or clicking close
    await page.keyboard.press('Escape');

    // Should show an unsaved changes dialog/warning
    const unsavedDialog = page.locator('dialog[open], .confirm-dialog, .modal:has-text("unsaved")');
    await expect(unsavedDialog).toBeVisible({ timeout: 2000 });

    // Dialog should have options to discard or cancel
    await expect(unsavedDialog).toContainText(/discard|cancel|unsaved/i);
  });
});
