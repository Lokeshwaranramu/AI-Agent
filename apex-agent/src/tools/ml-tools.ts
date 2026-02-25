// ============================================================================
// APEX Agent — ML Tools (Hugging Face Free Inference)
// ============================================================================

const HF_API_URL = 'https://api-inference.huggingface.co/models';

const DEFAULT_MODELS: Record<string, string> = {
  'text-generation': 'mistralai/Mistral-7B-Instruct-v0.3',
  'text-classification': 'distilbert-base-uncased-finetuned-sst-2-english',
  'summarization': 'facebook/bart-large-cnn',
  'translation': 'Helsinki-NLP/opus-mt-en-fr',
  'question-answering': 'deepset/roberta-base-squad2',
  'sentiment-analysis': 'distilbert-base-uncased-finetuned-sst-2-english',
};

export async function mlInference(params: {
  task: string;
  model?: string;
  input: string;
}): Promise<{ result: string; error?: string }> {
  const { task, input } = params;
  const model = params.model || DEFAULT_MODELS[task] || DEFAULT_MODELS['text-generation'];

  try {
    const hfToken = process.env.HF_TOKEN || '';
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (hfToken) {
      headers['Authorization'] = `Bearer ${hfToken}`;
    }

    let body: unknown;

    switch (task) {
      case 'text-generation':
        body = {
          inputs: input,
          parameters: { max_new_tokens: 500, temperature: 0.7 },
        };
        break;
      case 'summarization':
        body = {
          inputs: input,
          parameters: { max_length: 200, min_length: 50 },
        };
        break;
      case 'question-answering':
        body = {
          inputs: {
            question: input,
            context: input,
          },
        };
        break;
      default:
        body = { inputs: input };
    }

    const response = await fetch(`${HF_API_URL}/${model}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30000),
    });

    if (!response.ok) {
      const errorText = await response.text();
      if (response.status === 503) {
        return {
          result: '',
          error: `Model "${model}" is loading. Please try again in a few seconds.`,
        };
      }
      throw new Error(`HF API error (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    let result = '';

    if (Array.isArray(data)) {
      if (data[0]?.generated_text) {
        result = data[0].generated_text;
      } else if (data[0]?.summary_text) {
        result = data[0].summary_text;
      } else if (data[0]?.label) {
        result = data
          .map((d: { label: string; score: number }) => `${d.label}: ${(d.score * 100).toFixed(1)}%`)
          .join('\n');
      } else if (data[0]?.translation_text) {
        result = data[0].translation_text;
      } else {
        result = JSON.stringify(data, null, 2);
      }
    } else if (data?.answer) {
      result = `Answer: ${data.answer} (confidence: ${(data.score * 100).toFixed(1)}%)`;
    } else {
      result = JSON.stringify(data, null, 2);
    }

    return { result };
  } catch (error) {
    return {
      result: '',
      error: `ML inference failed: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
