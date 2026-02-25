// ============================================================================
// APEX Agent — Tool Executor (routes tool calls to implementations)
// ============================================================================

import { ToolCall, ToolResult } from './types';
import { executeCode, runShellCommand } from '@/tools/code-execution';
import { webSearch, fetchUrl } from '@/tools/web-search';
import { generateImage } from '@/tools/image-generation';
import { createVideo } from '@/tools/video-creation';
import { readFileContent, writeFileContent, listDirectory } from '@/tools/file-management';
import { browserAction } from '@/tools/browser-automation';
import { analyzeData } from '@/tools/data-analytics';
import { createContentPrompt } from '@/tools/content-creation';
import { mlInference } from '@/tools/ml-tools';
import { devopsAction } from '@/tools/devops-tools';

export async function executeToolCall(toolCall: ToolCall): Promise<ToolResult> {
  const startTime = Date.now();
  const args = toolCall.arguments;

  try {
    let resultText = '';
    let success = true;

    switch (toolCall.name) {
      // ── Code Execution ──
      case 'execute_code': {
        const result = await executeCode(
          args.language as string,
          args.code as string,
          (args.timeout as number) || 30
        );
        resultText = result.exitCode === 0
          ? `✓ Code executed successfully.\n\nOutput:\n${result.stdout || '(no output)'}`
          : `✗ Code execution failed (exit code: ${result.exitCode}).\n\nStdout:\n${result.stdout}\n\nStderr:\n${result.stderr}`;
        success = result.exitCode === 0;
        break;
      }

      case 'run_shell_command': {
        const result = await runShellCommand(
          args.command as string,
          args.cwd as string | undefined,
          (args.timeout as number) || 30
        );
        resultText = result.exitCode === 0
          ? `✓ Command completed.\n\n${result.stdout || '(no output)'}`
          : `✗ Command failed (exit code: ${result.exitCode}).\n\n${result.stderr}`;
        success = result.exitCode === 0;
        break;
      }

      // ── Web Search ──
      case 'web_search': {
        const result = await webSearch(
          args.query as string,
          (args.num_results as number) || 5
        );
        if (result.error) {
          resultText = `Search error: ${result.error}`;
          success = false;
        } else {
          resultText = result.results.length > 0
            ? result.results
                .map((r, i) => `${i + 1}. **${r.title}**\n   ${r.url}\n   ${r.snippet}`)
                .join('\n\n')
            : 'No results found.';
        }
        break;
      }

      case 'fetch_url': {
        const result = await fetchUrl(
          args.url as string,
          (args.extract_text as boolean) ?? true
        );
        if (result.error) {
          resultText = `Fetch error: ${result.error}`;
          success = false;
        } else {
          resultText = result.content;
        }
        break;
      }

      // ── Image Generation ──
      case 'generate_image': {
        const result = await generateImage(
          args.prompt as string,
          (args.width as number) || 1024,
          (args.height as number) || 1024,
          args.seed as number | undefined
        );
        if (result.error) {
          resultText = `Image generation error: ${result.error}`;
          success = false;
        } else {
          resultText = `✓ Image generated successfully.\nURL: ${result.url}\nLocal: ${result.localPath}`;
        }
        break;
      }

      // ── Video Creation ──
      case 'create_video': {
        const result = await createVideo(
          args.ffmpeg_command as string,
          args.description as string
        );
        if (result.error) {
          resultText = `Video error: ${result.error}`;
          success = false;
        } else {
          resultText = result.output;
        }
        break;
      }

      // ── File Management ──
      case 'read_file': {
        const result = await readFileContent(
          args.path as string,
          (args.encoding as BufferEncoding) || 'utf-8'
        );
        if (result.error) {
          resultText = `Read error: ${result.error}`;
          success = false;
        } else {
          resultText = result.content;
        }
        break;
      }

      case 'write_file': {
        const result = await writeFileContent(
          args.path as string,
          args.content as string,
          (args.append as boolean) || false
        );
        if (result.error) {
          resultText = `Write error: ${result.error}`;
          success = false;
        } else {
          resultText = `✓ File written successfully: ${args.path}`;
        }
        break;
      }

      case 'list_directory': {
        const result = await listDirectory(
          (args.path as string) || '.',
          (args.recursive as boolean) || false
        );
        if (result.error) {
          resultText = `Directory error: ${result.error}`;
          success = false;
        } else {
          resultText = result.entries
            .map((e) => `${e.type === 'directory' ? '📁' : '📄'} ${e.name}${e.size ? ` (${formatSize(e.size)})` : ''}`)
            .join('\n') || '(empty directory)';
        }
        break;
      }

      // ── Browser Automation ──
      case 'browser_action': {
        const result = await browserAction({
          action: args.action as string,
          url: args.url as string | undefined,
          selector: args.selector as string | undefined,
          text: args.text as string | undefined,
          script: args.script as string | undefined,
        });
        if (result.error) {
          resultText = `Browser error: ${result.error}`;
          success = false;
        } else {
          resultText = result.result;
        }
        break;
      }

      // ── Data Analytics ──
      case 'analyze_data': {
        const result = await analyzeData(
          args.code as string,
          args.data_source as string | undefined
        );
        if (result.error) {
          resultText = `Analysis error: ${result.error}`;
          success = false;
        } else {
          resultText = result.output;
        }
        break;
      }

      // ── Content Creation ──
      case 'create_content': {
        const result = createContentPrompt({
          type: args.type as string,
          topic: args.topic as string,
          platform: args.platform as string | undefined,
          tone: args.tone as string | undefined,
          length: args.length as string | undefined,
        });
        resultText = result.content;
        break;
      }

      // ── ML Tools ──
      case 'ml_inference': {
        const result = await mlInference({
          task: args.task as string,
          model: args.model as string | undefined,
          input: args.input as string,
        });
        if (result.error) {
          resultText = `ML error: ${result.error}`;
          success = false;
        } else {
          resultText = result.result;
        }
        break;
      }

      // ── DevOps ──
      case 'devops_action': {
        const result = await devopsAction({
          action: args.action as string,
          command: args.command as string,
          config: args.config as string | undefined,
        });
        if (result.error) {
          resultText = `DevOps error: ${result.error}`;
          success = false;
        } else {
          resultText = result.output;
        }
        break;
      }

      default:
        resultText = `Unknown tool: ${toolCall.name}`;
        success = false;
    }

    return {
      toolCallId: toolCall.id,
      toolName: toolCall.name,
      result: resultText,
      success,
      duration: Date.now() - startTime,
    };
  } catch (error) {
    return {
      toolCallId: toolCall.id,
      toolName: toolCall.name,
      result: `Tool execution error: ${error instanceof Error ? error.message : String(error)}`,
      success: false,
      duration: Date.now() - startTime,
    };
  }
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}
