import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, FastForward, Check } from 'lucide-react';
import { api, FeedbackValue } from '../../api';
import { useNotification } from '../../context/NotificationContext';

interface FeedbackButtonsProps {
  playlistId: string;
  trackId?: string | null;
  size?: 'sm' | 'md';
  onFeedbackSent?: (value: FeedbackValue) => void;
  className?: string;
}

export const FeedbackButtons: React.FC<FeedbackButtonsProps> = ({
  playlistId,
  trackId,
  size = 'md',
  onFeedbackSent,
  className = '',
}) => {
  const [activeValue, setActiveValue] = useState<FeedbackValue | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showSuccess, showError } = useNotification();

  const handleFeedback = async (value: FeedbackValue, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (isSubmitting) return;

    setIsSubmitting(true);
    // Optimistic UI state
    setActiveValue(value);

    try {
      // Fire-and-forget after 202 response
      await api.sendFeedback({
        playlistId,
        trackId: trackId ?? null,
        value,
      });

      const label = value === 'like' ? 'Liked' : value === 'dislike' ? 'Disliked' : 'Skipped';
      showSuccess(`Feedback Recorded: ${label}`);
      onFeedbackSent?.(value);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Feedback failed';
      showError('Feedback Error', errorMsg);
      // Revert active feedback state on failure
      setActiveValue(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const btnClasses = size === 'sm' ? 'p-1.5 text-xs' : 'p-2 text-sm';
  const iconSize = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4 h-4';
  const targetLabel = trackId ? 'track' : 'playlist';

  return (
    <div
      className={`inline-flex items-center bg-background-card/80 border border-background-border rounded-lg p-0.5 gap-0.5 ${className}`}
      data-testid="feedback-buttons"
      onClick={(e) => e.stopPropagation()}
      role="group"
      aria-label={`Feedback actions for ${targetLabel}`}
    >
      {/* Like Button */}
      <button
        onClick={(e) => handleFeedback('like', e)}
        title={`Like ${targetLabel}`}
        aria-label={`Like ${targetLabel}`}
        aria-pressed={activeValue === 'like'}
        disabled={isSubmitting}
        className={`${btnClasses} rounded-md transition-all flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden disabled:opacity-50 ${
          activeValue === 'like'
            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-xs'
            : 'text-gray-400 hover:text-emerald-300 hover:bg-background-hover'
        }`}
      >
        <ThumbsUp className={iconSize} />
        {activeValue === 'like' && <Check className="w-3 h-3 text-emerald-400" />}
      </button>

      {/* Dislike Button */}
      <button
        onClick={(e) => handleFeedback('dislike', e)}
        title={`Dislike ${targetLabel}`}
        aria-label={`Dislike ${targetLabel}`}
        aria-pressed={activeValue === 'dislike'}
        disabled={isSubmitting}
        className={`${btnClasses} rounded-md transition-all flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden disabled:opacity-50 ${
          activeValue === 'dislike'
            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40 shadow-xs'
            : 'text-gray-400 hover:text-rose-300 hover:bg-background-hover'
        }`}
      >
        <ThumbsDown className={iconSize} />
        {activeValue === 'dislike' && <Check className="w-3 h-3 text-rose-400" />}
      </button>

      {/* Skip Button */}
      <button
        onClick={(e) => handleFeedback('skip', e)}
        title={`Mark ${targetLabel} as skipped`}
        aria-label={`Mark ${targetLabel} as skipped`}
        aria-pressed={activeValue === 'skip'}
        disabled={isSubmitting}
        className={`${btnClasses} rounded-md transition-all flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden disabled:opacity-50 ${
          activeValue === 'skip'
            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40 shadow-xs'
            : 'text-gray-400 hover:text-amber-300 hover:bg-background-hover'
        }`}
      >
        <FastForward className={iconSize} />
        {activeValue === 'skip' && <Check className="w-3 h-3 text-amber-400" />}
      </button>
    </div>
  );
};
