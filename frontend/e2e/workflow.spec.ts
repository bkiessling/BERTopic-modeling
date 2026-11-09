import { test, expect } from "@playwright/test";
const csv =
  "id,text,notes\n" +
  [
    "katze hund tier futter",
    "fussball sport stadion tor",
    "computer software daten technik",
  ]
    .flatMap((text, group) =>
      Array.from(
        { length: 20 },
        (_, i) => `${group * 20 + i},${text} ${i},notiz`,
      ),
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
    page.getByRole("heading", { name: "Daten importieren" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "02 Modellierung" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("heading", {
      name: "#NDRfragt Topic Modeling",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText("BERTopic workspace", { exact: true }),
  ).toHaveCount(0);
  const upload = await page.locator(".upload-card").boundingBox();
  const selection = await page.locator(".selection-card").boundingBox();
  expect(Math.abs(upload!.width - selection!.width)).toBeLessThan(1);
  expect(selection!.y).toBeGreaterThan(upload!.y + upload!.height);
  await expect(
    page.getByRole("link", { name: "BERTopic", exact: true }),
  ).toBeVisible();
  await expect(page.locator("footer")).toHaveCount(0);
  const nav = await page
    .getByRole("navigation", { name: "Analyseschritte" })
    .boundingBox();
  const first = await page
    .getByRole("button", { name: "01 Import" })
    .boundingBox();
  const last = await page
    .getByRole("button", { name: "03 Ergebnisse" })
    .boundingBox();
  expect(
    Math.abs(
      (first!.x + last!.x + last!.width) / 2 - (nav!.x + nav!.width / 2),
    ),
  ).toBeLessThan(1);
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
  await page.getByLabel("CSV- oder Excel-Datei auswählen").setInputFiles({
    name: "texte.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(csv),
  });
  await expect(page.getByText("60 Zeilen · 3 Spalten")).toBeVisible();
  const initialPreview = page.locator(".preview-card");
  await expect(initialPreview.locator("th")).toHaveText(["ID"]);
  await expect(
    page.getByRole("button", { name: "Daten bereinigen", exact: true }),
  ).toBeDisabled();
  const idField = await page
    .getByLabel("ID-Spalte", { exact: true })
    .boundingBox();
  const textField = await page
    .getByRole("button", { name: "Textspalte(n)", exact: true })
    .boundingBox();
  expect(Math.abs(idField!.y - textField!.y)).toBeLessThan(1);
  const sampleField = await page.getByLabel("Stichprobe (%)").boundingBox();
  const stopwordField = await page
    .getByLabel("Zusätzliche Stopwörter", { exact: true })
    .boundingBox();
  expect(Math.abs(sampleField!.y - stopwordField!.y)).toBeLessThan(1);
  await page
    .getByRole("button", { name: "Textspalte(n)", exact: true })
    .click();
  await expect(
    page.getByRole("group", { name: "Textspalten auswählen" }),
  ).toBeVisible();
  await expect(
    page.getByLabel("Textspalte text", { exact: true }),
  ).not.toBeChecked();
  await page.getByLabel("Textspalten suchen").fill("tex");
  await expect(
    page.getByLabel("Textspalte notes", { exact: true }),
  ).toHaveCount(0);
  await page.getByLabel("Textspalten suchen").press("Enter");
  await page.getByLabel("Textspalten suchen").fill("");
  await expect(
    page.getByLabel("Textspalte text", { exact: true }),
  ).toBeChecked();
  const preview = page.locator(".preview-card");
  await expect(preview.locator("th")).toHaveText(["ID", "text"]);
  await expect(
    preview.locator("tbody tr").first().locator("td").first(),
  ).toHaveText("");
  await page.getByLabel("Textspalte notes", { exact: true }).check();
  await expect(
    page.getByRole("button", { name: "Textspalte(n)", exact: true }),
  ).toContainText("text, notes");
  await expect(preview.locator("th")).toHaveText(["ID", "text", "notes"]);
  await page.keyboard.press("Escape");
  await page.getByLabel("ID-Spalte", { exact: true }).selectOption("id");
  await expect(preview.locator("th")).toHaveText(["id", "text", "notes"]);
  await expect(
    preview.locator("tbody tr").first().locator("td").first(),
  ).toHaveText("0");
  await page
    .getByLabel("ID-Spalte", { exact: true })
    .selectOption("ID generieren");
  await page
    .getByRole("button", { name: "Textspalte(n)", exact: true })
    .click();
  await page.getByLabel("Textspalte notes", { exact: true }).uncheck();
  await expect(preview.locator("th")).toHaveText(["ID", "text"]);
  await page.getByLabel("Textspalte text", { exact: true }).uncheck();
  await expect(
    page.getByRole("button", { name: "Daten bereinigen", exact: true }),
  ).toBeDisabled();
  await page.getByLabel("Textspalte text", { exact: true }).check();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("group", { name: "Textspalten auswählen" }),
  ).toHaveCount(0);
  await page.screenshot({
    path: info.outputPath("import-selected.png"),
    fullPage: true,
  });
  const cleanButton = page.getByRole("button", {
    name: "Daten bereinigen",
    exact: true,
  });
  await expect(cleanButton.locator("svg")).toHaveCount(0);
  await cleanButton.hover();
  await expect(cleanButton).toHaveCSS("background-color", "rgb(38, 113, 198)");
  await page
    .getByRole("button", { name: "Daten bereinigen", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Bereit für die Analyse" }),
  ).toBeVisible();
  await expect(preview.locator("th")).toHaveText(["ID", "text"]);
  await expect(
    preview.locator("tbody tr").first().locator("td").first(),
  ).toHaveText("1");
  await expect(
    preview.locator("tbody tr").first().locator("td").nth(1),
  ).toHaveText("katze hund tier futter");
  await expect(
    page.getByText("Bereinigte Texte anzeigen", { exact: true }),
  ).toHaveCount(0);
  await page.screenshot({
    path: info.outputPath("import-cleaned.png"),
    fullPage: true,
  });
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
  const tiles = page.locator(".model-top-grid > .card");
  await expect(tiles).toHaveCount(3);
  const left = await tiles.nth(0).boundingBox(),
    middle = await tiles.nth(1).boundingBox(),
    right = await tiles.nth(2).boundingBox();
  expect(middle!.width).toBeGreaterThan(left!.width);
  expect(middle!.width).toBeGreaterThan(right!.width);
  expect(Math.abs(left!.y - middle!.y)).toBeLessThan(1);
  await expect(page.locator(".button svg")).toHaveCount(0);
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
