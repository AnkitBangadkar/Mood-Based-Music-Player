import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { api, JobResponse, LibraryStatsResponse, ApiError, ScanJobResult, ScanErrorSample } from '../api';
import { useNotification } from './NotificationContext';

interface LibraryScanContextType {
  stats: LibraryStatsResponse | null;
  isLoadingStats: boolean;
  activeJob: JobResponse | null;
  scanResult: ScanJobResult | null;
  errorSamples: ScanErrorSample[];
  isScanning: boolean;
  scanError: string | null;
  refreshStats: () => Promise<void>;
  startScan: (root: string) => Promise<void>;
  resumeJob: (jobId: string) => void;
  cancelScanning: () => void;
}

const LibraryScanContext = createContext<LibraryScanContextType | undefined>(undefined);

export const LibraryScanProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [stats, setStats] = useState<LibraryStatsResponse | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [activeJob, setActiveJob] = useState<JobResponse | null>(null);
  const [scanResult, setScanResult] = useState<ScanJobResult | null>(null);
  const [errorSamples, setErrorSamples] = useState<ScanErrorSample[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);
  const { showSuccess, showError, showInfo } = useNotification();

  const refreshStats = useCallback(async () => {
    setIsLoadingStats(true);
    try {
      const data = await api.getLibraryStats();
      setStats(data);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch library stats';
      showError('Library Stats Error', errorMsg);
    } finally {
      setIsLoadingStats(false);
    }
  }, [showError]);

  useEffect(() => {
    refreshStats();
  }, [refreshStats]);

  useEffect(() => {
    return () => abortControllerRef.current?.abort();
  }, []);

  const pollJob = useCallback(
    async (jobId: string) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setIsScanning(true);
      setScanError(null);
      setErrorSamples([]);
      setScanResult(null);

      try {
        const finalJob = await api.pollJobUntilDone(
          jobId,
          (currentJob) => {
            setActiveJob(currentJob);
            if (currentJob.result && 'error_samples' in currentJob.result) {
              const res = currentJob.result as ScanJobResult;
              setScanResult(res);
              if (Array.isArray(res.error_samples)) {
                setErrorSamples(res.error_samples);
              }
            }
          },
          800,
          controller.signal
        );

        setActiveJob(finalJob);
        if (finalJob.result && 'error_samples' in finalJob.result) {
          const res = finalJob.result as ScanJobResult;
          setScanResult(res);
          if (Array.isArray(res.error_samples)) {
            setErrorSamples(res.error_samples);
          }
        }

        if (finalJob.status === 'succeeded') {
          showSuccess(
            'Library Scan Succeeded',
            finalJob.message || 'Music library scan and indexing completed successfully.'
          );
          await refreshStats();
        } else if (finalJob.status === 'failed') {
          const errMessage =
            (finalJob.error && typeof finalJob.error.message === 'string'
              ? finalJob.error.message
              : finalJob.message) || 'Library scan failed';
          setScanError(errMessage);
          showError('Library Scan Failed', errMessage);
        }
      } catch (err: unknown) {
        if (err instanceof Error && err.message === 'Polling aborted') {
          return;
        }
        const errorMsg = err instanceof Error ? err.message : 'Error while tracking scan job';
        setScanError(errorMsg);
        showError('Scan Tracking Error', errorMsg);
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
          setIsScanning(false);
        }
      }
    },
    [refreshStats, showSuccess, showError]
  );

  const startScan = useCallback(
    async (root: string) => {
      setScanError(null);
      setErrorSamples([]);
      setScanResult(null);
      try {
        const response = await api.startScan(root);
        showInfo('Library Scan Started', `Job ID: ${response.job_id}`);
        await pollJob(response.job_id);
      } catch (err: unknown) {
        if (err instanceof ApiError && err.isScanAlreadyRunning) {
          const runningJobId = err.runningJobId;
          showInfo('Scan Already Running', 'Connecting to the active background scan job...');
          if (runningJobId) {
            await pollJob(runningJobId);
            return;
          }
        }
        const errorMsg = err instanceof Error ? err.message : 'Failed to start library scan';
        setScanError(errorMsg);
        showError('Failed to Start Scan', errorMsg);
        throw err;
      }
    },
    [pollJob, showError, showInfo]
  );

  const resumeJob = useCallback(
    (jobId: string) => {
      pollJob(jobId);
    },
    [pollJob]
  );

  const cancelScanning = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsScanning(false);
  }, []);

  return (
    <LibraryScanContext.Provider
      value={{
        stats,
        isLoadingStats,
        activeJob,
        scanResult,
        errorSamples,
        isScanning,
        scanError,
        refreshStats,
        startScan,
        resumeJob,
        cancelScanning,
      }}
    >
      {children}
    </LibraryScanContext.Provider>
  );
};

export const useLibraryScan = (): LibraryScanContextType => {
  const context = useContext(LibraryScanContext);
  if (!context) {
    throw new Error('useLibraryScan must be used within a LibraryScanProvider');
  }
  return context;
};
