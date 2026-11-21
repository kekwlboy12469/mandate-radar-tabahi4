import React, { useState } from 'react'
import {
  Lock,
  ArrowRight,
  ShieldCheck,
  Sparkles,
  Zap,
  ChevronDown,
  X,
  CreditCard,
  Building2,
  TrendingUp,
  AlertTriangle,
  Flame,
  CheckCircle2,
  Search,
  ExternalLink,
  ChevronRight,
  Upload,
  Leaf,
  Sliders,
  HelpCircle,
  Check,
  Shield,
  FileText
} from 'lucide-react'
import { RadarHeroPanel } from './RadarHeroPanel'

interface MoneliqLandingPageProps {
  onOpenAuth: (mode: 'signin' | 'signup') => void
  onLaunchDashboard: () => void
  onOpenDesignSystem: () => void
}

export const MoneliqLandingPage: React.FC<MoneliqLandingPageProps> = ({
  onOpenAuth,
  onLaunchDashboard,
  onOpenDesignSystem
}) => {
  const [activeNavPill, setActiveNavPill] = useState('Overview')

  // Interactive Calculator State for landing page
  const [calculatorMandates, setCalculatorMandates] = useState(10)
  const calculatedTotal = Math.round(calculatorMandates * 6562)
  const calculatedSavings = Math.round(calculatorMandates * 3117)
  const calculatedZombies = Math.max(1, Math.round(calculatorMandates * 0.3))

  // FAQ Accordion State
  const [expandedFaq, setExpandedFaq] = useState<number | null>(0)

  const faqs = [
    {
      q: 'Can banks or merchants legally refuse my mandate cancellation?',
      a: 'No. Under the Reserve Bank of India Master Direction on Recurring Transactions (RBI/2019-20/53), bank account holders and cardholders have the absolute statutory right to revoke consent for any recurring transaction standing instruction at any time without requiring merchant approval.'
    },
    {
      q: 'How does Mandate Radar connect cryptic billing strings to real parent companies?',
      a: 'We leverage a local Neo4j knowledge graph topology. Cryptic transaction descriptors from aggregators (like BILLDESK*NETFLIX or NOVI DIGITAL) are traversed across payment rails and mapped directly to parent conglomerate trees (like Netflix Inc, The Walt Disney Co, or Alphabet Inc).'
    },
    {
      q: 'Is my bank statement uploaded to any cloud server or database?',
      a: 'Never. Mandate Radar executes 100% client-side in your local browser sandbox via WebAssembly. Neither your account number, bank balances, nor raw statement transactions are ever transmitted or stored outside your machine.'
    },
    {
      q: 'What types of Indian auto-debit rails are supported?',
      a: 'Mandate Radar natively parses and classifies UPI Autopay (NPCI framework), Card Standing Instructions on Visa/Mastercard/RuPay, NACH & e-NACH mandates, In-App Store billing (Google Play and Apple App Store), and NetBanking recurring standing instructions.'
    }
  ]

  return (
    <div className="min-h-screen bg-[#F8F5EE] text-[#0F1713] antialiased flex flex-col font-sans selection:bg-[#C6F6D5] selection:text-[#0B2417]">
      
      {/* ========================================================
          1. TOP NAVBAR (Fernwood Theme: Sand Beige & Forest Green)
      ======================================================== */}
      <header className="w-full bg-[#F8F5EE] px-6 sm:px-12 py-5 flex items-center justify-between relative z-50">
        
        {/* Left: Fernwood Brand Logo with Leaf Pulse */}
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>
          <div className="w-8 h-8 rounded-full bg-[#0E2419] text-[#EFE8DC] flex items-center justify-center shadow-md border border-[#0E2419]/20">
            <Leaf className="w-4 h-4 text-[#2DE2B5]" />
          </div>
          <span className="font-extrabold text-xl tracking-tight text-[#0F1713]">
            Mandate Radar
          </span>
        </div>

        {/* Center: Frosted Glass Pill Navigation Bar */}
        <nav className="hidden md:flex items-center gap-1.5 p-1.5 rounded-full bg-[#0E2419]/8 border border-[#0E2419]/10 backdrop-blur-md shadow-sm">
          {['Overview', 'How It Works', 'Calculator', 'Rails', 'Live Radar', 'RBI Rules'].map((item) => (
            <button
              key={item}
              onClick={() => {
                setActiveNavPill(item)
                const id = item === 'Live Radar' ? 'live-radar' : item.toLowerCase().replace(/\s+/g, '-')
                const el = document.getElementById(id)
                if (el) el.scrollIntoView({ behavior: 'smooth' })
              }}
              className={`px-4 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                activeNavPill === item
                  ? 'bg-[#0E2419] text-[#EFE8DC] font-semibold shadow-sm'
                  : 'text-[#0F1713]/80 hover:text-[#0F1713] hover:bg-black/5'
              }`}
            >
              {item}
            </button>
          ))}
        </nav>

        {/* Right: Log in + Start Radar Pills */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onOpenAuth('signin')}
            className="pill-black text-xs sm:text-sm cursor-pointer"
          >
            Log in
          </button>
          
          <button
            onClick={() => onOpenAuth('signup')}
            className="pill-mint text-xs sm:text-sm cursor-pointer font-bold"
          >
            Start Radar
          </button>
        </div>
      </header>

      {/* ========================================================
          2. HERO SECTION (Fernwood Organic Forest & Misty Sand)
      ======================================================== */}
      <main className="flex-1 px-4 sm:px-8 pb-16 space-y-20">
        
        <div className="relative w-full rounded-[38px] sm:rounded-[56px] bg-[#0E2419] bg-stipple-forest border border-[#EEDBCA]/20 overflow-hidden px-6 sm:px-12 pt-14 sm:pt-20 pb-28 shadow-2xl flex flex-col items-center justify-center text-center">
          
          {/* Ambient Botanical Radial Glow */}
          <div
            className="absolute -top-24 left-1/2 -translate-x-1/2 w-[700px] h-[350px] rounded-full pointer-events-none opacity-30"
            style={{
              background: 'radial-gradient(circle, rgba(45, 226, 181, 0.45) 0%, rgba(20, 52, 36, 0.25) 50%, transparent 80%)',
              filter: 'blur(60px)'
            }}
          />

          {/* Sub-Navigation Breadcrumb Dots (Fernwood Replica) */}
          <div className="relative z-20 flex items-center justify-center gap-4 sm:gap-6 text-xs sm:text-sm text-[#EFE8DC]/85 font-medium mb-6 animate-fade-in">
            <span className="flex items-center gap-1.5 hover:text-white transition-colors cursor-pointer" onClick={onLaunchDashboard}>
              <span className="w-1.5 h-1.5 rounded-full bg-[#2DE2B5]" />
              <span>Monthly scans</span>
            </span>
            <span className="flex items-center gap-1.5 hover:text-white transition-colors cursor-pointer" onClick={onLaunchDashboard}>
              <span className="w-1.5 h-1.5 rounded-full bg-[#EFE8DC]/60" />
              <span>RBI care guides</span>
            </span>
            <span className="flex items-center gap-1.5 hover:text-white transition-colors cursor-pointer" onClick={onLaunchDashboard}>
              <span className="w-1.5 h-1.5 rounded-full bg-[#EFE8DC]/60" />
              <span>Mandate doctor</span>
            </span>
          </div>

          {/* Kinetic Typography Headline (Matching Fernwood Scale & Tone) */}
          <div className="relative z-20 max-w-4xl mx-auto space-y-4">
            <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-[#F5EEDB] tracking-tight leading-[1.08]">
              Grow your savings, <br />
              <span className="text-[#F5EEDB]">one mandate at a time.</span>
            </h1>

            <p className="max-w-xl mx-auto text-sm sm:text-base text-[#EFE8DC]/80 font-normal leading-relaxed pt-2">
              Potted, labeled and almost impossible to cancel. On your radar before the first of every month.
            </p>

            <div className="pt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
              <button
                onClick={() => onOpenAuth('signup')}
                className="pill-fernwood-sand flex items-center justify-center gap-2 cursor-pointer group shadow-lg"
              >
                <span>Start my radar</span>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </button>

              <button
                onClick={onLaunchDashboard}
                className="pill-fernwood-green flex items-center justify-center gap-2 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#2DE2B5]" />
                <span>Explore sample data (₹65,623)</span>
              </button>
            </div>
          </div>

          {/* Floating Merchant Telemetry Badges (Fernwood Accent Pills) */}
          
          {/* Spotify Badge */}
          <div className="absolute left-6 sm:left-16 top-24 pointer-events-auto hidden md:block animate-float-1 z-20">
            <div
              className="p-3.5 rounded-2xl bg-[#143323]/90 border border-[#FFB547]/35 backdrop-blur-md shadow-2xl flex items-center gap-3 hover:scale-105 transition-transform cursor-pointer"
              onClick={onLaunchDashboard}
            >
              <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/35 flex items-center justify-center font-bold text-base">
                ♫
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-[#F5EEDB]">Spotify Premium</div>
                <div className="text-[10px] font-mono text-[#FFB547]">+12% Price Creep</div>
              </div>
            </div>
          </div>

          {/* Netflix Standard Badge */}
          <div className="absolute left-8 sm:left-20 bottom-36 pointer-events-auto hidden md:block animate-float-2 z-20">
            <div
              className="p-3.5 rounded-2xl bg-[#143323]/90 border border-[#FF5C6C]/35 backdrop-blur-md shadow-2xl flex items-center gap-3 hover:scale-105 transition-transform cursor-pointer"
              onClick={onLaunchDashboard}
            >
              <div className="w-9 h-9 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/35 flex items-center justify-center font-bold text-base">
                N
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-[#F5EEDB]">Netflix Standard</div>
                <div className="text-[10px] font-mono text-[#FF5C6C]">Zombie (90d Inactive)</div>
              </div>
            </div>
          </div>

          {/* YouTube Premium Badge */}
          <div className="absolute right-6 sm:right-16 top-24 pointer-events-auto hidden md:block animate-float-3 z-20">
            <div
              className="p-3.5 rounded-2xl bg-[#143323]/90 border border-[#2DE2B5]/35 backdrop-blur-md shadow-2xl flex items-center gap-3 hover:scale-105 transition-transform cursor-pointer"
              onClick={onLaunchDashboard}
            >
              <div className="w-9 h-9 rounded-xl bg-red-500/20 text-red-400 border border-red-500/35 flex items-center justify-center font-bold text-base">
                ▶
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-[#F5EEDB]">YouTube Premium</div>
                <div className="text-[10px] font-mono text-[#3DDC97]">Verified Safe · Active</div>
              </div>
            </div>
          </div>

          {/* Disney+ Hotstar Badge */}
          <div className="absolute right-8 sm:right-20 bottom-36 pointer-events-auto hidden md:block animate-float-1 z-20">
            <div
              className="p-3.5 rounded-2xl bg-[#143323]/90 border border-[#8B7CFF]/35 backdrop-blur-md shadow-2xl flex items-center gap-3 hover:scale-105 transition-transform cursor-pointer"
              onClick={onLaunchDashboard}
            >
              <div className="w-9 h-9 rounded-xl bg-indigo-500/20 text-indigo-400 border border-indigo-500/35 flex items-center justify-center font-bold text-xs font-mono">
                D+
              </div>
              <div className="text-left">
                <div className="text-xs font-semibold text-[#F5EEDB]">Disney+ Hotstar</div>
                <div className="text-[10px] font-mono text-[#8B7CFF]">Trial Auto-Converted</div>
              </div>
            </div>
          </div>

          {/* Ethereal Sand Beige Mist / Fog Gradient Rising from Bottom */}
          <div
            className="absolute bottom-0 inset-x-0 h-64 sm:h-80 pointer-events-none z-10 animate-mist"
            style={{
              background: 'linear-gradient(to top, #F8F5EE 0%, rgba(248, 245, 238, 0.96) 24%, rgba(248, 245, 238, 0.6) 48%, rgba(14, 36, 25, 0.2) 78%, transparent 100%)'
            }}
          />

          {/* Embedded Live Dashboard Card Resting Inside the Misty Horizon */}
          <div className="mt-16 sm:mt-24 w-full max-w-3xl relative z-20">
            <div
              onClick={onLaunchDashboard}
              className="p-6 sm:p-8 rounded-3xl bg-[#091510]/95 border border-[#2DE2B5]/30 shadow-2xl backdrop-blur-xl hover:border-[#2DE2B5] transition-all cursor-pointer group text-left"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-7 rounded-md bg-[#EEDBCA] border border-[#D5C2AF] flex items-center justify-center text-[9px] font-mono font-bold text-[#0B2417] shadow-sm">
                    HDFC
                  </div>
                  <div>
                    <div className="text-xs font-semibold text-white flex items-center gap-2">
                      <span>MANDATE RADAR</span>
                      <span className="w-1.5 h-1.5 rounded-full bg-[#2DE2B5] animate-ping" />
                      <span className="text-[10px] font-mono text-[#EEDBCA]/80">•••• 4821</span>
                    </div>
                    <div className="text-[11px] text-[#BAC8BF]">10 Active Auto-Debits Linked · Primary Account</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 font-mono text-xs text-[#2DE2B5]">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Click to Open Full Command Center</span>
                </div>
              </div>

              <div className="pt-6 grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-[#BAC8BF]">
                    Total Committed Exposure
                  </div>
                  <div className="text-3xl sm:text-4xl font-extrabold text-white font-mono mt-1 tracking-tight">
                    ₹65,623
                    <span className="text-xs font-normal text-[#BAC8BF] ml-1.5">/ year</span>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[#BAC8BF]">Zombies &amp; Creeps</span>
                    <span className="font-mono text-[#FF5C6C] font-semibold">3 Flagged</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                    <div className="w-[45%] h-full bg-gradient-to-r from-[#2DE2B5] to-[#FF5C6C] rounded-full" />
                  </div>
                  <div className="text-[10px] text-[#EEDBCA]/80">Potential savings: ₹31,176 / yr</div>
                </div>

                <div className="flex items-center justify-end">
                  <div className="relative w-14 h-14 rounded-full border border-[#2DE2B5]/60 bg-[#0E1F17] flex items-center justify-center overflow-hidden shadow-[0_0_20px_rgba(45,226,181,0.25)]">
                    <div
                      className="w-full h-full animate-radar-sweep"
                      style={{
                        background: 'conic-gradient(from 0deg, transparent 65%, rgba(45, 226, 181, 0.4) 90%, #2DE2B5 100%)'
                      }}
                    />
                    <div className="w-2 h-2 rounded-full bg-[#2DE2B5] z-10" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ========================================================
            SUBSECTION 1: THE 3 VALUE PILLARS
        ======================================================== */}
        <section id="overview" className="max-w-6xl mx-auto">
          <div className="text-center space-y-2 mb-10">
            <span className="text-xs font-mono uppercase tracking-wider text-[#64756B] bg-[#E8E1D2]/60 px-3 py-1 rounded-full font-semibold">
              EFFICIENCY AT ITS BEST
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0F1713] tracking-tight">
              Designed for the Indian Banking Mandate Maze
            </h2>
            <p className="text-xs sm:text-sm text-[#64756B] max-w-xl mx-auto">
              UPI Autopay, Card Standing Instructions, and NACH e-Mandates conceal the real company behind aggregator memo strings.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Card 1 */}
            <div
              onClick={onLaunchDashboard}
              className="sand-card p-6 sm:p-8 flex flex-col justify-between space-y-6 cursor-pointer"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[#C6F6D5] flex items-center justify-center text-[#0B2417] shadow-sm">
                  <Search className="w-5 h-5 text-[#0B2417]" />
                </div>
                <h3 className="text-lg font-bold text-[#0F1713]">
                  Descriptor Graph Resolver
                </h3>
                <p className="text-xs text-[#64756B] leading-relaxed">
                  Connects cryptic memo strings like <span className="font-mono text-[#0F1713] font-bold">NOVI DIGITAL</span> to Disney+ Hotstar, Spotify AB, and Alphabet Inc using our local graph dictionary.
                </p>
              </div>

              <div className="pt-4 border-t border-[#E8E1D2] flex items-center justify-between text-xs font-semibold text-[#0B2417]">
                <span>Explore graph connections</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>

            {/* Card 2 */}
            <div
              onClick={onLaunchDashboard}
              className="sand-card p-6 sm:p-8 flex flex-col justify-between space-y-6 cursor-pointer"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[#EEDBCA] flex items-center justify-center text-[#0E2419] shadow-sm">
                  <Flame className="w-5 h-5 text-[#FF5C6C]" />
                </div>
                <h3 className="text-lg font-bold text-[#0F1713]">
                  Zombie &amp; Price Hike Sentry
                </h3>
                <p className="text-xs text-[#64756B] leading-relaxed">
                  Detects silent +12% annual renewal jumps and flags 90-day inactive subscriptions draining monthly funds unnoticed.
                </p>
              </div>

              <div className="pt-4 border-t border-[#E8E1D2] flex items-center justify-between text-xs font-semibold text-[#0E2419]">
                <span>Scan for zombie debits</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>

            {/* Card 3 */}
            <div
              onClick={onLaunchDashboard}
              className="sand-card p-6 sm:p-8 flex flex-col justify-between space-y-6 cursor-pointer"
            >
              <div className="space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[#C6F6D5] flex items-center justify-center text-[#0B2417] shadow-sm">
                  <ShieldCheck className="w-5 h-5 text-[#15803D]" />
                </div>
                <h3 className="text-lg font-bold text-[#0F1713]">
                  RBI Master Direction Routes
                </h3>
                <p className="text-xs text-[#64756B] leading-relaxed">
                  Generates precise cancellation instructions &amp; statutory legal notices compliant with RBI Circular RBI/2019-20/53.
                </p>
              </div>

              <div className="pt-4 border-t border-[#E8E1D2] flex items-center justify-between text-xs font-semibold text-[#0B2417]">
                <span>View statutory protections</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================
            SUBSECTION 2: STEP-BY-STEP WORKFLOW
        ======================================================== */}
        <section id="how-it-works" className="max-w-6xl mx-auto space-y-10">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase tracking-wider text-[#64756B] bg-[#E8E1D2]/60 px-3 py-1 rounded-full font-semibold">
              SIMPLE 3-STEP FLOW
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0F1713] tracking-tight">
              From Confusing Statement to Zero Unwanted Debits
            </h2>
            <p className="text-xs sm:text-sm text-[#64756B]">
              No complicated banking integrations needed. Works instantly in your browser.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                step: '01',
                title: 'Drop Bank PDF or CSV',
                desc: 'Upload any statement from HDFC, SBI, ICICI, or Axis Bank. Processed 100% locally on your machine.'
              },
              {
                step: '02',
                title: 'Radar Maps Recurring Rails',
                desc: 'Our engine identifies cadences, isolates UPI Autopay / Card SI mandates, and checks parent company nodes.'
              },
              {
                step: '03',
                title: 'Cancel with 1 Tap',
                desc: 'Follow direct app routes or copy RBI-cited statutory revocation notices with pre-filled mandate references.'
              }
            ].map((s) => (
              <div key={s.step} className="p-8 rounded-3xl bg-white border border-[#E8E1D2] shadow-sm space-y-4 text-left">
                <div className="font-mono text-2xl font-extrabold text-[#2DE2B5] bg-[#0E2419] w-12 h-12 rounded-2xl flex items-center justify-center shadow-md">
                  {s.step}
                </div>
                <h3 className="text-lg font-bold text-[#0F1713]">{s.title}</h3>
                <p className="text-xs text-[#64756B] leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ========================================================
            SUBSECTION 3: INTERACTIVE SAVINGS CALCULATOR
        ======================================================== */}
        <section id="calculator" className="max-w-4xl mx-auto">
          <div className="p-8 sm:p-12 rounded-3xl sm:rounded-[40px] bg-[#0E2419] bg-stipple-forest border border-[#EEDBCA]/30 shadow-2xl text-[#F5EEDB] space-y-8">
            <div className="text-center space-y-2">
              <span className="text-xs font-mono uppercase tracking-wider text-[#2DE2B5] bg-[#2DE2B5]/15 px-3 py-1 rounded-full font-bold">
                ESTIMATE YOUR BLEED
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F5EEDB] tracking-tight">
                How Much Are Forgotten Mandates Costing You?
              </h2>
              <p className="text-xs sm:text-sm text-[#BAC8BF]">
                Adjust the slider below to calculate your estimated annual committed exposure.
              </p>
            </div>

            <div className="space-y-4 pt-4 max-w-xl mx-auto">
              <div className="flex items-center justify-between font-mono text-sm">
                <span className="text-[#BAC8BF]">Active Subscriptions &amp; Mandates:</span>
                <span className="text-2xl font-bold text-[#2DE2B5]">{calculatorMandates}</span>
              </div>
              <input
                type="range"
                min="3"
                max="25"
                value={calculatorMandates}
                onChange={(e) => setCalculatorMandates(Number(e.target.value))}
                className="w-full accent-[#2DE2B5] h-2 bg-white/20 rounded-lg cursor-pointer"
              />
              <div className="flex justify-between text-[11px] font-mono text-[#BAC8BF]">
                <span>3 mandates</span>
                <span>15 mandates</span>
                <span>25 mandates</span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-[#EEDBCA]/20 text-center">
              <div className="p-4 rounded-2xl bg-[#143323]/80 border border-white/10">
                <div className="text-[10px] font-mono text-[#BAC8BF] uppercase">Annual Exposure</div>
                <div className="text-2xl font-mono font-bold text-[#F5EEDB] mt-1">₹{calculatedTotal.toLocaleString('en-IN')}</div>
                <div className="text-[10px] text-[#BAC8BF] mt-0.5">Committed every year</div>
              </div>

              <div className="p-4 rounded-2xl bg-[#143323]/80 border border-white/10">
                <div className="text-[10px] font-mono text-[#FF5C6C] uppercase">Zombie Subscriptions</div>
                <div className="text-2xl font-mono font-bold text-[#FF5C6C] mt-1">~{calculatedZombies} Inactive</div>
                <div className="text-[10px] text-[#BAC8BF] mt-0.5">Paying with zero usage</div>
              </div>

              <div className="p-4 rounded-2xl bg-[#2DE2B5]/15 border border-[#2DE2B5]/40">
                <div className="text-[10px] font-mono text-[#2DE2B5] uppercase">Potential Savings</div>
                <div className="text-2xl font-mono font-bold text-[#2DE2B5] mt-1">₹{calculatedSavings.toLocaleString('en-IN')}</div>
                <div className="text-[10px] text-[#EFE8DC]/80 mt-0.5">Money back in your pocket</div>
              </div>
            </div>

            <div className="text-center pt-2">
              <button
                onClick={onLaunchDashboard}
                className="pill-fernwood-sand cursor-pointer text-xs sm:text-sm font-bold shadow-lg"
              >
                Scan My Bank Statement Now
              </button>
            </div>
          </div>
        </section>

        {/* ========================================================
            SUBSECTION 4: PAYMENT RAILS BREAKDOWN
        ======================================================== */}
        <section id="rails" className="max-w-6xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase tracking-wider text-[#64756B] bg-[#E8E1D2]/60 px-3 py-1 rounded-full font-semibold">
              COMPREHENSIVE COVERAGE
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0F1713] tracking-tight">
              Supported Payment Rails Across India
            </h2>
            <p className="text-xs sm:text-sm text-[#64756B]">
              Every recurring debit mechanism recognized by the National Payments Corporation of India (NPCI) and RBI.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              {
                rail: 'UPI Autopay',
                badge: 'NPCI FRAMEWORK',
                desc: 'Recurring mandates registered on BHIM, Google Pay, PhonePe, Paytm, and CRED.',
                icon: '⚡'
              },
              {
                rail: 'Card Standing Instructions',
                badge: 'VISA / MC / RUPAY',
                desc: 'E-mandates registered on Credit and Debit cards with 24-hour pre-debit notifications.',
                icon: '💳'
              },
              {
                rail: 'NACH / e-NACH',
                badge: 'BANK DEBITS',
                desc: 'Direct bank account recurring debit instructions for loans, insurance, and mutual funds.',
                icon: '🏛️'
              },
              {
                rail: 'In-App Billing',
                badge: 'APP STORES',
                desc: 'Subscriptions routed through Google Play Billing and Apple App Store in-app purchases.',
                icon: '📱'
              }
            ].map((r) => (
              <div key={r.rail} className="p-6 rounded-3xl bg-white border border-[#E8E1D2] shadow-sm space-y-3 text-left">
                <div className="text-2xl">{r.icon}</div>
                <div>
                  <span className="text-[9px] font-mono font-bold text-[#0E2419] bg-[#C6F6D5] px-2 py-0.5 rounded-md">
                    {r.badge}
                  </span>
                  <h4 className="text-sm font-bold text-[#0F1713] mt-2">{r.rail}</h4>
                </div>
                <p className="text-xs text-[#64756B] leading-relaxed">{r.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ========================================================
            SUBSECTION 5: LIVE MANDATE RADAR SCANNER
            (Replaces Comparison Table with Interactive 360° Radar)
        ======================================================== */}
        <section id="live-radar" className="max-w-6xl mx-auto space-y-6">
          <div className="text-center space-y-2 max-w-2xl mx-auto">
            <span className="text-xs font-mono uppercase tracking-wider text-[#0E2419] bg-[#C6F6D5] px-3.5 py-1 rounded-full font-bold">
              360° SENTRY SCANNER
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[#0F1713] tracking-tight">
              Live Mandate Radar
            </h2>
            <p className="text-xs sm:text-sm text-[#64756B] leading-relaxed">
              Concentric orbital rings map your payment rails (CARD_SI, UPI_AUTOPAY, NACH). The rotating sweep line identifies hidden recurring debits and silent price creep in real time.
            </p>
          </div>

          {/* Luxury Frame Container */}
          <div className="rounded-[36px] sm:rounded-[48px] bg-[#0E2419] border border-[#EEDBCA]/30 shadow-2xl overflow-hidden relative">
            <RadarHeroPanel
              className="min-h-[560px] sm:min-h-[640px]"
              onExploreMandate={onLaunchDashboard}
            />

            {/* Radar Telemetry Footer Strip */}
            <div className="bg-[#07150F] border-t border-[#2DE2B5]/20 px-6 sm:px-10 py-5 flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-[#BAC8BF]">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#2DE2B5] animate-ping" />
                  <span>Sweep Rate: <strong className="text-[#F5EEDB]">5.5s / 360°</strong></span>
                </div>
                <div className="h-3 w-[1px] bg-white/20 hidden sm:block" />
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#FF5C6C]" />
                  <span>Flagged Risks: <strong className="text-[#FF5C6C]">5 Mandates</strong></span>
                </div>
                <div className="h-3 w-[1px] bg-white/20 hidden sm:block" />
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[#FFB547]" />
                  <span>Silent Creep: <strong className="text-[#FFB547]">+12% Detected</strong></span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={onLaunchDashboard}
                  className="btn-primary text-xs px-5 py-2.5 font-bold shadow-lg flex items-center gap-2 cursor-pointer"
                >
                  <span>Open Full Mandate Radar</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================
            SUBSECTION 6: RBI RULES & FREQUENTLY ASKED QUESTIONS
        ======================================================== */}
        <section id="rbi-rules" className="max-w-4xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-xs font-mono uppercase tracking-wider text-[#64756B] bg-[#E8E1D2]/60 px-3 py-1 rounded-full font-semibold">
              KNOW YOUR RIGHTS
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-[#0F1713] tracking-tight">
              RBI Statutory Protections &amp; FAQs
            </h2>
            <p className="text-xs sm:text-sm text-[#64756B]">
              Everything you need to know about Indian e-mandates, consumer protections, and data privacy.
            </p>
          </div>

          <div className="space-y-3 text-left">
            {faqs.map((f, i) => (
              <div
                key={i}
                className="rounded-2xl bg-white border border-[#E8E1D2] overflow-hidden shadow-sm transition-all"
              >
                <button
                  onClick={() => setExpandedFaq(expandedFaq === i ? null : i)}
                  className="w-full p-5 text-left font-bold text-xs sm:text-sm text-[#0F1713] flex items-center justify-between cursor-pointer"
                >
                  <span>{f.q}</span>
                  <ChevronDown className={`w-4 h-4 text-[#64756B] transition-transform duration-200 ${expandedFaq === i ? 'rotate-180' : ''}`} />
                </button>
                {expandedFaq === i && (
                  <div className="px-5 pb-5 pt-1 text-xs text-[#64756B] leading-relaxed border-t border-[#E8E1D2]/60 bg-[#FAF8F5]">
                    {f.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* ========================================================
            SUBSECTION 7: GRAND BOTTOM CALL TO ACTION (CTA)
        ======================================================== */}
        <section className="max-w-6xl mx-auto">
          <div className="p-10 sm:p-14 rounded-3xl sm:rounded-[48px] bg-[#0E2419] bg-stipple-forest border border-[#EEDBCA]/30 shadow-2xl text-center space-y-6 relative overflow-hidden">
            <div className="relative z-10 max-w-2xl mx-auto space-y-3">
              <h2 className="text-3xl sm:text-5xl font-extrabold text-[#F5EEDB] tracking-tight">
                Stop paying for subscriptions you forgot you had.
              </h2>
              <p className="text-xs sm:text-sm text-[#EFE8DC]/80">
                Scan your statement in 30 seconds. No signup required to explore full live sample data.
              </p>

              <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3.5">
                <button
                  onClick={() => onOpenAuth('signup')}
                  className="pill-fernwood-sand flex items-center justify-center gap-2 cursor-pointer group shadow-lg"
                >
                  <span>Open your Mandate account</span>
                  <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                </button>

                <button
                  onClick={onLaunchDashboard}
                  className="pill-fernwood-green flex items-center justify-center gap-2 cursor-pointer"
                >
                  <Sparkles className="w-3.5 h-3.5 text-[#2DE2B5]" />
                  <span>Explore sample data (₹65,623)</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* 4. FOOTER */}
      <footer className="w-full bg-[#F8F5EE] border-t border-[#E8E1D2] px-6 sm:px-12 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#64756B]">
        <div className="flex items-center gap-2">
          <Leaf className="w-4 h-4 text-[#2DE2B5]" />
          <span>MANDATE RADAR · Combined Sand Beige &amp; Forest Green Luxury Architecture</span>
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={onOpenDesignSystem}
            className="text-xs font-mono text-[#0B2417] hover:underline flex items-center gap-1 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Design System Spec</span>
          </button>
          <span>·</span>
          <span>100% Client-Side Local Parsing</span>
        </div>
      </footer>
    </div>
  )
}
