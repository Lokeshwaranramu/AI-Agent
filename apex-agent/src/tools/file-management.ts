// ============================================================================
// APEX Agent — File Management Tool
// ============================================================================

import {
  readFile as fsReadFile,
  writeFile as fsWriteFile,
  readdir,
  stat,
  mkdir,
  appendFile,
} from 'fs/promises';
import { join, resolve } from 'path';

const WORKSPACE_ROOT = process.cwd();

function sanitizePath(inputPath: string): string {
  // Resolve relative to workspace root and prevent directory traversal
  const resolved = resolve(WORKSPACE_ROOT, inputPath);
  return resolved;
}

export async function readFileContent(
  path: string,
  encoding: BufferEncoding = 'utf-8'
): Promise<{ content: string; error?: string }> {
  try {
    const safePath = sanitizePath(path);
    const content = await fsReadFile(safePath, { encoding });
    return { content };
  } catch (error) {
    return {
      content: '',
      error: `Failed to read file: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function writeFileContent(
  path: string,
  content: string,
  append = false
): Promise<{ success: boolean; error?: string }> {
  try {
    const safePath = sanitizePath(path);

    // Ensure directory exists
    const dir = safePath.substring(0, safePath.lastIndexOf('/'));
    await mkdir(dir, { recursive: true });

    if (append) {
      await appendFile(safePath, content, 'utf-8');
    } else {
      await fsWriteFile(safePath, content, 'utf-8');
    }

    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: `Failed to write file: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

interface FileEntry {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
}

export async function listDirectory(
  path = '.',
  recursive = false
): Promise<{ entries: FileEntry[]; error?: string }> {
  try {
    const safePath = sanitizePath(path);
    const entries: FileEntry[] = [];

    async function scanDir(dirPath: string, prefix = '') {
      const items = await readdir(dirPath);

      for (const item of items) {
        // Skip hidden files and node_modules
        if (item.startsWith('.') || item === 'node_modules') continue;

        const fullPath = join(dirPath, item);
        try {
          const stats = await stat(fullPath);
          const entry: FileEntry = {
            name: prefix ? `${prefix}/${item}` : item,
            type: stats.isDirectory() ? 'directory' : 'file',
            size: stats.isFile() ? stats.size : undefined,
            modified: stats.mtime.toISOString(),
          };
          entries.push(entry);

          if (recursive && stats.isDirectory()) {
            await scanDir(fullPath, entry.name);
          }
        } catch {
          // Skip files we can't access
        }
      }
    }

    await scanDir(safePath);
    return { entries };
  } catch (error) {
    return {
      entries: [],
      error: `Failed to list directory: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
