// ============================================================================
// APEX Agent — DevOps Tool (Docker, Git, Deploy, CI/CD)
// ============================================================================

import { runShellCommand } from './code-execution';
import { writeFileContent } from './file-management';

export async function devopsAction(params: {
  action: string;
  command: string;
  config?: string;
}): Promise<{ output: string; error?: string }> {
  const { action, command, config } = params;

  switch (action) {
    case 'docker':
      return await dockerAction(command);
    case 'git':
      return await gitAction(command);
    case 'deploy':
      return await deployAction(command, config);
    case 'ci_cd':
      return await ciCdAction(command, config);
    case 'monitor':
      return await monitorAction(command);
    default:
      return { output: '', error: `Unknown DevOps action: ${action}` };
  }
}

async function dockerAction(
  command: string
): Promise<{ output: string; error?: string }> {
  // Validate docker is available
  const dockerCheck = await runShellCommand('which docker');
  if (dockerCheck.exitCode !== 0) {
    return {
      output: '',
      error: 'Docker is not installed or not in PATH.',
    };
  }

  // Security: block dangerous docker commands
  const blocked = ['--privileged', '--pid=host', '-v /:/'];
  if (blocked.some((b) => command.includes(b))) {
    return { output: '', error: 'Docker command blocked for security reasons.' };
  }

  const result = await runShellCommand(`docker ${command}`, undefined, 120);
  return {
    output: result.stdout || 'Command completed',
    error: result.exitCode !== 0 ? result.stderr : undefined,
  };
}

async function gitAction(
  command: string
): Promise<{ output: string; error?: string }> {
  const result = await runShellCommand(`git ${command}`, undefined, 30);
  return {
    output: result.stdout || 'Git command completed',
    error: result.exitCode !== 0 ? result.stderr : undefined,
  };
}

async function deployAction(
  command: string,
  config?: string
): Promise<{ output: string; error?: string }> {
  // Common deployment commands for free platforms
  if (config) {
    // If config is provided, write it to appropriate file
    let filename = '';
    if (command.includes('vercel')) filename = 'vercel.json';
    else if (command.includes('netlify')) filename = 'netlify.toml';
    else if (command.includes('render')) filename = 'render.yaml';
    else if (command.includes('fly')) filename = 'fly.toml';
    else filename = 'deploy-config.json';

    await writeFileContent(filename, config);
  }

  const result = await runShellCommand(command, undefined, 120);
  return {
    output: result.stdout || 'Deployment command completed',
    error: result.exitCode !== 0 ? result.stderr : undefined,
  };
}

async function ciCdAction(
  command: string,
  config?: string
): Promise<{ output: string; error?: string }> {
  if (config) {
    // Generate CI/CD config file
    const configPath = command.includes('github')
      ? '.github/workflows/ci.yml'
      : command.includes('gitlab')
        ? '.gitlab-ci.yml'
        : 'ci-config.yml';

    const writeResult = await writeFileContent(configPath, config);
    if (!writeResult.success) {
      return { output: '', error: writeResult.error };
    }
    return { output: `CI/CD config written to ${configPath}` };
  }

  const result = await runShellCommand(command, undefined, 60);
  return {
    output: result.stdout || 'CI/CD command completed',
    error: result.exitCode !== 0 ? result.stderr : undefined,
  };
}

async function monitorAction(
  command: string
): Promise<{ output: string; error?: string }> {
  const result = await runShellCommand(command, undefined, 15);
  return {
    output: result.stdout || 'Monitor command completed',
    error: result.exitCode !== 0 ? result.stderr : undefined,
  };
}
