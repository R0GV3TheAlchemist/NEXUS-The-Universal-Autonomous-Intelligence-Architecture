/**
 * src/memory/promptMemory.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Pure utility: inject a semantic memory context block into any system prompt.
 *
 * Usage
 * ─────
 *   import { injectMemoryContext } from './promptMemory';
 *
 *   // Option A — placeholder substitution
 *   const prompt = `You are GAIA.\n{{memory_context}}\nNow answer:`;
 *   const final  = injectMemoryContext(prompt, hits);
 *
 *   // Option B — automatic append (no placeholder needed)
 *   const prompt2 = `You are GAIA.`;
 *   const final2  = injectMemoryContext(prompt2, hits);
 *
 * The injected block looks like:
 *
 *   <GAIA_MEMORY>
 *   The following memories are semantically relevant to this conversation.
 *   Use them to personalize your response. Do not reference them literally
 *   unless directly asked.
 *
 *   [1] (preference, importance=0.90) I prefer dark mode
 *   [2] (fact, importance=0.80) User is based in San Antonio, Texas
 *   [3] (goal, importance=0.75) Building a sovereign AI OS called GAIA
 *   </GAIA_MEMORY>
 */

import type { MemoryHit } from './memoryClient';

/** The placeholder string used in system prompt templates. */
export const MEMORY_PLACEHOLDER = '{{memory_context}}';

/** Maximum characters for a single memory item's text in the prompt. */
const MAX_ITEM_CHARS = 300;

/**
 * Format a list of MemoryHit objects into the <GAIA_MEMORY> block string.
 * Returns an empty string when hits is empty.
 */
export function formatMemoryBlock(hits: MemoryHit[]): string {
  if (!hits.length) return '';

  const lines = hits.map((h, i) => {
    const text = h.text.length > MAX_ITEM_CHARS
      ? h.text.slice(0, MAX_ITEM_CHARS) + '…'
      : h.text;
    return `[${i + 1}] (${h.kind}, importance=${h.importance.toFixed(2)}, score=${h.score.toFixed(3)}) ${text}`;
  });

  return [
    '<GAIA_MEMORY>',
    'The following memories are semantically relevant to this conversation.',
    'Use them to personalize your response. Do not reference them literally unless directly asked.',
    '',
    ...lines,
    '</GAIA_MEMORY>',
  ].join('\n');
}

/**
 * Inject the memory block into a system prompt.
 *
 * - If the prompt contains `{{memory_context}}`, replaces it.
 * - Otherwise appends the block at the end, separated by two newlines.
 * - Returns the original prompt unchanged when hits is empty.
 */
export function injectMemoryContext(
  systemPrompt: string,
  hits: MemoryHit[]
): string {
  if (!hits.length) return systemPrompt;

  const block = formatMemoryBlock(hits);

  if (systemPrompt.includes(MEMORY_PLACEHOLDER)) {
    return systemPrompt.replace(MEMORY_PLACEHOLDER, block);
  }

  return `${systemPrompt}\n\n${block}`;
}

/**
 * Strip the <GAIA_MEMORY> block from a prompt (useful for display).
 */
export function stripMemoryBlock(prompt: string): string {
  return prompt.replace(/<GAIA_MEMORY>[\s\S]*?<\/GAIA_MEMORY>/g, '').trim();
}
