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

test("should create and display a performance", async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem("access_token", "test-token");
  });

  const performances = [
    {
      id: 10,
      title: "Existing Performance",
      description: "Already uploaded",
      musician_id: 1,
      audio_file_url: "https://example.com/existing.mp3",
      submitted_at: "2026-01-01T00:00:00Z",
      status: "pending",
      analysis: null,
    },
  ];

  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "1",
        username: "musician",
        email: "musician@example.com",
        first_name: "Test",
        last_name: "Musician",
        role: "musician",
        is_active: true,
      }),
    });
  });

  await page.route(/\/api\/v1\/performances\/?$/, async (route) => {
    const request = route.request();

    if (request.method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(performances),
      });
      return;
    }

    if (request.method() === "POST") {
      const createdPerformance = {
        id: 101,
        title: "Upload Flow Test",
        description: "Created from Playwright",
        musician_id: 1,
        audio_file_url: null,
        submitted_at: "2026-07-15T12:00:00Z",
        status: "pending",
        analysis: null,
      };

      performances.unshift(createdPerformance);

      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(createdPerformance),
      });
      return;
    }

    await route.fallback();
  });

  await page.goto("/performances");

  await expect(
    page
      .getByRole("main")
      .getByRole("heading", { name: "Performances", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /new performance/i }).click();
  await page.getByPlaceholder("Performance title").fill("Upload Flow Test");
  await page
    .getByPlaceholder("Optional description")
    .fill("Created from Playwright");

  const createResponsePromise = page.waitForResponse(
    (response) =>
      /\/api\/v1\/performances\/?$/.test(response.url()) &&
      response.request().method() === "POST",
  );

  await page.getByRole("button", { name: /create performance/i }).click();

  const createResponse = await createResponsePromise;
  expect(createResponse.ok()).toBeTruthy();
  await expect(page.getByText("Upload Flow Test")).toBeVisible();
  await expect(page.getByText("Created from Playwright")).toBeVisible();
});
