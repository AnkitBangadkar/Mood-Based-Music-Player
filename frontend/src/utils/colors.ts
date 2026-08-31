/**
 * Generates deterministic colors and geometric patterns for track/album artwork
 * without fabricating external artwork images.
 */

export function stringToHash(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

const PALETTES = [
  { bg: 'from-purple-900 to-indigo-950', text: 'text-purple-200', border: 'border-purple-500/30' },
  { bg: 'from-teal-900 to-emerald-950', text: 'text-teal-200', border: 'border-teal-500/30' },
  { bg: 'from-rose-900 to-red-950', text: 'text-rose-200', border: 'border-rose-500/30' },
  { bg: 'from-amber-900 to-orange-950', text: 'text-amber-200', border: 'border-amber-500/30' },
  { bg: 'from-cyan-900 to-blue-950', text: 'text-cyan-200', border: 'border-cyan-500/30' },
  { bg: 'from-fuchsia-900 to-pink-950', text: 'text-fuchsia-200', border: 'border-fuchsia-500/30' },
  { bg: 'from-violet-900 to-purple-950', text: 'text-violet-200', border: 'border-violet-500/30' },
  { bg: 'from-emerald-900 to-teal-950', text: 'text-emerald-200', border: 'border-emerald-500/30' },
];

export function getDeterministicPalette(seed: string): typeof PALETTES[number] {
  const hash = stringToHash(seed || 'soulseek');
  return PALETTES[hash % PALETTES.length];
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined || isNaN(seconds)) return '--:--';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
}
