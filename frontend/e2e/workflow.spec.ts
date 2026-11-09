import { test, expect } from "@playwright/test";
const csv =
  "id,text\n" +
  [
    "katze hund tier futter",
    "fussball sport stadion tor",
    "computer software daten technik",
  ]
    .flatMap((text, group) =>
      Array.from({ length: 20 }, (_, i) => `${group * 20 + i},${text} ${i}`),
    )
    .join("\n");

test("clean desktop and mobile import, connection dialog", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByText("Lokal verbunden")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Gib deinen Texten einen Platz." }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "02 Modellierung" }),
  ).toBeDisabled();
  await page.screenshot({
    path: info.outputPath("import-desktop.png"),
    fullPage: true,
  });
  await page.getByText("Lokal verbunden").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "API-Zugriff prüfen" }),
  ).toBeDisabled();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: info.outputPath("import-mobile.png"),
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect(errors).toEqual([]);
});

test("real API: import, clean, train, all charts, search, download, restore", async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(page.getByText("Lokal verbunden")).toBeVisible();
  await page
    .getByLabel("CSV- oder Excel-Datei auswählen")
    .setInputFiles({
      name: "texte.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(csv),
    });
  await expect(page.getByText("60 Zeilen · 2 Spalten")).toBeVisible();
  await page
    .getByRole("button", { name: "Daten bereinigen", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Bereit für die Analyse" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Weiter zur Modellierung" }).click();
  await expect(
    page.getByRole("heading", { name: "Die richtigen Fragen an deine Texte." }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Hilfe zu Nachbarn", exact: true })
    .click();
  await expect(page.getByRole("note")).toContainText("lokale Gruppen");
  await page.getByRole("button", { name: "Hilfe schließen" }).click();
  await page.getByLabel("Sprache", { exact: true }).selectOption("Englisch");
  await expect(page.getByLabel("Embedding-Modell")).toHaveValue(
    "sentence-transformers/all-MiniLM-L6-v2",
  );
  await page.getByRole("button", { name: "KeyBERT", exact: true }).click();
  await page.getByRole("button", { name: "MMR", exact: true }).click();
  await expect(page.getByLabel("Themen mit OpenAI benennen")).toBeDisabled();
  await page.screenshot({
    path: info.outputPath("model-desktop.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: info.outputPath("model-mobile.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page
    .getByRole("button", { name: "Modell trainieren", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Deine Texte. Ihre Themen." }),
  ).toBeVisible({ timeout: 60000 });
  await expect(page.getByText("Identifizierte Themen")).toBeVisible();
  await page.screenshot({
    path: info.outputPath("results-desktop.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Visualisierungen", exact: true })
    .click();
  await expect(page.locator(".js-plotly-plot")).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "Top-Keywords", exact: true }).click();
  await expect(page.locator(".js-plotly-plot")).toBeVisible();
  await page
    .getByRole("button", { name: "Dokumentenkarte", exact: true })
    .click();
  await expect(page.locator(".js-plotly-plot")).toBeVisible();
  await page.screenshot({
    path: info.outputPath("chart-desktop.png"),
    fullPage: true,
  });
  await page.getByRole("button", { name: "Textbeiträge", exact: true }).click();
  await page.getByLabel("Textbeiträge durchsuchen").fill("computer");
  await expect(page.getByText(/20 Einträge/)).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Ergebnisse exportieren" }).click();
  expect((await downloadPromise).suggestedFilename()).toBe(
    "bertopic-results.zip",
  );
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Deine Texte. Ihre Themen." }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});
