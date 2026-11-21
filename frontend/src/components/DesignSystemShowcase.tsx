import React, { useState } from 'react'
import {
  X,
  Check,
  AlertTriangle,
  Flame,
  ShieldCheck,
  TrendingUp,
  CreditCard,
  Building2,
  Copy,
  ExternalLink,
  Search,
  Bell,
  Sparkles,
  Layers,
  ArrowRight
} from 'lucide-react'

interface DesignSystemShowcaseProps {
  onClose?: () => void
}

export const DesignSystemShowcase: React.FC<DesignSystemShowcaseProps> = ({ onClose }) => {
  const [copiedToken, setCopiedToken] = useState<string | null>(null)
  const [toastVisible, setToastVisible] = useState(true)
  const [testInput, setTestInput] = useState('')

  const copyToClipboard = (text: string, token: string) => {
    navigator.clipboard.writeText(text)
    setCopiedToken(token)
    setTimeout(() => setCopiedToken(null), 1800)
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md p-4 sm:p-8 flex justify-center animate-fade-in text-left">
      <div className="w-full max-w-5xl bg-[#0E1F17] border border-[#203E30] rounded-2xl p-6 sm:p-10 text-[#F7F3EB] shadow-2xl relative my-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-6 border-b border-[#203E30]">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs uppercase px-2 py-0.5 rounded bg-[#2DE2B5]/15 text-[#2DE2B5] border border-[#2DE2B5]/30">
                Design System Specification
              </span>
              <span className="font-mono text-xs text-[#BAC8BF]">v2.4 · Linear/Stripe Level</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mt-1 text-[#F7F3EB]">
              Mandate Radar Design System
            </h1>
            <p className="text-xs sm:text-sm text-[#BAC8BF] mt-1">
              Color tokens, typography scale, 8px grid components, motion rules &amp; rail badges for Indian fintech mandates.
            </p>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              className="w-9 h-9 rounded-full bg-[#162E23] border border-[#203E30] flex items-center justify-center hover:bg-[#203E30] transition-colors"
            >
              <X className="w-5 h-5 text-[#BAC8BF]" />
            </button>
          )}
        </div>

        {/* Content Sections */}
        <div className="mt-8 space-y-12">
          
          {/* 1. COLOR THEME PALETTE */}
          <section>
            <h2 className="text-lg font-bold tracking-tight text-[#F7F3EB] mb-4 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2DE2B5]" />
              Color Palette: Sand Beige &amp; Forest Green (Dark Primary + Light Variant)
            </h2>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
              {/* Forest Deep */}
              <div
                onClick={() => copyToClipboard('#07120D', 'forest-bg')}
                className="p-3 rounded-xl border border-[#203E30] bg-[#07120D] cursor-pointer hover:border-[#2DE2B5] transition-all"
              >
                <div className="h-10 rounded-lg bg-[#07120D] border border-white/10 mb-2" />
                <div className="text-xs font-semibold">Background</div>
                <div className="text-[10px] font-mono text-[#BAC8BF]">#07120D / #0B0F14</div>
              </div>

              {/* Surface */}
              <div
                onClick={() => copyToClipboard('#0E1F17', 'surface')}
                className="p-3 rounded-xl border border-[#203E30] bg-[#0E1F17] cursor-pointer hover:border-[#2DE2B5] transition-all"
              >
                <div className="h-10 rounded-lg bg-[#0E1F17] border border-white/10 mb-2" />
                <div className="text-xs font-semibold">Surface</div>
                <div className="text-[10px] font-mono text-[#BAC8BF]">#0E1F17 / #121821</div>
              </div>

              {/* Elevated Surface */}
              <div
                onClick={() => copyToClipboard('#162E23', 'elevated')}
                className="p-3 rounded-xl border border-[#203E30] bg-[#162E23] cursor-pointer hover:border-[#2DE2B5] transition-all"
              >
                <div className="h-10 rounded-lg bg-[#162E23] border border-white/10 mb-2" />
                <div className="text-xs font-semibold">Elevated Surface</div>
                <div className="text-[10px] font-mono text-[#BAC8BF]">#162E23 / #1A2230</div>
              </div>

              {/* Sand Beige Primary */}
              <div
                onClick={() => copyToClipboard('#EEDBCA', 'sand-primary')}
                className="p-3 rounded-xl border border-[#203E30] bg-[#162E23] cursor-pointer hover:border-[#2DE2B5] transition-all"
              >
                <div className="h-10 rounded-lg bg-[#EEDBCA] mb-2" />
                <div className="text-xs font-semibold text-[#EEDBCA]">Sand Beige</div>
                <div className="text-[10px] font-mono text-[#BAC8BF]">#EEDBCA / #F7F3EB</div>
              </div>

              {/* Radar Teal-Green Brand */}
              <div
                onClick={() => copyToClipboard('#2DE2B5', 'radar-teal')}
                className="p-3 rounded-xl border border-[#203E30] bg-[#162E23] cursor-pointer hover:border-[#2DE2B5] transition-all"
              >
                <div className="h-10 rounded-lg bg-[#2DE2B5] mb-2 shadow-[0_0_12px_rgba(45,226,181,0.4)]" />
                <div className="text-xs font-semibold text-[#2DE2B5]">Brand Accent</div>
                <div className="text-[10px] font-mono text-[#BAC8BF]">#2DE2B5 (Radar Teal)</div>
              </div>

              {/* Border Tone */}
              <div
                onClick={() => copyToClipboard('#203E30', 'border-tone')}
                className="p-3 rounded-xl border border-[#203E30] bg-[#162E23] cursor-pointer hover:border-[#2DE2B5] transition-all"
              >
                <div className="h-10 rounded-lg bg-[#203E30] mb-2" />
                <div className="text-xs font-semibold">Border Tone</div>
                <div className="text-[10px] font-mono text-[#BAC8BF]">#203E30 / #242E3D</div>
              </div>
            </div>

            {/* Alert & Graph Palette */}
            <div className="mt-4 pt-4 border-t border-[#203E30]/60">
              <div className="text-xs font-mono uppercase text-[#BAC8BF] mb-3">Alerts &amp; Graph Entities</div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl border border-[#FFB547]/30 bg-[#FFB547]/10">
                  <div className="h-3 w-8 rounded-full bg-[#FFB547] mb-2" />
                  <div className="text-xs font-bold text-[#FFB547]">Silent Price Hike</div>
                  <div className="text-[10px] font-mono text-[#BAC8BF]">#FFB547 (Amber)</div>
                </div>

                <div className="p-3 rounded-xl border border-[#8B7CFF]/30 bg-[#8B7CFF]/10">
                  <div className="h-3 w-8 rounded-full bg-[#8B7CFF] mb-2" />
                  <div className="text-xs font-bold text-[#8B7CFF]">Trial Trap / Parent Node</div>
                  <div className="text-[10px] font-mono text-[#BAC8BF]">#8B7CFF (Violet)</div>
                </div>

                <div className="p-3 rounded-xl border border-[#FF5C6C]/30 bg-[#FF5C6C]/10">
                  <div className="h-3 w-8 rounded-full bg-[#FF5C6C] mb-2" />
                  <div className="text-xs font-bold text-[#FF5C6C]">Zombie Charge</div>
                  <div className="text-[10px] font-mono text-[#BAC8BF]">#FF5C6C (Red)</div>
                </div>

                <div className="p-3 rounded-xl border border-[#3DDC97]/30 bg-[#3DDC97]/10">
                  <div className="h-3 w-8 rounded-full bg-[#3DDC97] mb-2" />
                  <div className="text-xs font-bold text-[#3DDC97]">Verified / Safe</div>
                  <div className="text-[10px] font-mono text-[#BAC8BF]">#3DDC97 (Green)</div>
                </div>
              </div>
            </div>
          </section>

          {/* 2. TYPOGRAPHY SCALE */}
          <section>
            <h2 className="text-lg font-bold tracking-tight text-[#F7F3EB] mb-4 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#8B7CFF]" />
              Typography Scale (Inter for UI, JetBrains Mono for ₹ amounts &amp; Cypher)
            </h2>

            <div className="bg-[#07120D] border border-[#203E30] rounded-xl p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between border-b border-[#203E30]/60 pb-3">
                <span className="font-mono text-xs text-[#BAC8BF]">Scale 40 (Hero Number)</span>
                <span className="font-mono text-4xl font-extrabold text-[#F7F3EB] tabular-nums">
                  ₹65,623<small className="text-base text-[#BAC8BF] ml-2">/ year committed</small>
                </span>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between border-b border-[#203E30]/60 pb-3">
                <span className="font-mono text-xs text-[#BAC8BF]">Scale 28 (Section Title)</span>
                <span className="text-2xl font-bold text-[#F7F3EB] font-sans">
                  Find every auto-debit. Cancel the ones you don't need.
                </span>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between border-b border-[#203E30]/60 pb-3">
                <span className="font-mono text-xs text-[#BAC8BF]">Scale 20 (Card Header)</span>
                <span className="text-xl font-semibold text-[#F7F3EB] font-sans">
                  Active Recurring Mandates (10 Detected)
                </span>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between border-b border-[#203E30]/60 pb-3">
                <span className="font-mono text-xs text-[#BAC8BF]">Scale 16 (Body Text)</span>
                <span className="text-base text-[#BAC8BF] font-sans">
                  Upload a bank statement. We map every recurring charge to the right cancellation route.
                </span>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between border-b border-[#203E30]/60 pb-3">
                <span className="font-mono text-xs text-[#BAC8BF]">Scale 14 (UI Controls)</span>
                <span className="text-sm font-medium text-[#F7F3EB]">
                  Continue with Google · Try with sample data · Choose your bank
                </span>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-baseline justify-between">
                <span className="font-mono text-xs text-[#BAC8BF]">Scale 12 (Mono Descriptors &amp; Cypher)</span>
                <span className="font-mono text-xs text-[#2DE2B5]">
                  MATCH (m:Merchant &#123;name: 'Spotify'&#125;)-[:VIA_RAIL]-&gt;(r:Rail) RETURN m, r
                </span>
              </div>
            </div>
          </section>

          {/* 3. BUTTONS & INPUT COMPONENTS */}
          <section>
            <h2 className="text-lg font-bold tracking-tight text-[#F7F3EB] mb-4 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#4DA3FF]" />
              Buttons &amp; Input Fields (8px Grid, 12px Card Radii, 8px Buttons)
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              {/* Buttons */}
              <div className="p-5 rounded-xl border border-[#203E30] bg-[#07120D] space-y-3">
                <div className="text-xs font-mono uppercase text-[#BAC8BF]">Button Hierarchy</div>
                <button className="w-full h-10 btn-primary text-xs font-semibold">
                  Primary Button (Accent)
                </button>
                <button className="w-full h-10 btn-secondary text-xs font-medium">
                  Secondary Surface Button
                </button>
                <button className="w-full h-10 btn-ghost text-xs">
                  Ghost / Outline Button
                </button>
              </div>

              {/* Input States */}
              <div className="p-5 rounded-xl border border-[#203E30] bg-[#07120D] space-y-3 sm:col-span-2">
                <div className="text-xs font-mono uppercase text-[#BAC8BF]">Input Focus &amp; Error Rings</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] text-[#BAC8BF] mb-1">Focus state (with accent glow)</label>
                    <input
                      type="text"
                      defaultValue="you@example.com"
                      className="w-full px-3 py-2 text-xs fintech-input border-[#2DE2B5] ring-2 ring-[#2DE2B5]/30"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-[#BAC8BF] mb-1">Error state (with red ring)</label>
                    <input
                      type="password"
                      defaultValue="wrong_password"
                      className="w-full px-3 py-2 text-xs fintech-input border-[#FF5C6C] ring-2 ring-[#FF5C6C]/30 text-[#FF5C6C]"
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 4. STATUS CHIPS & RAIL BADGES */}
          <section>
            <h2 className="text-lg font-bold tracking-tight text-[#F7F3EB] mb-4 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#FFB547]" />
              Status Chips &amp; Payment Rail Badges
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {/* Status Chips */}
              <div className="p-5 rounded-xl border border-[#203E30] bg-[#07120D] space-y-3">
                <div className="text-xs font-mono uppercase text-[#BAC8BF]">Risk Status Chips</div>
                <div className="flex flex-wrap gap-2">
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold chip-hike flex items-center gap-1">
                    <TrendingUp className="w-3.5 h-3.5" />
                    Price Hike (+12%)
                  </span>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold chip-trial flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Trial Trap
                  </span>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold chip-zombie flex items-center gap-1">
                    <Flame className="w-3.5 h-3.5" />
                    Zombie Charge
                  </span>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold chip-emi">
                    EMI (6/12)
                  </span>
                  <span className="px-2.5 py-1 rounded-full text-xs font-semibold chip-safe flex items-center gap-1">
                    <Check className="w-3.5 h-3.5" />
                    Verified Safe
                  </span>
                </div>
              </div>

              {/* Payment Rail Badges */}
              <div className="p-5 rounded-xl border border-[#203E30] bg-[#07120D] space-y-3">
                <div className="text-xs font-mono uppercase text-[#BAC8BF]">Payment Rails (Indian Fintech)</div>
                <div className="flex flex-wrap gap-2">
                  <span className="badge-rail bg-[#4DA3FF]/15 text-[#4DA3FF] border border-[#4DA3FF]/30">
                    CARD_SI
                  </span>
                  <span className="badge-rail bg-[#3DDC97]/15 text-[#3DDC97] border border-[#3DDC97]/30">
                    UPI_AUTOPAY
                  </span>
                  <span className="badge-rail bg-[#FFB547]/15 text-[#FFB547] border border-[#FFB547]/30">
                    PLAY_STORE
                  </span>
                  <span className="badge-rail bg-[#8B7CFF]/15 text-[#8B7CFF] border border-[#8B7CFF]/30">
                    APP_STORE
                  </span>
                  <span className="badge-rail bg-[#FF7EB6]/15 text-[#FF7EB6] border border-[#FF7EB6]/30">
                    NACH
                  </span>
                  <span className="badge-rail bg-[#2DE2B5]/15 text-[#2DE2B5] border border-[#2DE2B5]/30">
                    WALLET
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* 5. MERCHANT AVATARS & STAT CARDS */}
          <section>
            <h2 className="text-lg font-bold tracking-tight text-[#F7F3EB] mb-4 flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#3DDC97]" />
              Merchant Avatars, Table Rows &amp; Interactive Toast
            </h2>

            <div className="p-5 rounded-xl border border-[#203E30] bg-[#07120D] space-y-4">
              <div className="text-xs font-mono uppercase text-[#BAC8BF]">Merchant Table Row Preview</div>
              <div className="border border-[#203E30] rounded-xl overflow-hidden divide-y divide-[#203E30]">
                {/* Netflix Row */}
                <div className="p-3.5 flex items-center justify-between hover:bg-[#162E23]/60 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-red-500/15 text-red-400 border border-red-500/30 flex items-center justify-center font-bold text-xs">
                      N
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-[#F7F3EB]">Netflix Standard</div>
                      <div className="text-[11px] font-mono text-[#BAC8BF]">NETFLIX-MUM-SI-49102</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="badge-rail bg-[#4DA3FF]/15 text-[#4DA3FF] border border-[#4DA3FF]/30">
                      CARD_SI
                    </span>
                    <span className="chip-zombie px-2 py-0.5 rounded-full text-[10px] font-semibold">
                      Zombie (90d inactive)
                    </span>
                    <div className="font-mono text-sm font-bold text-[#F7F3EB] tabular-nums">
                      ₹7,788<span className="text-[10px] text-[#BAC8BF]">/yr</span>
                    </div>
                  </div>
                </div>

                {/* Spotify Row */}
                <div className="p-3.5 flex items-center justify-between hover:bg-[#162E23]/60 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 flex items-center justify-center font-bold text-xs">
                      ♫
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-[#F7F3EB]">Spotify Premium Individual</div>
                      <div className="text-[11px] font-mono text-[#BAC8BF]">UPI/P2M/23849182/SPOTIFY</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="badge-rail bg-[#3DDC97]/15 text-[#3DDC97] border border-[#3DDC97]/30">
                      UPI_AUTOPAY
                    </span>
                    <span className="chip-hike px-2 py-0.5 rounded-full text-[10px] font-semibold">
                      +12% Price Creep
                    </span>
                    <div className="font-mono text-sm font-bold text-[#F7F3EB] tabular-nums">
                      ₹1,199<span className="text-[10px] text-[#BAC8BF]">/yr</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Toast component */}
              {toastVisible && (
                <div className="mt-4 p-3 rounded-lg border border-[#3DDC97]/40 bg-[#3DDC97]/10 flex items-center justify-between text-xs text-[#3DDC97]">
                  <div className="flex items-center gap-2">
                    <Check className="w-4 h-4 text-[#3DDC97]" />
                    <span>Design token verified: Indian currency formatting is applied (₹65,623).</span>
                  </div>
                  <button onClick={() => setToastVisible(false)} className="hover:opacity-75">
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>
          </section>

        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-[#203E30] flex items-center justify-between text-xs text-[#BAC8BF]">
          <span>Design System Spec for Mandate Radar · Built with Sand Beige &amp; Forest Green</span>
          {onClose && (
            <button onClick={onClose} className="btn-primary text-xs px-4 py-2">
              Done Viewing
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
