---
name: playwright-automation
description: End-to-end browser automation and testing suite with Playwright. Covers Page Object Models (POM), visual regression, network mocking, and cross-browser CI verification.
---

# Playwright Browser Automation & E2E Testing

A production-grade web automation and end-to-end testing skill using Microsoft Playwright. Enables agents to author resilient test suites, inspect DOM elements, capture visual diffs, mock API endpoints, and verify full user journeys across Chromium, Firefox, and WebKit.

## Core Best Practices

1. **User-Facing Locators**: Always prefer resilient locators matching user perception over brittle CSS/XPath selectors:
   - `page.getByRole('button', { name: 'Submit' })`
   - `page.getByLabel('Email Address')`
   - `page.getByPlaceholder('Search documentation...')`
   - `page.getByTestId('checkout-card')`
2. **Page Object Model (POM)**: Structure tests cleanly into reusable page classes encapsulating element locators and user actions.
3. **Auto-Waiting & Web-First Assertions**: Use `await expect(locator).toBeVisible()` instead of hardcoded `sleep` timeouts.
4. **Network Mocking & Route Interception**: Mock third-party APIs (`page.route('**/api/v1/user', route => route.fulfill({...}))`) for deterministic tests.

## Test Suite Architecture

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';

test.describe('Authentication Flow', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('user@example.com', 'securePassword123');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });
});
```

## Commands & Workflows

- `/playwright test [filter]`: Run the test suite headlessly or with specified tags.
- `/playwright codegen <url>`: Launch interactive test recorder.
- `/playwright trace <trace-file>`: Inspect execution timeline, network waterfall, and action snapshots.
- `/playwright screenshot <url> <path>`: Capture full-page visual artifacts across mobile/desktop viewports.
