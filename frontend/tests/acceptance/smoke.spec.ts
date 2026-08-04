import { test, expect } from "@playwright/test";

test("should render login and register pages", async ({ page }) => {
  await page.goto("/login");
  await expect(
    page.getByRole("heading", { name: /sign in to your account/i }),
  ).toBeVisible();
  await expect(page.getByPlaceholder("Username")).toBeVisible();
  await expect(page.getByPlaceholder("Password")).toBeVisible();

  await page.goto("/register");
  await expect(
    page.getByRole("heading", { name: /create your account/i }),
  ).toBeVisible();
  await expect(page.getByPlaceholder("Email")).toBeVisible();
  await expect(page.getByPlaceholder("First Name")).toBeVisible();
  await expect(page.getByPlaceholder("Last Name")).toBeVisible();
  await expect(
    page.getByRole("button", { name: /create account/i }),
  ).toBeVisible();
});
