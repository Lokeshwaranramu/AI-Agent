// ============================================================================
// APEX Agent — Image Generation Tool (Pollinations.ai — free, no API key)
// ============================================================================

import { mkdir } from 'fs/promises';
import { join } from 'path';
import { v4 as uuid } from 'uuid';

const OUTPUT_DIR = join(process.cwd(), 'public', 'generated');

async function ensureOutputDir() {
  await mkdir(OUTPUT_DIR, { recursive: true });
}

export async function generateImage(
  prompt: string,
  width = 1024,
  height = 1024,
  seed?: number
): Promise<{ url: string; localPath: string; error?: string }> {
  try {
    await ensureOutputDir();

    // Pollinations.ai — completely free, no API key needed
    const encodedPrompt = encodeURIComponent(prompt);
    const seedParam = seed ? `&seed=${seed}` : '';
    const imageUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=${width}&height=${height}&nologo=true${seedParam}`;

    // Download the generated image
    const response = await fetch(imageUrl, {
      signal: AbortSignal.timeout(60000), // 60s timeout for generation
    });

    if (!response.ok) {
      throw new Error(`Image generation failed: HTTP ${response.status}`);
    }

    const buffer = Buffer.from(await response.arrayBuffer());
    const filename = `apex_${uuid().slice(0, 8)}.png`;
    const localPath = join(OUTPUT_DIR, filename);

    const { writeFile } = await import('fs/promises');
    await writeFile(localPath, buffer);

    return {
      url: `/generated/${filename}`,
      localPath,
    };
  } catch (error) {
    return {
      url: '',
      localPath: '',
      error: `Image generation failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
