// ============================================================================
// APEX Agent — Tool Definitions (Ollama-compatible format)
// ============================================================================

import { OllamaTool, ToolDefinition } from '@/lib/types';

// ---------- Tool Registry ----------

export const TOOL_DEFINITIONS: ToolDefinition[] = [
  // ── Code Execution ──
  {
    name: 'execute_code',
    description:
      'Execute code in Python, JavaScript/Node.js, or Bash. Returns stdout, stderr, and exit code. Use this for calculations, data processing, file manipulation, or any programming task.',
    category: 'code_execution',
    parameters: {
      type: 'object',
      properties: {
        language: {
          type: 'string',
          description: 'Programming language to execute',
          enum: ['python', 'javascript', 'bash'],
        },
        code: {
          type: 'string',
          description: 'The code to execute',
        },
        timeout: {
          type: 'number',
          description: 'Execution timeout in seconds (default: 30)',
          default: 30,
        },
      },
      required: ['language', 'code'],
    },
  },
  {
    name: 'run_shell_command',
    description:
      'Run a shell command and return the output. Use for system operations, package management, git commands, etc.',
    category: 'code_execution',
    parameters: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'The shell command to run',
        },
        cwd: {
          type: 'string',
          description: 'Working directory (default: current directory)',
        },
        timeout: {
          type: 'number',
          description: 'Timeout in seconds (default: 30)',
          default: 30,
        },
      },
      required: ['command'],
    },
  },

  // ── Web Search ──
  {
    name: 'web_search',
    description:
      'Search the web for current information using DuckDuckGo. Returns relevant search results with titles, URLs, and snippets.',
    category: 'web_search',
    parameters: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'The search query',
        },
        num_results: {
          type: 'number',
          description: 'Number of results to return (default: 5)',
          default: 5,
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'fetch_url',
    description:
      'Fetch the content of a web page and return the text content. Use for reading articles, documentation, API responses, etc.',
    category: 'web_search',
    parameters: {
      type: 'object',
      properties: {
        url: {
          type: 'string',
          description: 'The URL to fetch',
        },
        extract_text: {
          type: 'boolean',
          description: 'Extract clean text from HTML (default: true)',
          default: true,
        },
      },
      required: ['url'],
    },
  },

  // ── Image Generation ──
  {
    name: 'generate_image',
    description:
      'Generate an image from a text prompt using Pollinations.ai (free, no API key needed). Returns the image URL.',
    category: 'image_generation',
    parameters: {
      type: 'object',
      properties: {
        prompt: {
          type: 'string',
          description: 'Detailed text description of the image to generate',
        },
        width: {
          type: 'number',
          description: 'Image width in pixels (default: 1024)',
          default: 1024,
        },
        height: {
          type: 'number',
          description: 'Image height in pixels (default: 1024)',
          default: 1024,
        },
        seed: {
          type: 'number',
          description: 'Random seed for reproducibility',
        },
      },
      required: ['prompt'],
    },
  },

  // ── Video Creation ──
  {
    name: 'create_video',
    description:
      'Create or edit a video using FFmpeg. Supports combining images, adding audio, trimming, converting formats, adding text overlays, and more.',
    category: 'video_creation',
    parameters: {
      type: 'object',
      properties: {
        ffmpeg_command: {
          type: 'string',
          description:
            'The FFmpeg command arguments (without the "ffmpeg" prefix). Example: "-i input.mp4 -vf scale=1280:720 output.mp4"',
        },
        description: {
          type: 'string',
          description: 'Human-readable description of what this video operation does',
        },
      },
      required: ['ffmpeg_command', 'description'],
    },
  },

  // ── File Management ──
  {
    name: 'read_file',
    description: 'Read the contents of a file. Returns the file content as text.',
    category: 'file_management',
    parameters: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'File path to read',
        },
        encoding: {
          type: 'string',
          description: 'File encoding (default: utf-8)',
          default: 'utf-8',
        },
      },
      required: ['path'],
    },
  },
  {
    name: 'write_file',
    description: 'Write content to a file. Creates the file if it does not exist, overwrites if it does.',
    category: 'file_management',
    parameters: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'File path to write to',
        },
        content: {
          type: 'string',
          description: 'Content to write to the file',
        },
        append: {
          type: 'boolean',
          description: 'Append to file instead of overwriting (default: false)',
          default: false,
        },
      },
      required: ['path', 'content'],
    },
  },
  {
    name: 'list_directory',
    description: 'List files and directories at a given path.',
    category: 'file_management',
    parameters: {
      type: 'object',
      properties: {
        path: {
          type: 'string',
          description: 'Directory path to list (default: current directory)',
          default: '.',
        },
        recursive: {
          type: 'boolean',
          description: 'List recursively (default: false)',
          default: false,
        },
      },
      required: [],
    },
  },

  // ── Browser Automation ──
  {
    name: 'browser_action',
    description:
      'Perform browser automation actions using a headless browser. Can navigate to URLs, click elements, fill forms, take screenshots, and extract data.',
    category: 'browser_automation',
    parameters: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          description: 'Action to perform',
          enum: ['navigate', 'click', 'type', 'screenshot', 'extract_text', 'evaluate'],
        },
        url: {
          type: 'string',
          description: 'URL to navigate to (for navigate action)',
        },
        selector: {
          type: 'string',
          description: 'CSS selector for click/type/extract actions',
        },
        text: {
          type: 'string',
          description: 'Text to type (for type action)',
        },
        script: {
          type: 'string',
          description: 'JavaScript to evaluate on the page (for evaluate action)',
        },
      },
      required: ['action'],
    },
  },

  // ── Data Analytics ──
  {
    name: 'analyze_data',
    description:
      'Analyze data using Python (Pandas, NumPy, Matplotlib). Provide a Python script that processes data and generates insights or visualizations.',
    category: 'data_analytics',
    parameters: {
      type: 'object',
      properties: {
        code: {
          type: 'string',
          description:
            'Python code for data analysis. Use pandas, numpy, matplotlib, seaborn. Save plots to files.',
        },
        data_source: {
          type: 'string',
          description: 'Path to data file (CSV, JSON, Excel) or inline data',
        },
      },
      required: ['code'],
    },
  },

  // ── Content Creation ──
  {
    name: 'create_content',
    description:
      'Generate professional content: blog posts, social media captions, documentation, emails, scripts, etc. The LLM handles this directly.',
    category: 'content_creation',
    parameters: {
      type: 'object',
      properties: {
        type: {
          type: 'string',
          description: 'Type of content to create',
          enum: [
            'blog_post',
            'social_media',
            'documentation',
            'email',
            'script',
            'readme',
            'pitch',
            'article',
          ],
        },
        topic: {
          type: 'string',
          description: 'The topic or subject of the content',
        },
        platform: {
          type: 'string',
          description: 'Target platform (for social media)',
          enum: ['twitter', 'linkedin', 'instagram', 'youtube', 'tiktok'],
        },
        tone: {
          type: 'string',
          description: 'Desired tone',
          enum: ['professional', 'casual', 'technical', 'creative', 'formal'],
        },
        length: {
          type: 'string',
          description: 'Desired length',
          enum: ['short', 'medium', 'long'],
        },
      },
      required: ['type', 'topic'],
    },
  },

  // ── ML Tools ──
  {
    name: 'ml_inference',
    description:
      'Run machine learning inference using Hugging Face free inference API. Supports text generation, classification, summarization, translation, etc.',
    category: 'ml_tools',
    parameters: {
      type: 'object',
      properties: {
        task: {
          type: 'string',
          description: 'ML task to perform',
          enum: [
            'text-generation',
            'text-classification',
            'summarization',
            'translation',
            'question-answering',
            'sentiment-analysis',
          ],
        },
        model: {
          type: 'string',
          description: 'Hugging Face model ID (e.g., "facebook/bart-large-cnn")',
        },
        input: {
          type: 'string',
          description: 'Input text for the model',
        },
      },
      required: ['task', 'input'],
    },
  },

  // ── DevOps ──
  {
    name: 'devops_action',
    description:
      'Perform DevOps operations: Docker commands, Git operations, deployment, CI/CD setup, monitoring.',
    category: 'devops',
    parameters: {
      type: 'object',
      properties: {
        action: {
          type: 'string',
          description: 'DevOps action to perform',
          enum: ['docker', 'git', 'deploy', 'ci_cd', 'monitor'],
        },
        command: {
          type: 'string',
          description: 'The specific command to run',
        },
        config: {
          type: 'string',
          description: 'Configuration content (for generating Dockerfiles, CI configs, etc.)',
        },
      },
      required: ['action', 'command'],
    },
  },
];

// ---------- Convert to Ollama format ----------

export function getOllamaTools(): OllamaTool[] {
  return TOOL_DEFINITIONS.map((tool) => ({
    type: 'function' as const,
    function: {
      name: tool.name,
      description: tool.description,
      parameters: {
        type: 'object',
        properties: tool.parameters.properties,
        required: tool.parameters.required || [],
      },
    },
  }));
}
