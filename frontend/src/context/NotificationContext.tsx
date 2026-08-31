import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  actionLabel?: string;
  onAction?: () => void;
  duration?: number;
}

interface NotificationContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
  showSuccess: (title: string, message?: string) => string;
  showError: (title: string, message?: string, action?: { label: string; onClick: () => void }) => string;
  showWarning: (title: string, message?: string) => string;
  showInfo: (title: string, message?: string) => string;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    (toast: Omit<Toast, 'id'>) => {
      const id = 'toast_' + Math.random().toString(36).substring(2, 9);
      const newToast: Toast = { ...toast, id };
      setToasts((prev) => [...prev, newToast]);

      const duration = toast.duration ?? (toast.type === 'error' ? 8000 : 4500);
      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
      return id;
    },
    [removeToast]
  );

  const showSuccess = useCallback(
    (title: string, message?: string) => addToast({ type: 'success', title, message }),
    [addToast]
  );

  const showError = useCallback(
    (title: string, message?: string, action?: { label: string; onClick: () => void }) =>
      addToast({
        type: 'error',
        title,
        message,
        actionLabel: action?.label,
        onAction: action?.onClick,
        duration: 9000,
      }),
    [addToast]
  );

  const showWarning = useCallback(
    (title: string, message?: string) => addToast({ type: 'warning', title, message }),
    [addToast]
  );

  const showInfo = useCallback(
    (title: string, message?: string) => addToast({ type: 'info', title, message }),
    [addToast]
  );

  return (
    <NotificationContext.Provider
      value={{
        toasts,
        addToast,
        removeToast,
        showSuccess,
        showError,
        showWarning,
        showInfo,
      }}
    >
      {children}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </NotificationContext.Provider>
  );
};

export const useNotification = (): NotificationContextType => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

const ToastContainer: React.FC<{ toasts: Toast[]; onDismiss: (id: string) => void }> = ({
  toasts,
  onDismiss,
}) => {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-24 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      aria-live="polite"
    >
      {toasts.map((toast) => {
        const icons = {
          success: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />,
          error: <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />,
          warning: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
          info: <Info className="w-5 h-5 text-cyan-400 shrink-0" />,
        };

        const borders = {
          success: 'border-emerald-500/30 bg-emerald-950/90',
          error: 'border-rose-500/30 bg-rose-950/90',
          warning: 'border-amber-500/30 bg-amber-950/90',
          info: 'border-cyan-500/30 bg-cyan-950/90',
        };

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border backdrop-blur-md shadow-2xl text-sm transition-all duration-200 animate-slide-in ${borders[toast.type]}`}
          >
            {icons[toast.type]}
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-100">{toast.title}</p>
              {toast.message && (
                <p className="text-gray-300 text-xs mt-0.5 break-words line-clamp-3 leading-relaxed">
                  {toast.message}
                </p>
              )}
              {toast.actionLabel && toast.onAction && (
                <button
                  onClick={() => {
                    toast.onAction?.();
                    onDismiss(toast.id);
                  }}
                  className="mt-2 text-xs font-semibold px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white transition-colors"
                >
                  {toast.actionLabel}
                </button>
              )}
            </div>
            <button
              onClick={() => onDismiss(toast.id)}
              className="text-gray-400 hover:text-white transition-colors p-0.5 rounded"
              aria-label="Dismiss notification"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
