// ============================================================================
// APEX Agent — Video Creation Tool (FFmpeg)
// ============================================================================

import { exec } from 'child_process';
import { mkdir } from 'fs/promises';
import { join } from 'path';

const OUTPUT_DIR = join(process.cwd(), 'public', 'generated');

async function ensureOutputDir() {
  await mkdir(OUTPUT_DIR, { recursive: true });
}

export async function createVideo(
  ffmpegCommand: string,
  description: string
): Promise<{ output: string; error?: string }> {
  try {
    await ensureOutputDir();

    // Security: validate command doesn't contain dangerous operations
    const blocked = ['rm ', 'del ', 'format ', 'mkfs', ' /dev/'];
    if (blocked.some((b) => ffmpegCommand.toLowerCase().includes(b))) {
      return { output: '', error: 'Command contains blocked operations.' };
    }

    // Ensure ffmpeg is available
    const ffmpegExists = await new Promise<boolean>((resolve) => {
      exec('which ffmpeg', (error) => resolve(!error));
    });

    if (!ffmpegExists) {
      return {
        output: '',
        error:
          'FFmpeg is not installed. Install it with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)',
      };
    }

    const fullCommand = `ffmpeg -y ${ffmpegCommand}`;

    return new Promise((resolve) => {
      exec(
        fullCommand,
        {
          timeout: 300000, // 5 min timeout for video ops
          maxBuffer: 10 * 1024 * 1024,
          cwd: OUTPUT_DIR,
        },
        (error, stdout, stderr) => {
          if (error && error.code !== 0) {
            resolve({
              output: stdout?.toString() || '',
              error: `FFmpeg error: ${stderr?.toString() || error.message}`,
            });
          } else {
            resolve({
              output: `✓ Video operation complete: ${description}\n${stdout?.toString() || ''}\n${stderr?.toString() || ''}`.trim(),
            });
          }
        }
      );
    });
  } catch (error) {
    return {
      output: '',
      error: `Video creation failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
