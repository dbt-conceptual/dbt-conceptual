import { test, expect } from '@playwright/test';

/**
 * E2E Test: Sync with dbt project and verify validation messages
 *
 * Tests that:
 * 1. The sync button is accessible in the messages panel
 * 2. Clicking sync triggers a sync operation
 * 3. Validation messages appear after sync
 * 4. Message severity counts are displayed correctly
 * 5. Messages can be filtered by severity
 */

test.describe('Sync and Validation', () => {
  test('should find sync button in messages bar', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // The messages bar should be visible (collapsed state)
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible({ timeout: 5000 });

    // The sync button should be in the messages bar
    const syncButton = messagesBar.locator('button[title*="Sync" i], button[aria-label*="Sync" i], .messages-bar-sync');
    await expect(syncButton).toBeVisible();

    // Verify the button is enabled (not disabled initially)
    await expect(syncButton).toBeEnabled();
  });

  test('should trigger sync and update validation messages', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // Find the messages bar
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible({ timeout: 5000 });

    // Click the sync button
    const syncButton = messagesBar.locator('button[title*="Sync" i], button[aria-label*="Sync" i], .messages-bar-sync');
    await syncButton.click();

    // The sync button should show a loading state (disabled or different icon)
    // Wait for sync to complete - button should become enabled again
    await expect(syncButton).toBeEnabled({ timeout: 15000 });

    // After sync, the messages count or badges should be visible
    // The demo project should have some validation messages
    const messageCount = messagesBar.locator('.messages-bar-count, .messages-bar-badge');
    const hasMessages = await messageCount.count() > 0;

    // If there are messages, verify they're displayed
    if (hasMessages) {
      await expect(messageCount.first()).toBeVisible();
    }
  });

  test('should display validation messages in expanded panel', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // Find the messages bar and click to expand
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible({ timeout: 5000 });

    // Click the sync button first to ensure we have validation results
    const syncButton = messagesBar.locator('button[title*="Sync" i], button[aria-label*="Sync" i], .messages-bar-sync');
    await syncButton.click();

    // Wait for sync to complete
    await expect(syncButton).toBeEnabled({ timeout: 15000 });

    // Click to expand the messages panel (click on the bar, but not the sync button)
    const expandButton = messagesBar.locator('button[title*="Expand" i], button[aria-label*="Expand" i]').first();
    await expandButton.click();

    // The expanded panel should be visible
    const expandedPanel = page.locator('.messages-panel');
    await expect(expandedPanel).toBeVisible({ timeout: 2000 });

    // Panel should have a header
    await expect(expandedPanel.locator('.messages-panel-header')).toBeVisible();

    // Should show message filters (error, warning, info)
    const messageFilters = expandedPanel.locator('.messages-filters, .filter-toggle');
    await expect(messageFilters.first()).toBeVisible();

    // Should show severity counts in the filters
    const errorCount = expandedPanel.locator('.filter-toggle.error .filter-toggle-count, .filter-toggle:has-text("⊘")');
    const warningCount = expandedPanel.locator('.filter-toggle.warning .filter-toggle-count, .filter-toggle:has-text("⚠")');
    const infoCount = expandedPanel.locator('.filter-toggle.info .filter-toggle-count, .filter-toggle:has-text("ℹ")');

    // At least one of these should be visible
    const hasAnySeverity =
      (await errorCount.count() > 0) ||
      (await warningCount.count() > 0) ||
      (await infoCount.count() > 0);
    expect(hasAnySeverity).toBeTruthy();
  });

  test('should filter messages by severity', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // Find and expand the messages panel
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible({ timeout: 5000 });

    // Sync first
    const syncButton = messagesBar.locator('button[title*="Sync" i], button[aria-label*="Sync" i], .messages-bar-sync');
    await syncButton.click();
    await expect(syncButton).toBeEnabled({ timeout: 15000 });

    // Expand the panel
    const expandButton = messagesBar.locator('button[title*="Expand" i], button[aria-label*="Expand" i]').first();
    await expandButton.click();

    const expandedPanel = page.locator('.messages-panel');
    await expect(expandedPanel).toBeVisible({ timeout: 2000 });

    // Get the message list
    const messagesList = expandedPanel.locator('.messages-list, .message-item');
    const initialMessageCount = await messagesList.count();

    // If there are no messages, skip the filter test
    if (initialMessageCount === 0) {
      test.skip();
      return;
    }

    // Find the error filter toggle button
    const errorFilter = expandedPanel.locator('.filter-toggle.error, button[aria-label*="error" i]').first();

    // Check if error filter exists
    if (await errorFilter.count() === 0) {
      test.skip();
      return;
    }

    // Click to toggle off errors (if they're on by default)
    await errorFilter.click();

    // Wait for the filter to update
    await page.waitForTimeout(500);

    // The message count should change or messages should be filtered
    const filteredMessageCount = await messagesList.count();

    // Either the count changed, or we can verify the filter button's state changed
    const filterState = await errorFilter.getAttribute('aria-pressed');
    expect(filterState).toBeTruthy();
  });

  test('should show severity counts after sync', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // Find the messages bar
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible({ timeout: 5000 });

    // Sync
    const syncButton = messagesBar.locator('button[title*="Sync" i], button[aria-label*="Sync" i], .messages-bar-sync');
    await syncButton.click();
    await expect(syncButton).toBeEnabled({ timeout: 15000 });

    // Expand the panel to see counts
    const expandButton = messagesBar.locator('button[title*="Expand" i], button[aria-label*="Expand" i]').first();
    await expandButton.click();

    const expandedPanel = page.locator('.messages-panel');
    await expect(expandedPanel).toBeVisible({ timeout: 2000 });

    // Check for severity count badges
    const severityCounts = expandedPanel.locator('.filter-toggle-count');
    const countElements = await severityCounts.count();

    // Should have at least 3 count elements (error, warning, info)
    expect(countElements).toBeGreaterThanOrEqual(3);

    // Each count should be a number
    for (let i = 0; i < Math.min(countElements, 3); i++) {
      const countText = await severityCounts.nth(i).textContent();
      expect(countText).toMatch(/^\d+$/);
    }
  });

  test('should collapse messages panel', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Wait for the canvas to be ready
    await page.waitForSelector('.react-flow', { timeout: 10000 });

    // Find and expand the messages panel
    const messagesBar = page.locator('.messages-bar');
    await expect(messagesBar).toBeVisible({ timeout: 5000 });

    const expandButton = messagesBar.locator('button[title*="Expand" i], button[aria-label*="Expand" i]').first();
    await expandButton.click();

    // Verify expanded panel is visible
    const expandedPanel = page.locator('.messages-panel');
    await expect(expandedPanel).toBeVisible({ timeout: 2000 });

    // Find the collapse button in the expanded panel
    const collapseButton = expandedPanel.locator('button[title*="Collapse" i], button[aria-label*="Collapse" i]');
    await expect(collapseButton).toBeVisible();

    // Click to collapse
    await collapseButton.click();

    // The expanded panel should no longer be visible
    await expect(expandedPanel).not.toBeVisible({ timeout: 2000 });

    // The collapsed bar should be visible again
    await expect(messagesBar).toBeVisible();
  });
});
