// ============================================================================
// APEX Agent — Content Creation Tool
// ============================================================================

interface ContentResult {
  content: string;
  metadata: {
    type: string;
    topic: string;
    platform?: string;
    tone?: string;
    wordCount: number;
  };
}

export function createContentPrompt(params: {
  type: string;
  topic: string;
  platform?: string;
  tone?: string;
  length?: string;
}): ContentResult {
  const { type, topic, platform, tone = 'professional', length = 'medium' } = params;

  const lengthGuide = {
    short: '100-200 words',
    medium: '300-500 words',
    long: '800-1500 words',
  };

  const platformGuide: Record<string, string> = {
    twitter: 'max 280 characters, use hashtags, punchy and engaging',
    linkedin: 'professional tone, industry insights, 1-3 paragraphs with line breaks',
    instagram: 'visual-first description, emojis allowed, relevant hashtags (up to 30)',
    youtube: 'SEO-optimized title, description with timestamps, engaging thumbnail concept',
    tiktok: 'trend-aware, hook in first 3 seconds, casual and authentic',
  };

  let prompt = '';

  switch (type) {
    case 'blog_post':
      prompt = `Write a ${tone} blog post about "${topic}". Length: ${lengthGuide[length as keyof typeof lengthGuide] || lengthGuide.medium}. Include: compelling headline, introduction, main sections with subheadings, conclusion, and a call-to-action.`;
      break;

    case 'social_media':
      prompt = `Create a ${tone} social media post about "${topic}" for ${platform || 'general'}. ${platform && platformGuide[platform] ? `Platform guidelines: ${platformGuide[platform]}.` : ''} Make it engaging and shareable.`;
      break;

    case 'documentation':
      prompt = `Write technical documentation for "${topic}". Include: overview, installation/setup, usage examples with code snippets, API reference if applicable, and troubleshooting section. Use clear, concise language.`;
      break;

    case 'email':
      prompt = `Write a ${tone} email about "${topic}". Include a clear subject line, greeting, body with the main message, and a professional closing. Length: ${lengthGuide[length as keyof typeof lengthGuide] || lengthGuide.medium}.`;
      break;

    case 'script':
      prompt = `Write a ${tone} script about "${topic}". Include speaker directions, dialogue, timing notes, and scene descriptions. Target length: ${lengthGuide[length as keyof typeof lengthGuide] || lengthGuide.medium}.`;
      break;

    case 'readme':
      prompt = `Write a comprehensive README.md for a project about "${topic}". Include: project title with badge suggestions, description, features list, installation instructions, usage examples, configuration options, contributing guidelines, and license section. Use proper Markdown formatting.`;
      break;

    case 'pitch':
      prompt = `Create a ${tone} pitch deck outline for "${topic}". Include: title slide, problem statement, solution, market opportunity, business model, traction/milestones, team, and ask/closing. Make each slide concise but compelling.`;
      break;

    case 'article':
      prompt = `Write a ${tone} article about "${topic}". Length: ${lengthGuide[length as keyof typeof lengthGuide] || lengthGuide.medium}. Include research-backed points, expert perspective, and actionable takeaways.`;
      break;

    default:
      prompt = `Create ${type} content about "${topic}" in a ${tone} tone. Length: ${lengthGuide[length as keyof typeof lengthGuide] || lengthGuide.medium}.`;
  }

  // The content creation is handled by the LLM itself, so we return
  // the constructed prompt for the agent to process
  return {
    content: prompt,
    metadata: {
      type,
      topic,
      platform,
      tone,
      wordCount: 0, // Will be filled by the LLM response
    },
  };
}
