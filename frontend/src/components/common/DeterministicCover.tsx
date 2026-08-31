import React from 'react';
import { Music } from 'lucide-react';
import { getDeterministicPalette, stringToHash } from '../../utils/colors';

interface DeterministicCoverProps {
  title?: string;
  artist?: string;
  album?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export const DeterministicCover: React.FC<DeterministicCoverProps> = ({
  title = '',
  artist = '',
  album = '',
  size = 'md',
  className = '',
}) => {
  const seed = `${artist}-${album}-${title}`.trim() || 'soulseek-track';
  const palette = getDeterministicPalette(seed);
  const hash = stringToHash(seed);
  
  // Pick initials or fallback
  const firstLetter = (title || artist || album || 'S').trim().charAt(0).toUpperCase();

  const sizeClasses = {
    sm: 'w-10 h-10 text-xs rounded-md',
    md: 'w-12 h-12 text-sm rounded-lg',
    lg: 'w-16 h-16 text-base rounded-xl',
    xl: 'w-32 h-32 text-2xl rounded-2xl',
  }[size];

  // Geometric pattern seed for aesthetic background shapes
  const patternType = hash % 4;

  return (
    <div
      className={`relative overflow-hidden flex-shrink-0 flex items-center justify-center font-bold bg-gradient-to-br border ${palette.bg} ${palette.text} ${palette.border} ${sizeClasses} ${className} shadow-sm select-none`}
      data-testid="deterministic-cover"
      title={`${title} by ${artist}`}
    >
      {/* Abstract geometric accents */}
      {patternType === 0 && (
        <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-white/10 blur-[1px]" />
      )}
      {patternType === 1 && (
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-white/15 to-transparent" />
      )}
      {patternType === 2 && (
        <div className="absolute -bottom-2 -left-2 w-10 h-10 rotate-45 bg-white/5" />
      )}
      {patternType === 3 && (
        <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />
      )}

      {/* Monogram / Icon */}
      <span className="relative z-10 font-semibold tracking-wider flex items-center justify-center">
        {firstLetter || <Music className="w-1/2 h-1/2 opacity-70" />}
      </span>
    </div>
  );
};
