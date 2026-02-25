// ============================================================================
// APEX Agent — Browser Automation Tool (Script-based, no Playwright dep)
// ============================================================================
// Uses Node.js fetch + script execution for browser tasks
// Playwright integration available when installed separately

import { exec } from 'child_process';
import { writeFile, unlink, mkdir } from 'fs/promises';
import { join } from 'path';
import { v4 as uuid } from 'uuid';

const WORKSPACE_DIR = join(process.cwd(), '.apex-workspace');

async function ensureWorkspaceDir() {
  await mkdir(WORKSPACE_DIR, { recursive: true });
}

export async function browserAction(params: {
  action: string;
  url?: string;
  selector?: string;
  text?: string;
  script?: string;
}): Promise<{ result: string; error?: string }> {
  const { action, url, selector, text, script } = params;

  switch (action) {
    case 'navigate':
    case 'extract_text':
      if (!url) return { result: '', error: 'URL is required for navigate/extract_text action' };
      return await fetchAndExtract(url);

    case 'screenshot':
      if (!url) return { result: '', error: 'URL is required for screenshot action' };
      return await takeScreenshot(url);

    case 'evaluate':
      if (!script) return { result: '', error: 'Script is required for evaluate action' };
      return await evaluateScript(script, url);

    case 'click':
    case 'type':
      return await automateWithScript(action, url, selector, text);

    default:
      return { result: '', error: `Unknown action: ${action}` };
  }
}

async function fetchAndExtract(url: string): Promise<{ result: string; error?: string }> {
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      },
      signal: AbortSignal.timeout(15000),
    });

    let content = await response.text();

    // Clean HTML to text
    content = content
      .replace(/<script[\s\S]*?<\/script>/gi, '')
      .replace(/<style[\s\S]*?<\/style>/gi, '')
      .replace(/<[^>]+>/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

    if (content.length > 8000) {
      content = content.slice(0, 8000) + '\n[... truncated]';
    }

    return { result: content };
  } catch (error) {
    return {
      result: '',
      error: `Failed to fetch: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

async function takeScreenshot(url: string): Promise<{ result: string; error?: string }> {
  await ensureWorkspaceDir();

  // Try using Playwright if available, otherwise fall back to a Python script
  const screenshotScript = `
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('${url.replace(/'/g, "\\'")}', { waitUntil: 'networkidle' });
  await page.screenshot({ path: '${join(WORKSPACE_DIR, 'screenshot.png')}', fullPage: false });
  await browser.close();
  console.log('Screenshot saved');
})().catch(e => {
  console.error('Playwright not available. Install with: npm install playwright');
  process.exit(1);
});
`;

  const scriptPath = join(WORKSPACE_DIR, `screenshot_${uuid().slice(0, 8)}.js`);
  await writeFile(scriptPath, screenshotScript);

  return new Promise((resolve) => {
    exec(`node "${scriptPath}"`, { timeout: 30000 }, async (error, stdout, stderr) => {
      try { await unlink(scriptPath); } catch { /* ignore */ }

      if (error) {
        resolve({
          result: '',
          error: `Screenshot failed: ${stderr || error.message}. Ensure Playwright is installed.`,
        });
      } else {
        resolve({ result: `Screenshot saved to .apex-workspace/screenshot.png` });
      }
    });
  });
}

async function evaluateScript(
  script: string,
  url?: string
): Promise<{ result: string; error?: string }> {
  await ensureWorkspaceDir();

  // Run JavaScript with Node.js  
  const nodeScript = url
    ? `
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('${url.replace(/'/g, "\\'")}');
  const result = await page.evaluate(() => { ${script} });
  console.log(JSON.stringify(result));
  await browser.close();
})().catch(e => console.error(e.message));
`
    : script;

  const scriptPath = join(WORKSPACE_DIR, `eval_${uuid().slice(0, 8)}.js`);
  await writeFile(scriptPath, nodeScript);

  return new Promise((resolve) => {
    exec(`node "${scriptPath}"`, { timeout: 15000 }, async (error, stdout, stderr) => {
      try { await unlink(scriptPath); } catch { /* ignore */ }

      resolve({
        result: stdout?.toString() || '',
        error: error ? (stderr?.toString() || error.message) : undefined,
      });
    });
  });
}

async function automateWithScript(
  action: string,
  url?: string,
  selector?: string,
  text?: string
): Promise<{ result: string; error?: string }> {
  if (!url || !selector) {
    return { result: '', error: 'URL and selector are required for click/type actions' };
  }

  await ensureWorkspaceDir();

  const actionCode =
    action === 'click'
      ? `await page.click('${selector.replace(/'/g, "\\'")}');`
      : `await page.fill('${selector.replace(/'/g, "\\'")}', '${(text || '').replace(/'/g, "\\'")}');`;

  const script = `
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('${url.replace(/'/g, "\\'")}', { waitUntil: 'networkidle' });
  ${actionCode}
  await page.waitForTimeout(1000);
  const content = await page.content();
  console.log('Action completed successfully');
  await browser.close();
})().catch(e => console.error(e.message));
`;

  const scriptPath = join(WORKSPACE_DIR, `auto_${uuid().slice(0, 8)}.js`);
  await writeFile(scriptPath, script);

  return new Promise((resolve) => {
    exec(`node "${scriptPath}"`, { timeout: 30000 }, async (error, stdout, stderr) => {
      try { await unlink(scriptPath); } catch { /* ignore */ }

      if (error) {
        resolve({
          result: '',
          error: `Browser automation failed: ${stderr || error.message}`,
        });
      } else {
        resolve({ result: stdout?.toString() || 'Action completed' });
      }
    });
  });
}
