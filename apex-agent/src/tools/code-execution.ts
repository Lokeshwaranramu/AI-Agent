// ============================================================================
// APEX Agent — Code Execution Tool
// ============================================================================

import { exec } from 'child_process';
import { writeFile, unlink, mkdir } from 'fs/promises';
import { join } from 'path';
import { v4 as uuid } from 'uuid';

const WORKSPACE_DIR = join(process.cwd(), '.apex-workspace');

async function ensureWorkspaceDir() {
  await mkdir(WORKSPACE_DIR, { recursive: true });
}

export async function executeCode(
  language: string,
  code: string,
  timeout = 30
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  await ensureWorkspaceDir();

  const fileId = uuid().slice(0, 8);
  let filePath: string;
  let command: string;

  switch (language) {
    case 'python':
      filePath = join(WORKSPACE_DIR, `script_${fileId}.py`);
      await writeFile(filePath, code);
      command = `python3 "${filePath}"`;
      break;
    case 'javascript':
      filePath = join(WORKSPACE_DIR, `script_${fileId}.js`);
      await writeFile(filePath, code);
      command = `node "${filePath}"`;
      break;
    case 'bash':
      filePath = join(WORKSPACE_DIR, `script_${fileId}.sh`);
      await writeFile(filePath, code);
      command = `bash "${filePath}"`;
      break;
    default:
      return {
        stdout: '',
        stderr: `Unsupported language: ${language}. Supported: python, javascript, bash`,
        exitCode: 1,
      };
  }

  return new Promise((resolve) => {
    const timeoutMs = timeout * 1000;
    const child = exec(
      command,
      { timeout: timeoutMs, maxBuffer: 1024 * 1024, cwd: WORKSPACE_DIR },
      async (error, stdout, stderr) => {
        // Cleanup temp file
        try {
          await unlink(filePath);
        } catch {
          // ignore cleanup errors
        }

        resolve({
          stdout: stdout?.toString() || '',
          stderr: stderr?.toString() || (error?.message || ''),
          exitCode: error?.code || (error ? 1 : 0),
        });
      }
    );

    // Force kill on timeout
    setTimeout(() => {
      child.kill('SIGKILL');
    }, timeoutMs + 1000);
  });
}

export async function runShellCommand(
  command: string,
  cwd?: string,
  timeout = 30
): Promise<{ stdout: string; stderr: string; exitCode: number }> {
  await ensureWorkspaceDir();

  // Security: block dangerous commands
  const blocked = ['rm -rf /', 'mkfs', 'dd if=/dev/zero', ':(){:|:&};:'];
  if (blocked.some((b) => command.includes(b))) {
    return {
      stdout: '',
      stderr: 'Command blocked for security reasons.',
      exitCode: 1,
    };
  }

  return new Promise((resolve) => {
    const timeoutMs = timeout * 1000;
    exec(
      command,
      {
        timeout: timeoutMs,
        maxBuffer: 1024 * 1024,
        cwd: cwd || WORKSPACE_DIR,
      },
      (error, stdout, stderr) => {
        resolve({
          stdout: stdout?.toString() || '',
          stderr: stderr?.toString() || (error?.message || ''),
          exitCode: error?.code || (error ? 1 : 0),
        });
      }
    );
  });
}
