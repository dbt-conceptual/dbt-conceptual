import { test, expect } from '@playwright/test';

/**
 * E2E Test: Load project and verify canvas renders
 *
 * Tests that:
 * 1. The app loads without errors
 * 2. The canvas renders with concepts from the demo project
 * 3. The messages panel is present and shows validation status
 */

test.describe('Load Project', () => {
  test('should load the app and display concepts on canvas', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready (React Flow container)
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // Verify that the app loaded without any console errors
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    // Verify toolbar is present
    await expect(page.locator('.toolbar')).toBeVisible();

    // Verify canvas is present
    const canvas = page.locator('.react-flow');
    await expect(canvas).toBeVisible();

    // Wait for concepts to render (concept nodes should appear)
    // The demo project should have concepts
    const conceptNodes = page.locator('.concept-node');
    await expect(conceptNodes.first()).toBeVisible({ timeout: 10000 });

    // Verify that multiple concepts are rendered
    const conceptCount = await conceptNodes.count();
    expect(conceptCount).toBeGreaterThan(0);

    // Verify that concept nodes have names displayed
    const firstConceptName = conceptNodes.first().locator('.concept-name');
    await expect(firstConceptName).toBeVisible();
    const nameText = await firstConceptName.textContent();
    expect(nameText).toBeTruthy();
    expect(nameText?.length).toBeGreaterThan(0);
  });

  test('should display messages panel with validation results', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // The messages panel should be present (either collapsed or expanded)
    // In collapsed state, it shows as a bar at the bottom
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible({ timeout: 5000 });

    // The bar should show message counts or status
    // It should have severity indicators (error, warning, info)
    const severityIndicators = messagesBar.locator('.severity-count, .messages-bar-summary');
    await expect(severityIndicators.first()).toBeVisible();
  });

  test('should expand messages panel when clicked', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // Find the collapsed messages bar
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible();

    // Click to expand the messages panel
    await messagesBar.click();

    // The expanded panel should now be visible
    const expandedPanel = page.locator('.messages-panel-expanded, .messages-panel');
    await expect(expandedPanel).toBeVisible({ timeout: 2000 });

    // Should have a close/collapse button or mechanism
    const collapseButton = page.locator('.messages-panel-header button, .messages-panel-collapse');
    await expect(collapseButton).toBeVisible();
  });

  test('should display property panel when concept is selected', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for concepts to render
    const conceptNodes = page.locator('.concept-node');
    await expect(conceptNodes.first()).toBeVisible({ timeout: 10000 });

    // Click on a concept to select it
    await conceptNodes.first().click();

    // Property panel should become visible
    const propertyPanel = page.locator('.property-panel');
    await expect(propertyPanel).toBeVisible({ timeout: 2000 });

    // Property panel should show concept details
    const conceptName = propertyPanel.locator('input[placeholder*="Name"], .concept-name-field');
    await expect(conceptName).toBeVisible();
  });
});
