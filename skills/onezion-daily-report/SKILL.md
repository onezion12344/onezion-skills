---
name: onezion-daily-report
description: Generate beautiful infographic posters (daily reports, data summaries, social media content) as HTML, then convert to high-res PNG via Puppeteer screenshot. Use when user wants a visual report, poster, or infographic to share on WeChat Moments, LinkedIn, or other social platforms. Trigger on: "daily report", "日报", "信息图", "infographic", "poster", "海报", "发圈", "social media graphic".
allowed-tools: Bash, Read, Write, Edit, OpenResultView, PreviewUrl
agent_created: true
---

# Daily Report / Infographic Poster Skill

Generate beautiful HTML-based infographics and convert them to high-res PNG images for social media sharing.

## Workflow

1. **Generate HTML** — Write a self-contained HTML file with inline styles, no external dependencies except Google Fonts
2. **Preview** — Use `preview_url` to show the user the HTML preview
3. **Screenshot** — Use Puppeteer to capture a 2x retina PNG
4. **Deliver** — Use `open_result_view` to present the final image

## Step 1: Create HTML poster

Design principles:
- Use a single self-contained HTML file
- Inline all CSS (no external stylesheets except Google Fonts)
- Use Google Fonts CDN for typography (Noto Sans SC for Chinese, Inter for English)
- Dark gradient background (navy → deep purple) works well for social media
- Use CSS gradient text for titles
- Color-coded sections with distinct icons/labels
- Stats row at the top with big numbers
- Keep width at 720px (standard for mobile-friendly sharing)
- Use `deviceScaleFactor: 2` for retina quality

Color palette:
- Background: `linear-gradient(175deg, #0d1b3e, #15103a, #1a0e35, #0d0a2a)`
- Purple accents: `#a78bfa`, `#c7d2fe`
- Green (success): `#34d399`
- Amber (pending): `#fbbf24`
- Pink (highlight): `#f472b6`
- Blue (info): `#60a5fa`
- Cyan (secondary): `#22d3ee`

## Step 2: Take screenshot with Puppeteer

Prerequisites: `puppeteer-core` must be installed in the workspace.
```bash
npm install puppeteer-core
```

Screenshot script template (`screenshot.js`):
```javascript
const puppeteer = require('puppeteer-core');
(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 720, height: 2000, deviceScaleFactor: 2 });
  await page.goto('file:///ABSOLUTE_PATH_TO_HTML', { waitUntil: 'networkidle0', timeout: 30000 });
  await page.evaluate(() => document.fonts.ready);
  const poster = await page.$('.poster');
  await poster.screenshot({ path: '/ABSOLUTE_PATH_TO_OUTPUT.png', type: 'png' });
  console.log('Screenshot saved!');
  await browser.close();
})();
```

Run: `node screenshot.js`

## Step 3: Deliver

Use `open_result_view` on the PNG file, then use `deliver_attachments` to send to user.

## Key rules

1. **Width always 720px** — optimal for WeChat Moments and most social platforms
2. **Always use `.poster` class** on the main container so the screenshot script can target it
3. **Always wait for fonts** — `document.fonts.ready` ensures Google Fonts are loaded before capture
4. **deviceScaleFactor: 2** — produces 1440px wide retina images
5. **Inline everything** — no external CSS/JS except Google Fonts CDN
6. **Test with preview_url first** before screenshotting

## Platform-specific notes

- **macOS**: Chrome path is `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Windows**: Chrome path varies, check `where chrome` or common paths
- **WeChat Moments**: 720px width is ideal, vertical format preferred
- **LinkedIn**: Both 720px and 1080px work
- **Twitter/X**: 1200×675 or 1080×1080 for square
