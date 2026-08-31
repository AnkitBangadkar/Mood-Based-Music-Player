import React, { useEffect, useState } from 'react';
import {
  Sparkles,
  Library,
  FolderSearch,
  Radio,
  CheckCircle2,
  AlertCircle,
  Activity,
} from 'lucide-react';
import { api, HealthResponse } from '../../api';
import { useLibraryScan } from '../../context/LibraryScanContext';

export type ActiveScreen = 'generator' | 'library' | 'setup';

interface SidebarProps {
  activeScreen: ActiveScreen;
  onSelectScreen: (screen: ActiveScreen) => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeScreen,
  onSelectScreen,
  isOpenMobile,
  onCloseMobile,
}) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState(false);
  const { stats, isScanning } = useLibraryScan();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await api.getHealth();
        setHealth(data);
        setHealthError(false);
      } catch {
        setHealthError(true);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    {
      id: 'generator' as ActiveScreen,
      label: 'Playlist Generator',
      icon: Sparkles,
      badge: null,
    },
    {
      id: 'library' as ActiveScreen,
      label: 'Track Library',
      icon: Library,
      badge: stats ? `${stats.track_count}` : null,
    },
    {
      id: 'setup' as ActiveScreen,
      label: 'Library Setup',
      icon: FolderSearch,
      badge: isScanning ? 'Scanning' : null,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpenMobile && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-xs"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-background border-r border-background-border flex flex-col justify-between p-4 transition-transform duration-300 ${
          isOpenMobile ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
        data-testid="app-sidebar"
      >
        <div className="space-y-6">
          {/* Logo & Brand */}
          <div className="flex items-center gap-3 px-2 py-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center text-background-darker shadow-lg shadow-brand-500/25">
              <Radio className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <h1 className="font-extrabold text-lg text-gray-100 tracking-tight flex items-center gap-1.5">
                <span>SoulSeek</span>
              </h1>
              <p className="text-[11px] text-brand-400 font-medium">Local-First AI Discovery</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeScreen === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelectScreen(item.id);
                    onCloseMobile();
                  }}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden ${
                    isActive
                      ? 'bg-brand-500/15 text-brand-300 border border-brand-500/30 shadow-xs'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-background-hover'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-brand-400' : 'text-gray-500'}`} />
                    <span>{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${
                        item.badge === 'Scanning'
                          ? 'bg-brand-500/20 text-brand-300 animate-pulse border border-brand-500/40'
                          : 'bg-background-card text-gray-400 border border-background-border'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Backend & Encoder Status Card */}
        <div className="space-y-3 pt-4 border-t border-background-border/50">
          <div className="p-3 bg-background-card/80 border border-background-border/60 rounded-xl space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400 font-medium flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-brand-400" />
                Backend Status
              </span>
              {healthError ? (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-rose-400">
                  <AlertCircle className="w-3 h-3" /> Offline
                </span>
              ) : health ? (
                <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
                  <CheckCircle2 className="w-3 h-3" /> v{health.version}
                </span>
              ) : (
                <span className="text-[11px] text-gray-500">Checking...</span>
              )}
            </div>

            {health && (
              <div className="text-[10px] font-mono text-gray-400 pt-1 border-t border-background-border/30 truncate" title={`Encoder: ${health.encoder_id}`}>
                Encoder: <span className="text-purple-300">{health.encoder_id}</span>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
