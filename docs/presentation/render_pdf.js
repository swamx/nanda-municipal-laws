// Renders docs/presentation/deck.html to docs/presentation/Municipal-Law-Skill.pdf
// via headless Chrome (puppeteer-core). One slide (1280x720, 16:9) per PDF page.
//
// Requires puppeteer-core (`npm install puppeteer-core`, or reuse an existing
// install - e.g. one already pulled in by @mermaid-js/mermaid-cli) and a real
// Chrome/Chromium binary on disk.
//
// Run: node docs/presentation/render_pdf.js <path-to-chrome-executable>

const path = require("path");

function loadPuppeteer() {
  try {
    return require("puppeteer-core");
  } catch (err) {
    // Fall back to an existing global install (e.g. mermaid-cli's own
    // bundled copy) rather than forcing a fresh local install just for this.
    const globalCandidate = path.join(
      process.env.APPDATA || "",
      "npm/node_modules/@mermaid-js/mermaid-cli/node_modules/puppeteer-core"
    );
    return require(globalCandidate);
  }
}

const puppeteer = loadPuppeteer();

async function main() {
  const chromePath = process.argv[2];
  if (!chromePath) {
    console.error("Usage: node render_pdf.js <path-to-chrome-executable>");
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ["--no-sandbox"],
  });
  const page = await browser.newPage();
  const deckPath = "file:///" + path.resolve(__dirname, "deck.html").split(path.sep).join("/");
  await page.goto(deckPath, { waitUntil: "load" });

  await page.pdf({
    path: path.resolve(__dirname, "Municipal-Law-Skill.pdf"),
    width: "1280px",
    height: "720px",
    printBackground: true,
    margin: { top: 0, bottom: 0, left: 0, right: 0 },
  });

  await browser.close();
  console.log("wrote Municipal-Law-Skill.pdf");
}

main().catch((err) => {
  console.error("FAILED:", err);
  process.exit(1);
});
