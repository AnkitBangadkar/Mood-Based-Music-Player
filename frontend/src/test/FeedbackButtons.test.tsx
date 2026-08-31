import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { FeedbackButtons } from '../components/generator/FeedbackButtons';
import { NotificationProvider } from '../context/NotificationContext';
import { api } from '../api/client';

describe('FeedbackButtons', () => {
  it('submits like feedback as fire-and-forget 202 and provides user feedback', async () => {
    const sendFeedbackSpy = vi.spyOn(api, 'sendFeedback').mockResolvedValue({
      feedback_id: 'fb_123',
      accepted: true,
    });
    const onSent = vi.fn();

    render(
      <NotificationProvider>
        <FeedbackButtons playlistId="pl_test" trackId="trk_1" onFeedbackSent={onSent} />
      </NotificationProvider>
    );

    const likeButton = screen.getByRole('button', { name: /^Like track$/i });
    fireEvent.click(likeButton);

    await waitFor(() => {
      expect(sendFeedbackSpy).toHaveBeenCalledWith({
        playlistId: 'pl_test',
        trackId: 'trk_1',
        value: 'like',
      });
      expect(onSent).toHaveBeenCalledWith('like');
    });
  });

  it('prevents duplicate submissions when clicking rapidly while request is in-flight', async () => {
    let resolveFeedback: (val: any) => void;
    const feedbackPromise = new Promise((resolve) => {
      resolveFeedback = resolve;
    });

    const sendFeedbackSpy = vi.spyOn(api, 'sendFeedback').mockImplementation(() => feedbackPromise as any);

    render(
      <NotificationProvider>
        <FeedbackButtons playlistId="pl_test" trackId="trk_1" />
      </NotificationProvider>
    );

    const likeButton = screen.getByRole('button', { name: /^Like track$/i });
    
    // First click triggers in-flight request
    fireEvent.click(likeButton);
    expect(sendFeedbackSpy).toHaveBeenCalledTimes(1);

    // Subsequent clicks while in-flight are ignored (disabled)
    fireEvent.click(likeButton);
    fireEvent.click(likeButton);
    expect(sendFeedbackSpy).toHaveBeenCalledTimes(1);

    // Resolve in-flight request
    resolveFeedback!({ feedback_id: 'fb_123', accepted: true });
    await waitFor(() => {
      expect(sendFeedbackSpy).toHaveBeenCalledTimes(1);
    });
  });
});
