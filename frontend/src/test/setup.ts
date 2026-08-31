import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { vi, afterEach } from 'vitest';

// Mock HTMLMediaElement / Audio
export class MockAudio {
  static instances: MockAudio[] = [];

  src = '';
  currentTime = 0;
  duration = 180;
  volume = 1;
  muted = false;
  paused = true;
  preload = 'auto';
  error: { code: number; message: string } | null = null;

  private listeners: Record<string, EventListenerOrEventListenerObject[]> = {};

  constructor() {
    MockAudio.instances.push(this);
  }

  addEventListener(event: string, callback: EventListenerOrEventListenerObject) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  removeEventListener(event: string, callback: EventListenerOrEventListenerObject) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter((cb) => cb !== callback);
    }
  }

  dispatchEvent(event: Event): boolean {
    const handlers = this.listeners[event.type] || [];
    handlers.forEach((h) => {
      if (typeof h === 'function') {
        h(event);
      } else {
        h.handleEvent(event);
      }
    });
    return true;
  }

  load = vi.fn();

  play = vi.fn().mockImplementation(() => {
    this.paused = false;
    this.dispatchEvent(new Event('play'));
    return Promise.resolve();
  });

  pause = vi.fn().mockImplementation(() => {
    this.paused = true;
    this.dispatchEvent(new Event('pause'));
  });
}

afterEach(() => {
  cleanup();
  MockAudio.instances = [];
});

// Assign to global Window
global.Audio = MockAudio as unknown as typeof Audio;

// Mock window.navigator.clipboard
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
});
