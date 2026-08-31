import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';

interface ScoreBadgeProps {
  score: number;
  className?: string;
}

export const ScoreBadge: React.FC<ScoreBadgeProps> = ({ score, className = '' }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Format internal utility score (e.g. 0.842 or 1.234)
  const formattedScore = typeof score === 'number' ? score.toFixed(3) : String(score);

  return (
    <div className={`relative inline-flex items-center gap-1 ${className}`}>
      <span
        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium bg-background-card/90 text-brand-300 border border-brand-500/20 shadow-xs cursor-help"
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip((prev) => !prev)}
        title="Internal ranking utility (not a percentage)"
      >
        <span className="text-gray-400 mr-1 text-[10px]">Rank Utility:</span>
        {formattedScore}
        <HelpCircle className="w-3 h-3 ml-1 text-gray-400 opacity-70" />
      </span>

      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-52 p-2 bg-background-card border border-background-border rounded-lg shadow-xl text-[11px] text-gray-300 z-50 pointer-events-none backdrop-blur-md">
          <p className="font-semibold text-brand-300 mb-0.5">Relative Ranking Utility</p>
          <p className="text-gray-400 leading-tight">
            Internal mathematical score used to balance semantic relevance and diversity. This is not a confidence percentage.
          </p>
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-background-border" />
        </div>
      )}
    </div>
  );
};
