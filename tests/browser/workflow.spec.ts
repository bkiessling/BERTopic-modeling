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
      name: "#NDRfragt Themenfinder",
      exact: true,
    }),
  ).toBeVisible();
  await expect(page).toHaveTitle("#NDRfragt Themenfinder");
  await expect(page.locator("h1 img")).toHaveAttribute("src", "/schwalbe.svg");
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute(
    "href",
    "/schwalbe-weiss.svg",
  );
  await expect(
    page.getByText("BERTopic workspace", { exact: true }),
  ).toHaveCount(0);
  const upload = await page.locator(".upload-card").boundingBox();
  const selection = await page.locator(".selection-card").boundingBox();
  expect(Math.abs(upload!.width - selection!.width)).toBeLessThan(1);
  expect(selection!.y).toBeGreaterThan(upload!.y + upload!.height);
  await expect(
    page.getByRole("link", { name: "Topic Modeling", exact: true }),
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
  const title = page.locator("h1 span");
  const icon = page.locator("h1 img");
  const titleBox = await title.boundingBox();
  const iconBox = await icon.boundingBox();
  expect(iconBox!.height).toBeLessThanOrEqual(titleBox!.height);
  expect(iconBox!.x + iconBox!.width).toBeLessThan(titleBox!.x);
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
  await expect(page.locator(".raw-preview tbody tr")).toHaveCount(3);
  await expect(page.locator(".raw-preview th")).toHaveText([
    "id",
    "text",
    "notes",
  ]);
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
    page.getByRole("heading", { name: "Daten für die Modellierung" }),
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
    page.getByRole("heading", { name: "Modellierung" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Hilfe zu Voreinstellungen", exact: true })
    .click();
  await expect(page.getByRole("note")).toContainText("Heuristiken");
  await page.getByRole("button", { name: "Hilfe schließen" }).click();
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
  await page.getByLabel("Themen mit OpenAI benennen").click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page
    .getByLabel("OpenAI-API-Key", { exact: true })
    .fill("test-only-workspace-key");
  await page
    .getByRole("button", { name: "Key übernehmen", exact: true })
    .click();
  await expect(
    page.getByText("API-Key erkannt · Aktueller Arbeitsbereich"),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByLabel("Themen mit OpenAI benennen")).toBeChecked();
  await page.getByLabel("Themen mit OpenAI benennen").uncheck();
  const tiles = page.locator(".model-top-grid > .card");
  await expect(tiles).toHaveCount(3);
  const left = await tiles.nth(0).boundingBox(),
    middle = await tiles.nth(1).boundingBox(),
    right = await tiles.nth(2).boundingBox();
  expect(middle!.width).toBeGreaterThan(left!.width);
  expect(middle!.width).toBeGreaterThan(right!.width);
  expect(Math.abs(left!.y - middle!.y)).toBeLessThan(1);
  await expect(
    tiles
      .nth(0)
      .getByRole("button", { name: "Modell trainieren", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Parameter zurücksetzen" }),
  ).toBeVisible();
  const actionButtons = [
    page.getByRole("button", { name: "Parameter zurücksetzen", exact: true }),
    page.getByRole("button", { name: "Modell trainieren", exact: true }),
    page.getByRole("button", { name: "OpenAI-Modell", exact: true }),
  ];
  const sizes = await Promise.all(
    actionButtons.map((button) => button.boundingBox()),
  );
  expect(sizes.map((box) => box!.width)).toEqual([200, 200, 200]);
  expect(sizes.map((box) => box!.height)).toEqual([48, 48, 48]);
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
  await page.route("**/api/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page
    .getByRole("button", { name: "Modell trainieren", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("Backend ist veraltet");
  await page.unroute("**/api/health");
  await page
    .getByRole("button", { name: "Modell trainieren", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: "Ergebnisse" })).toBeVisible({
    timeout: 60000,
  });
  await expect(page.getByText("Identifizierte Themen")).toBeVisible();
  await page.screenshot({
    path: info.outputPath("results-desktop.png"),
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Visualisierungen", exact: true })
    .click();
  await expect(page.locator(".js-plotly-plot")).toBeVisible({ timeout: 30000 });
  await expect(
    page.getByRole("button", { name: "Netzwerk", exact: true }),
  ).toHaveClass("selected");
  await expect(page.locator(".documents-card")).toBeVisible();
  await page.getByRole("button", { name: "Top-Keywords", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Themen für Top-Keywords", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Anzahl Keywords", { exact: true }).fill("3");
  await expect(page.locator(".js-plotly-plot")).toBeVisible();
  await page.getByRole("button", { name: "Netzwerk", exact: true }).click();
  await expect(page.locator(".js-plotly-plot")).toBeVisible();
  await page.screenshot({
    path: info.outputPath("chart-desktop.png"),
    fullPage: true,
  });
  await expect(
    page.getByRole("heading", { name: "Textbeiträge", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Modellparameter anzeigen", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Verwendete Modellparameter" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Modellparameter anzeigen", exact: true })
    .click();
  const filter = page.getByLabel("Nach Thema filtern", { exact: true });
  await filter.selectOption({ index: 1 });
  await expect(page.locator(".documents-card tbody tr")).toHaveCount(20);
  await page
    .locator(".documents-card")
    .getByRole("button", { name: "Textbeitrag", exact: false })
    .click();
  await expect(
    page.locator('.documents-card th[aria-sort="ascending"]'),
  ).toContainText("Textbeitrag");
  await filter.selectOption("");
  await expect(
    page.getByLabel("Nur repräsentative Beiträge", { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByLabel("Nach ID gruppieren", { exact: true }),
  ).toHaveCount(0);
  await expect(page.locator(".documents-card th").first()).toContainText(
    "Themenname",
  );
  await page.getByLabel("Textbeiträge durchsuchen").fill("computer");
  await expect(page.getByText(/20 Einträge/)).toBeVisible();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Ergebnisse exportieren" }).click();
  expect((await downloadPromise).suggestedFilename()).toBe(
    "topic-modeling-results.zip",
  );
  await page.reload();
  await expect(page.getByRole("heading", { name: "Ergebnisse" })).toBeVisible();
  await page.getByText("Ergebnisse verbessern", { exact: true }).click();
  const subnav = page.getByRole("navigation", {
    name: "Ergebnisansichten",
    exact: true,
  });
  const mainnav = await page
    .getByRole("navigation", { name: "Analyseschritte", exact: true })
    .boundingBox();
  const subBox = await subnav.boundingBox();
  const resultsHeading = await page
    .getByRole("heading", { name: "Ergebnisse", exact: true })
    .boundingBox();
  expect(subBox!.y).toBeGreaterThan(mainnav!.y + mainnav!.height);
  expect(subBox!.y + subBox!.height).toBeLessThan(resultsHeading!.y);
  const firstTab = await subnav
    .getByRole("button", { name: "Themenübersicht", exact: true })
    .boundingBox();
  const lastTab = await subnav
    .getByRole("button", { name: "Visualisierungen", exact: true })
    .boundingBox();
  expect(
    Math.abs(
      (firstTab!.x + lastTab!.x + lastTab!.width) / 2 -
        (subBox!.x + subBox!.width / 2),
    ),
  ).toBeLessThan(1);
  await expect(subnav.locator("button svg")).toHaveCount(2);
  await page
    .getByRole("button", { name: "Hilfe zu Outlier", exact: true })
    .click();
  await expect(page.getByRole("note")).toContainText("keinem stabilen Thema");
  await page
    .getByRole("button", { name: "Hilfe schließen", exact: true })
    .click();
  const merge = page.getByRole("button", {
    name: "Themen zum Zusammenführen",
    exact: true,
  });
  await merge.click();
  const menu = page.getByRole("group", {
    name: "Themen auswählen",
    exact: true,
  });
  await menu.locator('input[type="checkbox"]').nth(0).check();
  await menu.locator('input[type="checkbox"]').nth(1).check();
  await page.keyboard.press("Escape");
  const beforeCount = Number(
    await page.locator(".stat-card").first().locator("strong").innerText(),
  );
  await page
    .getByRole("button", {
      name: "Ausgewählte Themen zusammenführen",
      exact: true,
    })
    .click();
  await expect(page.locator(".stat-card").first().locator("strong")).toHaveText(
    String(beforeCount - 1),
    { timeout: 30000 },
  );
  await page
    .getByLabel("Thema umbenennen", { exact: true })
    .selectOption({ index: 1 });
  await page
    .getByLabel("Neuer Themenname", { exact: true })
    .fill("Mein manuell bearbeitetes Thema");
  await page
    .getByRole("button", { name: "Themenname speichern", exact: true })
    .click();
  await expect(
    page.getByLabel("Nach Thema filtern", { exact: true }),
  ).toContainText("Mein manuell bearbeitetes Thema");
  await page.reload();
  await expect(
    page.getByLabel("Nach Thema filtern", { exact: true }),
  ).toContainText("Mein manuell bearbeitetes Thema");
  await page.getByText("Ergebnisse verbessern", { exact: true }).click();

  await page.getByLabel("Zielanzahl Themen", { exact: true }).fill("1");
  await page
    .getByRole("button", { name: "Themen zusammenfassen", exact: true })
    .click();
  await expect(page.locator(".stat-card").first().locator("strong")).toHaveText(
    "1",
    { timeout: 30000 },
  );
  await page
    .getByRole("button", { name: "Themen neu benennen", exact: true })
    .click();
  await expect(
    page.getByText("Themennamen von OpenAI · gpt-4.1-mini"),
  ).toBeVisible({ timeout: 30000 });
  await expect(
    page.locator(".documents-card tbody tr").first().locator("td").first(),
  ).toContainText("Test-Themenname");
  expect(errors).toEqual([]);
});
