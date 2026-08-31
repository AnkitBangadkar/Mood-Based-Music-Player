import React from 'react';
import { Menu, Sparkles, Library, FolderSearch, RefreshCw } from 'lucide-react';
import { ActiveScreen } from './Sidebar';
import { useLibraryScan } from '../../context/LibraryScanContext';

interface HeaderProps {
  activeScreen: ActiveScreen;
  onOpenMobileMenu: () => void;
}

export const Header: React.FC<HeaderProps> = ({ activeScreen, onOpenMobileMenu }) => {
  const { stats, isScanning } = useLibraryScan();

  const titles: Record<ActiveScreen, { title: string; icon: React.ElementType }> = {
    generator: { title: 'Playlist Generator', icon: Sparkles },
    library: { title: 'Track Library', icon: Library },
    setup: { title: 'Library Setup', icon: FolderSearch },
  };

  const current = titles[activeScreen];
  const Icon = current.icon;

  return (
    <header className="h-16 border-b border-background-border bg-background/80 backdrop-blur-md flex items-center justify-between px-4 md:px-8 z-20 shrink-0">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        <button
          onClick={onOpenMobileMenu}
          className="p-2 md:hidden text-gray-400 hover:text-white rounded-lg hover:bg-background-hover focus-visible:ring-2 focus-visible:ring-brand-400 focus:outline-hidden"
          aria-label="Open Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-brand-400" />
          <span className="font-bold text-gray-100 text-base md:text-lg">{current.title}</span>
        </div>
      </div>

      {/* Quick summary stats in top bar */}
      <div className="flex items-center gap-3 text-xs">
        {isScanning && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/30 text-brand-300 animate-pulse">
            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            <span className="font-semibold">Library Scan Active</span>
          </div>
        )}

        {stats && (
          <div className="hidden sm:flex items-center gap-2 text-gray-400">
            <span className="bg-background-card px-2.5 py-1 rounded-lg border border-background-border">
              <span className="font-mono text-gray-200 font-semibold">{stats.track_count}</span> tracks
            </span>
          </div>
        )}
      </div>
    </header>
  );
};
