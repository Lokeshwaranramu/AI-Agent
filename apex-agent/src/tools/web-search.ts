// ============================================================================
// APEX Agent — Web Search Tool (DuckDuckGo + URL Fetching)
// ============================================================================

interface SearchResult {
  title: string;
  url: string;
  snippet: string;
}

export async function webSearch(
  query: string,
  numResults = 5
): Promise<{ results: SearchResult[]; error?: string }> {
  try {
    // Use DuckDuckGo HTML search (no API key needed)
    const encodedQuery = encodeURIComponent(query);
    const response = await fetch(
      `https://html.duckduckgo.com/html/?q=${encodedQuery}`,
      {
        headers: {
          'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Search failed with status ${response.status}`);
    }

    const html = await response.text();
    const results: SearchResult[] = [];

    // Parse results from DuckDuckGo HTML
    const resultRegex =
      /<a rel="nofollow" class="result__a" href="([^"]*)"[^>]*>(.*?)<\/a>[\s\S]*?<a class="result__snippet"[^>]*>(.*?)<\/a>/g;
    let match;

    while ((match = resultRegex.exec(html)) !== null && results.length < numResults) {
      const url = decodeURIComponent(
        match[1].replace(/\/\/duckduckgo\.com\/l\/\?uddg=/, '').split('&')[0]
      );
      const title = match[2].replace(/<\/?[^>]+(>|$)/g, '').trim();
      const snippet = match[3].replace(/<\/?[^>]+(>|$)/g, '').trim();

      if (title && url) {
        results.push({ title, url, snippet });
      }
    }

    // Fallback: try a simpler regex if no results
    if (results.length === 0) {
      const simpleRegex =
        /<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/g;
      while (
        (match = simpleRegex.exec(html)) !== null &&
        results.length < numResults
      ) {
        const url = match[1];
        const title = match[2].trim();
        if (title && url) {
          results.push({ title, url, snippet: '' });
        }
      }
    }

    return { results };
  } catch (error) {
    return {
      results: [],
      error: `Search failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}

export async function fetchUrl(
  url: string,
  extractText = true
): Promise<{ content: string; error?: string }> {
  try {
    const response = await fetch(url, {
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        Accept: 'text/html,application/xhtml+xml,application/json,text/plain',
      },
      signal: AbortSignal.timeout(15000),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const contentType = response.headers.get('content-type') || '';
    let content = await response.text();

    if (extractText && contentType.includes('text/html')) {
      // Strip HTML tags and clean up text
      content = content
        .replace(/<script[\s\S]*?<\/script>/gi, '')
        .replace(/<style[\s\S]*?<\/style>/gi, '')
        .replace(/<nav[\s\S]*?<\/nav>/gi, '')
        .replace(/<footer[\s\S]*?<\/footer>/gi, '')
        .replace(/<header[\s\S]*?<\/header>/gi, '')
        .replace(/<[^>]+>/g, ' ')
        .replace(/&nbsp;/g, ' ')
        .replace(/&amp;/g, '&')
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&quot;/g, '"')
        .replace(/&#39;/g, "'")
        .replace(/\s+/g, ' ')
        .trim();

      // Truncate to prevent overwhelming the context
      if (content.length > 8000) {
        content = content.slice(0, 8000) + '\n\n[... content truncated at 8000 chars]';
      }
    }

    return { content };
  } catch (error) {
    return {
      content: '',
      error: `Fetch failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
