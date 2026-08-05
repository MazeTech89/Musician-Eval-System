import { expect, test } from "@playwright/test";

// Basic smoke tests: verify key pages render their expected form fields/controls
test("renders the login page", async ({ page }) => {
  await page.goto("/login");

  await expect(
    page.getByRole("heading", { name: /sign in to your account/i }),
  ).toBeVisible();
  await expect(page.getByPlaceholder("Username")).toBeVisible();
  await expect(page.getByPlaceholder("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
});

test("renders the register page", async ({ page }) => {
  await page.goto("/register");

  await expect(
    page.getByRole("heading", { name: /create your account/i }),
  ).toBeVisible();
  await expect(page.getByPlaceholder("Username")).toBeVisible();
  await expect(page.getByPlaceholder("Email")).toBeVisible();
  await expect(page.getByPlaceholder("First Name")).toBeVisible();
  await expect(page.getByPlaceholder("Last Name")).toBeVisible();
  await expect(
    page.getByRole("button", { name: /create account/i }),
  ).toBeVisible();
});

test("renders the password reset request page", async ({ page }) => {
  await page.goto("/forgot-password");
  await page.waitForLoadState("networkidle");

  await expect(
    page.getByRole("heading", { name: /reset your password/i }),
  ).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByPlaceholder("you@example.com")).toBeVisible();
  await expect(
    page.getByRole("button", { name: /request password reset/i }),
  ).toBeVisible();
});

test("renders the password reset form", async ({ page }) => {
  await page.goto("/reset-password?token=test-token");
  await page.waitForLoadState("networkidle");

  await expect(
    page.getByRole("heading", { name: /create a new password/i }),
  ).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByPlaceholder("Paste your reset token")).toHaveValue(
    "test-token",
  );
  await expect(page.getByPlaceholder("At least 8 characters")).toBeVisible();
  await expect(page.getByPlaceholder("Re-enter your password")).toBeVisible();
  await expect(
    page.getByRole("button", { name: /set new password/i }),
  ).toBeVisible();
});

test("redirects unauthenticated users away from protected dashboard", async ({
  page,
}) => {
  // ProtectedRoute should bounce anonymous visitors to /login
  await page.goto("/");

  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: /sign in to your account/i }),
  ).toBeVisible();
});
