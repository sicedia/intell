import { test, expect } from "@playwright/test";

test("homepage loads and redirects to dashboard", async ({ page }) => {
  await page.goto("/");

  // Should redirect to dashboard
  await expect(page).toHaveURL(/.*\/dashboard/);
});

test("dashboard page is accessible", async ({ page }) => {
  await page.goto("/en/dashboard");

  // Check if dashboard content is visible
  await expect(page.getByText("Dashboard")).toBeVisible();
});
