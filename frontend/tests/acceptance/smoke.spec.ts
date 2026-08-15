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

test("should create a performance and upload audio file", async ({ page }) => {
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

  await page.route(
    /\/api\/v1\/performances\/\d+\/upload-audio\/?$/,
    async (route) => {
      performances[0] = {
        ...performances[0],
        audio_file_url: "https://example.com/uploaded.mp3",
      };

      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          performance_id: 101,
          s3_key: "performances/101/uploaded.mp3",
          file_url: "https://example.com/uploaded.mp3",
          file_size: 12345,
          message: "Audio file uploaded successfully",
        }),
      });
    },
  );

  await page.goto("/performances");

  await expect(
    page.getByRole("heading", { name: /^performances$/i }),
  ).toBeVisible();
  await page.getByRole("button", { name: /new performance/i }).click();
  await page.getByPlaceholder("Performance title").fill("Upload Flow Test");

  await page.locator('input[type="file"]').setInputFiles({
    name: "sample.mp3",
    mimeType: "audio/mpeg",
    buffer: Buffer.from("ID3-sample-audio-content"),
  });

  const uploadResponsePromise = page.waitForResponse(
    /\/api\/v1\/performances\/\d+\/upload-audio\/?$/,
  );

  await page.getByRole("button", { name: /create performance/i }).click();

  const uploadResponse = await uploadResponsePromise;
  expect(uploadResponse.ok()).toBeTruthy();
  await expect(page.getByText("Upload Flow Test")).toBeVisible();
  await expect(
    page.getByRole("link", { name: /view audio/i }).first(),
  ).toHaveAttribute("href", /uploaded\.mp3/);
});
