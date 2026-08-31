import React, { useState } from 'react';
import { NotificationProvider } from './context/NotificationContext';
import { LibraryScanProvider } from './context/LibraryScanContext';
import { AudioPlayerProvider } from './context/AudioPlayerContext';
import { Sidebar, ActiveScreen } from './components/common/Sidebar';
import { Header } from './components/common/Header';
import { PlaylistGenerator } from './components/generator/PlaylistGenerator';
import { TrackBrowser } from './components/library/TrackBrowser';
import { LibrarySetup } from './components/library/LibrarySetup';
import { PersistentPlayer } from './components/player/PersistentPlayer';
import { QueueDrawer } from './components/player/QueueDrawer';

const AppContent: React.FC = () => {
  const [activeScreen, setActiveScreen] = useState<ActiveScreen>('generator');
  const [isOpenMobile, setIsOpenMobile] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-gray-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar
        activeScreen={activeScreen}
        onSelectScreen={setActiveScreen}
        isOpenMobile={isOpenMobile}
        onCloseMobile={() => setIsOpenMobile(false)}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden pb-24">
        <Header
          activeScreen={activeScreen}
          onOpenMobileMenu={() => setIsOpenMobile(true)}
        />

        <main className="flex-1 overflow-hidden flex flex-col">
          {activeScreen === 'generator' && (
            <PlaylistGenerator onNavigateToSetup={() => setActiveScreen('setup')} />
          )}
          {activeScreen === 'library' && (
            <TrackBrowser onNavigateToSetup={() => setActiveScreen('setup')} />
          )}
          {activeScreen === 'setup' && <LibrarySetup />}
        </main>
      </div>

      {/* Queue Side Drawer */}
      <QueueDrawer />

      {/* Global Persistent HTML5 Audio Player */}
      <PersistentPlayer />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <NotificationProvider>
      <LibraryScanProvider>
        <AudioPlayerProvider>
          <AppContent />
        </AudioPlayerProvider>
      </LibraryScanProvider>
    </NotificationProvider>
  );
};

export default App;
