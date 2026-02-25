// ============================================================================
// APEX Agent — Data Analytics Tool
// ============================================================================

import { executeCode } from './code-execution';

export async function analyzeData(
  code: string,
  dataSource?: string
): Promise<{ output: string; error?: string; artifacts?: string[] }> {
  // Wrap in a Python script that ensures proper imports
  const wrappedCode = `
import sys
import os
os.makedirs('${process.cwd()}/public/generated', exist_ok=True)

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install pandas numpy matplotlib seaborn -q")
    import pandas as pd
    import numpy as np

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_theme()
except ImportError:
    pass

${dataSource ? `# Data source: ${dataSource}` : ''}

${code}
`;

  const result = await executeCode('python', wrappedCode, 60);

  const artifacts: string[] = [];
  // Check for generated files in the output
  const fileMatches = result.stdout.match(/saved?.*?['"](.*?)['"]/gi);
  if (fileMatches) {
    artifacts.push(...fileMatches);
  }

  return {
    output: result.stdout || 'Analysis complete (no output)',
    error: result.exitCode !== 0 ? result.stderr : undefined,
    artifacts,
  };
}
