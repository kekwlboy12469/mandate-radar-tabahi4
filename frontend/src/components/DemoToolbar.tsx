import React, { useState } from 'react'
import {
  Monitor,
  Smartphone,
  Maximize2,
  Palette,
  Sparkles,
  Sliders,
  ChevronDown,
  ChevronUp,
  Layers,
  Shield,
  Eye
} from 'lucide-react'
import type { AuthState } from './AuthCard'

export type ViewportMode = 'responsive' | 'desktop-1440' | 'mobile-390'
export type ScreenView = 'login' | 'onboarding-1' | 'onboarding-2' | 'onboarding-3' | 'dashboard' | 'design-system'
export type ThemeMode = 'forest-sand' | 'sand-light' | 'dark-radar'

interface DemoToolbarProps {
  currentScreen: ScreenView
  onSelectScreen: (screen: ScreenView) => void
  currentViewport: ViewportMode
  onSelectViewport: (vp: ViewportMode) => void
  currentTheme: ThemeMode
  onSelectTheme: (theme: ThemeMode) => void
  currentAuthState: AuthState
  onSelectAuthState: (state: AuthState) => void
  onToggleDesignSystem: () => void
}

export const DemoToolbar: React.FC<DemoToolbarProps> = ({
  currentScreen,
  onSelectScreen,
  currentViewport,
  onSelectViewport,
  currentTheme,
  onSelectTheme,
  currentAuthState,
  onSelectAuthState,
  onToggleDesignSystem
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <aside
      aria-label="Demo and testing controls"
      className="fixed top-0 left-0 right-0 z-40 bg-[#07120D]/95 border-b border-[#203E30] backdrop-blur-md px-3 sm:px-6 py-2 transition-all shadow-xl"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3 text-xs">
        {/* Left: Brand badge & Screen switcher */}
        <div className="flex items-center gap-2 sm:gap-4 overflow-x-auto py-1 scrollbar-none">
          <div className="flex items-center gap-1.5 font-bold text-[#F7F3EB] shrink-0">
            <span className="w-2 h-2 rounded-full bg-[#2DE2B5] animate-ping" />
            <span className="hidden md:inline">Mandate Radar UI</span>
          </div>

          <div className="h-4 w-[1px] bg-[#203E30] hidden sm:block" />

          {/* Screen Buttons */}
          <div className="flex items-center gap-1 bg-[#0E1F17] p-0.5 rounded-lg border border-[#203E30] shrink-0">
            <button
              onClick={() => onSelectScreen('login')}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                currentScreen === 'login'
                  ? 'bg-[#2DE2B5] text-[#061A13] font-semibold shadow-sm'
                  : 'text-[#BAC8BF] hover:text-[#F7F3EB]'
              }`}
            >
              Login Screen
            </button>
            <button
              onClick={() => onSelectScreen('onboarding-1')}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                currentScreen.startsWith('onboarding')
                  ? 'bg-[#2DE2B5] text-[#061A13] font-semibold shadow-sm'
                  : 'text-[#BAC8BF] hover:text-[#F7F3EB]'
              }`}
            >
              3-Step Onboarding
            </button>
            <button
              onClick={() => onSelectScreen('dashboard')}
              className={`px-2.5 py-1 rounded text-[11px] font-medium transition-all ${
                currentScreen === 'dashboard'
                  ? 'bg-[#2DE2B5] text-[#061A13] font-semibold shadow-sm'
                  : 'text-[#BAC8BF] hover:text-[#F7F3EB]'
              }`}
            >
              Full Radar Dashboard
            </button>
          </div>
        </div>

        {/* Right: Viewport + Theme + Auth States + Design System */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          
          {/* Auth State Switcher (when on login screen) */}
          {currentScreen === 'login' && (
            <div className="hidden lg:flex items-center gap-1 bg-[#0E1F17] px-1 py-0.5 rounded-lg border border-[#203E30]">
              <span className="text-[10px] font-mono text-[#7E9387] px-1">STATE:</span>
              {(['default', 'focused', 'error', 'loading', 'otp', 'signup'] as AuthState[]).map(st => (
                <button
                  key={st}
                  onClick={() => onSelectAuthState(st)}
                  className={`px-2 py-0.5 rounded text-[10px] font-mono capitalize transition-all ${
                    currentAuthState === st
                      ? 'bg-[#162E23] text-[#2DE2B5] border border-[#2DE2B5]/40 font-bold'
                      : 'text-[#7E9387] hover:text-[#BAC8BF]'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          )}

          {/* Viewport switch (Desktop 1440 vs Mobile 390 vs Responsive) */}
          <div className="flex items-center gap-1 bg-[#0E1F17] p-0.5 rounded-lg border border-[#203E30]">
            <button
              title="Responsive Viewport"
              onClick={() => onSelectViewport('responsive')}
              className={`p-1.5 rounded transition-all ${
                currentViewport === 'responsive'
                  ? 'bg-[#2DE2B5]/20 text-[#2DE2B5] border border-[#2DE2B5]/40'
                  : 'text-[#7E9387] hover:text-[#BAC8BF]'
              }`}
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
            <button
              title="Desktop 1440x900 Frame"
              onClick={() => onSelectViewport('desktop-1440')}
              className={`p-1.5 rounded transition-all ${
                currentViewport === 'desktop-1440'
                  ? 'bg-[#2DE2B5]/20 text-[#2DE2B5] border border-[#2DE2B5]/40'
                  : 'text-[#7E9387] hover:text-[#BAC8BF]'
              }`}
            >
              <Monitor className="w-3.5 h-3.5" />
            </button>
            <button
              title="Mobile 390x844 Frame"
              onClick={() => onSelectViewport('mobile-390')}
              className={`p-1.5 rounded transition-all ${
                currentViewport === 'mobile-390'
                  ? 'bg-[#2DE2B5]/20 text-[#2DE2B5] border border-[#2DE2B5]/40'
                  : 'text-[#7E9387] hover:text-[#BAC8BF]'
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Theme Selector */}
          <div className="flex items-center gap-1 bg-[#0E1F17] p-0.5 rounded-lg border border-[#203E30]">
            <button
              title="Forest Green & Sand Beige (Primary Theme)"
              onClick={() => onSelectTheme('forest-sand')}
              className={`px-2 py-1 rounded text-[11px] font-medium flex items-center gap-1 transition-all ${
                currentTheme === 'forest-sand'
                  ? 'bg-[#1D5C43] text-[#F7F3EB] font-bold shadow-sm'
                  : 'text-[#BAC8BF] hover:text-[#F7F3EB]'
              }`}
            >
              <span>🌲 Forest &amp; Sand</span>
            </button>
            <button
              title="Sand Beige Light Theme Variant"
              onClick={() => onSelectTheme('sand-light')}
              className={`px-2 py-1 rounded text-[11px] font-medium flex items-center gap-1 transition-all ${
                currentTheme === 'sand-light'
                  ? 'bg-[#EEDBCA] text-[#0F251C] font-bold shadow-sm'
                  : 'text-[#BAC8BF] hover:text-[#F7F3EB]'
              }`}
            >
              <span>🏜️ Sand Light</span>
            </button>
            <button
              title="Dark Radar Obsidian Variant"
              onClick={() => onSelectTheme('dark-radar')}
              className={`px-2 py-1 rounded text-[11px] font-medium flex items-center gap-1 transition-all ${
                currentTheme === 'dark-radar'
                  ? 'bg-[#1A2230] text-[#2DE2B5] font-bold shadow-sm'
                  : 'text-[#BAC8BF] hover:text-[#F7F3EB]'
              }`}
            >
              <span>🌌 Radar Dark</span>
            </button>
          </div>

          {/* Design System Spec Button */}
          <button
            onClick={onToggleDesignSystem}
            className="px-2.5 py-1 rounded-lg bg-[#2DE2B5]/15 border border-[#2DE2B5]/40 text-[#2DE2B5] font-semibold text-[11px] hover:bg-[#2DE2B5]/25 flex items-center gap-1 transition-all"
          >
            <Layers className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Design System</span>
          </button>
        </div>
      </div>
    </aside>
  )
}
