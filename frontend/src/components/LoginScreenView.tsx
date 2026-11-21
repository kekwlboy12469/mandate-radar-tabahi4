import React from 'react'
import { AuthCard, type AuthState } from './AuthCard'
import { RadarHeroPanel } from './RadarHeroPanel'

interface LoginScreenViewProps {
  authState?: AuthState
  onSuccess: () => void
  onTrySampleData: () => void
  onOpenDesignSystem?: () => void
}

export const LoginScreenView: React.FC<LoginScreenViewProps> = ({
  authState = 'default',
  onSuccess,
  onTrySampleData,
  onOpenDesignSystem
}) => {
  return (
    <div className="w-full min-h-screen flex flex-col lg:flex-row items-stretch justify-center bg-[var(--bg-primary)]">
      
      {/* Mobile Top Header Strip (Radar Hero Compact on Mobile) */}
      <div className="block lg:hidden w-full border-b border-[#203E30] bg-[#07120D]">
        <RadarHeroPanel compact onExploreMandate={() => onTrySampleData()} />
      </div>

      {/* Left 45% (Desktop) / Main Form (Mobile) */}
      <div className="w-full lg:w-[45%] flex items-center justify-center border-r border-[#203E30]/60 bg-[var(--bg-primary)] py-8 px-4 sm:px-8">
        <AuthCard
          initialState={authState}
          onSuccess={onSuccess}
          onTrySampleData={onTrySampleData}
          onOpenDesignSystem={onOpenDesignSystem}
        />
      </div>

      {/* Right 55% (Desktop Hero Panel with Dark Radar Grid & Floating Glass Cards) */}
      <div className="hidden lg:flex lg:w-[55%] relative items-center justify-center bg-[#07120D]">
        <RadarHeroPanel onExploreMandate={() => onTrySampleData()} />
      </div>
    </div>
  )
}
