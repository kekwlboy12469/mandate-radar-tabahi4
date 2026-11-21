import React, { useState, useEffect } from 'react'
import {
  Upload,
  FileText,
  Share2,
  ChevronDown,
  ChevronUp,
  Check,
  CheckCircle2,
  Lock,
  ArrowRight,
  ArrowLeft,
  Building2,
  Database,
  Radio,
  Sparkles,
  Loader2,
  AlertCircle
} from 'lucide-react'

export type OnboardingStep = 1 | 2 | 3

interface OnboardingFlowProps {
  initialStep?: OnboardingStep
  onBackToLogin: () => void
  onComplete: () => void
}

export const OnboardingFlow: React.FC<OnboardingFlowProps> = ({
  initialStep = 1,
  onBackToLogin,
  onComplete
}) => {
  const [step, setStep] = useState<OnboardingStep>(initialStep)
  
  // Step 1: Data Connection states
  const [selectedSource, setSelectedSource] = useState<'upload' | 'sample' | 'neo4j'>('sample')
  const [isNeo4jOpen, setIsNeo4jOpen] = useState(false)
  const [neo4jUri, setNeo4jUri] = useState('neo4j+s://8cf912ab.databases.neo4j.io')
  const [neo4jUser, setNeo4jUser] = useState('neo4j')
  const [neo4jPassword, setNeo4jPassword] = useState('••••••••••••')
  const [neo4jStatus, setNeo4jStatus] = useState<'idle' | 'testing' | 'connected'>('connected')

  // Step 2: Bank selection states
  const [selectedBank, setSelectedBank] = useState<'hdfc' | 'sbi' | 'icici' | 'axis' | 'other'>('hdfc')

  // Step 3: Scan checklist states
  const [scanProgress, setScanProgress] = useState(0)
  const [checklist, setChecklist] = useState({
    parsing: false,
    cadence: false,
    graph: false,
    risks: false
  })

  // Sync initialStep
  useEffect(() => {
    setStep(initialStep)
  }, [initialStep])

  // Step 3 Scanning Simulator
  useEffect(() => {
    if (step === 3) {
      setScanProgress(0)
      setChecklist({ parsing: false, cadence: false, graph: false, risks: false })

      const t1 = setTimeout(() => {
        setChecklist(prev => ({ ...prev, parsing: true }))
        setScanProgress(28)
      }, 700)

      const t2 = setTimeout(() => {
        setChecklist(prev => ({ ...prev, cadence: true }))
        setScanProgress(56)
      }, 1500)

      const t3 = setTimeout(() => {
        setChecklist(prev => ({ ...prev, graph: true }))
        setScanProgress(84)
      }, 2300)

      const t4 = setTimeout(() => {
        setChecklist(prev => ({ ...prev, risks: true }))
        setScanProgress(100)
      }, 3100)

      return () => {
        clearTimeout(t1)
        clearTimeout(t2)
        clearTimeout(t3)
        clearTimeout(t4)
      }
    }
  }, [step])

  const handleTestNeo4j = () => {
    setNeo4jStatus('testing')
    setTimeout(() => {
      setNeo4jStatus('connected')
    }, 1200)
  }

  return (
    <div className="w-full max-w-[880px] mx-auto min-h-[640px] flex flex-col justify-between py-6 px-4 sm:px-8 text-left">
      <div>
        {/* Top Header & Progress Stepper */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-[#203E30]/60 gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative w-7 h-7 rounded-full border border-[#2DE2B5] bg-[#0E1F17] flex items-center justify-center overflow-hidden">
              <div
                className="absolute inset-0 rounded-full animate-radar-sweep pointer-events-none"
                style={{
                  background: 'conic-gradient(from 0deg, transparent 65%, rgba(45, 226, 181, 0.4) 90%, #2DE2B5 100%)'
                }}
              />
              <div className="w-1.5 h-1.5 rounded-full bg-[#2DE2B5] z-10" />
            </div>
            <span className="font-bold text-base tracking-tight text-[#F7F3EB]">
              Mandate Radar
            </span>
          </div>

          {/* Stepper (1 Data -> 2 Bank -> 3 Scan) */}
          <div className="flex items-center gap-6 self-center">
            {/* Step 1 */}
            <div className="flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all ${
                  step === 1
                    ? 'bg-[#2DE2B5] text-[#061A13] shadow-[0_0_12px_rgba(45,226,181,0.4)]'
                    : step > 1
                    ? 'bg-[#2DE2B5]/20 text-[#2DE2B5] border border-[#2DE2B5]/40'
                    : 'bg-[#162E23] text-[#7E9387]'
                }`}
              >
                {step > 1 ? <Check className="w-3.5 h-3.5" /> : '1'}
              </div>
              <span className={`text-[11px] font-medium mt-1 ${step === 1 ? 'text-[#F7F3EB]' : 'text-[#7E9387]'}`}>
                Data
              </span>
            </div>

            <div className={`w-12 sm:w-16 h-[1.5px] -mt-4 transition-colors ${step > 1 ? 'bg-[#2DE2B5]' : 'bg-[#203E30]'}`} />

            {/* Step 2 */}
            <div className="flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all ${
                  step === 2
                    ? 'bg-[#2DE2B5] text-[#061A13] shadow-[0_0_12px_rgba(45,226,181,0.4)]'
                    : step > 2
                    ? 'bg-[#2DE2B5]/20 text-[#2DE2B5] border border-[#2DE2B5]/40'
                    : 'bg-[#162E23] text-[#7E9387]'
                }`}
              >
                {step > 2 ? <Check className="w-3.5 h-3.5" /> : '2'}
              </div>
              <span className={`text-[11px] font-medium mt-1 ${step === 2 ? 'text-[#F7F3EB]' : 'text-[#7E9387]'}`}>
                Bank
              </span>
            </div>

            <div className={`w-12 sm:w-16 h-[1.5px] -mt-4 transition-colors ${step > 2 ? 'bg-[#2DE2B5]' : 'bg-[#203E30]'}`} />

            {/* Step 3 */}
            <div className="flex flex-col items-center">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all ${
                  step === 3
                    ? 'bg-[#2DE2B5] text-[#061A13] shadow-[0_0_12px_rgba(45,226,181,0.4)]'
                    : 'bg-[#162E23] text-[#7E9387]'
                }`}
              >
                3
              </div>
              <span className={`text-[11px] font-medium mt-1 ${step === 3 ? 'text-[#F7F3EB]' : 'text-[#7E9387]'}`}>
                Scan
              </span>
            </div>
          </div>

          <div className="hidden sm:block text-[11px] font-mono tracking-wider text-[#7E9387] uppercase">
            SETUP YOUR RADAR
          </div>
        </div>

        {/* STEP 1: Connect your data (Exact Image 2 replica) */}
        {step === 1 && (
          <div className="mt-8 animate-fade-in">
            <div className="mb-6">
              <span className="font-mono text-[11px] uppercase tracking-wider text-[#2DE2B5] font-semibold">
                STEP 1 OF 3
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F7F3EB] mt-1">
                Connect your data
              </h2>
              <p className="text-sm text-[#BAC8BF] mt-1.5">
                Choose how to bring your recurring payments into view.
              </p>
            </div>

            {/* Cards Container */}
            <div className="space-y-4">
              {/* Card 1: Upload CSV/PDF statement */}
              <div
                onClick={() => setSelectedSource('upload')}
                className={`p-4 sm:p-5 rounded-xl border cursor-pointer transition-all ${
                  selectedSource === 'upload'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-1 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30] hover:border-[#335E4B] hover:bg-[#0E1F17]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[#2DE2B5]/10 border border-[#2DE2B5]/30 flex items-center justify-center text-[#2DE2B5]">
                      <Upload className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-base font-semibold text-[#F7F3EB]">
                        Upload CSV/PDF statement
                      </div>
                      <div className="text-xs text-[#BAC8BF] mt-0.5">
                        CSV or PDF · up to 20 MB
                      </div>
                    </div>
                  </div>
                  <div className="text-xs font-mono text-[#BAC8BF]">
                    ›
                  </div>
                </div>

                {selectedSource === 'upload' && (
                  <div className="mt-4 pt-4 border-t border-[#203E30] flex flex-col items-center justify-center border-dashed border-2 rounded-lg py-6 bg-[#07120D]/60 border-[#335E4B]">
                    <Upload className="w-6 h-6 text-[#2DE2B5] mb-2" />
                    <span className="text-xs text-[#F7F3EB] font-medium">
                      Drag &amp; drop bank statement here or click to browse
                    </span>
                    <span className="text-[11px] text-[#7E9387] mt-1">
                      Supports HDFC, SBI, ICICI, Axis, Kotak, and generic statement formats
                    </span>
                  </div>
                )}
              </div>

              {/* Card 2: Use sample data */}
              <div
                onClick={() => setSelectedSource('sample')}
                className={`p-4 sm:p-5 rounded-xl border cursor-pointer transition-all ${
                  selectedSource === 'sample'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-1 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30] hover:border-[#335E4B] hover:bg-[#0E1F17]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[#2DE2B5]/10 border border-[#2DE2B5]/30 flex items-center justify-center text-[#2DE2B5]">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-base font-semibold text-[#F7F3EB]">
                        Use sample data
                      </div>
                      <div className="text-xs text-[#BAC8BF] mt-0.5">
                        Explore a ready-to-scan Indian bank statement
                      </div>
                    </div>
                  </div>
                  {selectedSource === 'sample' && (
                    <div className="w-6 h-6 rounded-full bg-[#2DE2B5]/20 border border-[#2DE2B5] flex items-center justify-center text-[#2DE2B5]">
                      <Check className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>

                {selectedSource === 'sample' && (
                  <div className="mt-3.5 pt-3 border-t border-[#203E30]/70 flex flex-wrap gap-2 text-[11px] font-mono">
                    <span className="px-2 py-0.5 rounded bg-[#162E23] text-[#F7F3EB] border border-[#203E30]">
                      HDFC Salaried Statement
                    </span>
                    <span className="px-2 py-0.5 rounded bg-[#162E23] text-[#2DE2B5] border border-[#203E30]">
                      142 Transactions
                    </span>
                    <span className="px-2 py-0.5 rounded bg-[#162E23] text-[#FFB547] border border-[#203E30]">
                      10 Active Mandates
                    </span>
                  </div>
                )}
              </div>

              {/* Card 3: Connect Neo4j Aura (Advanced, collapsible) */}
              <div
                className={`p-4 sm:p-5 rounded-xl border transition-all ${
                  selectedSource === 'neo4j'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-1 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30]'
                }`}
              >
                <div
                  onClick={() => {
                    setSelectedSource('neo4j')
                    setIsNeo4jOpen(!isNeo4jOpen)
                  }}
                  className="flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[#8B7CFF]/15 border border-[#8B7CFF]/30 flex items-center justify-center text-[#8B7CFF]">
                      <Share2 className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="text-base font-semibold text-[#F7F3EB] flex items-center gap-2">
                        <span>Connect Neo4j Aura</span>
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#8B7CFF]/20 text-[#8B7CFF] border border-[#8B7CFF]/30">
                          Advanced
                        </span>
                      </div>
                      <div className="text-xs text-[#BAC8BF] mt-0.5">
                        Connect an existing graph workspace
                      </div>
                    </div>
                  </div>
                  <div className="text-[#BAC8BF]">
                    {isNeo4jOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                  </div>
                </div>

                {/* Collapsible Form */}
                {isNeo4jOpen && (
                  <div className="mt-4 pt-4 border-t border-[#203E30] space-y-3 animate-fade-in">
                    <div>
                      <label className="block text-[11px] font-mono uppercase text-[#BAC8BF] mb-1">
                        Bolt / Aura URI
                      </label>
                      <input
                        type="text"
                        value={neo4jUri}
                        onChange={e => setNeo4jUri(e.target.value)}
                        className="w-full px-3 py-2 text-xs font-mono fintech-input"
                      />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div>
                        <label className="block text-[11px] font-mono uppercase text-[#BAC8BF] mb-1">
                          Username
                        </label>
                        <input
                          type="text"
                          value={neo4jUser}
                          onChange={e => setNeo4jUser(e.target.value)}
                          className="w-full px-3 py-2 text-xs font-mono fintech-input"
                        />
                      </div>
                      <div>
                        <label className="block text-[11px] font-mono uppercase text-[#BAC8BF] mb-1">
                          Password
                        </label>
                        <input
                          type="password"
                          value={neo4jPassword}
                          onChange={e => setNeo4jPassword(e.target.value)}
                          className="w-full px-3 py-2 text-xs font-mono fintech-input"
                        />
                      </div>
                    </div>

                    <div className="pt-2 flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs font-mono">
                        <span
                          className={`w-2.5 h-2.5 rounded-full ${
                            neo4jStatus === 'connected'
                              ? 'bg-[#3DDC97] shadow-[0_0_8px_#3DDC97]'
                              : neo4jStatus === 'testing'
                              ? 'bg-[#FFB547] animate-pulse'
                              : 'bg-[#7E9387]'
                          }`}
                        />
                        <span className="text-[#BAC8BF]">
                          {neo4jStatus === 'connected'
                            ? 'AuraDB Enterprise connected · 12,480 merchant nodes'
                            : neo4jStatus === 'testing'
                            ? 'Pinging Bolt protocol...'
                            : 'Not tested yet'}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={handleTestNeo4j}
                        disabled={neo4jStatus === 'testing'}
                        className="btn-secondary text-xs px-3 py-1.5"
                      >
                        {neo4jStatus === 'testing' ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Testing...</span>
                          </>
                        ) : (
                          'Test connection'
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Helper link */}
            <div className="mt-4 text-xs font-medium text-[#2DE2B5]">
              No signup needed for sample data.
            </div>
          </div>
        )}

        {/* STEP 2: Choose your bank */}
        {step === 2 && (
          <div className="mt-8 animate-fade-in">
            <div className="mb-6">
              <span className="font-mono text-[11px] uppercase tracking-wider text-[#2DE2B5] font-semibold">
                STEP 2 OF 3
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F7F3EB] mt-1">
                Choose your bank
              </h2>
              <p className="text-sm text-[#BAC8BF] mt-1.5">
                Select your bank to optimize parsing for statement headers, UPI references, and mandate markers.
              </p>
            </div>

            {/* Bank Selectable Tiles */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* HDFC Bank */}
              <div
                onClick={() => setSelectedBank('hdfc')}
                className={`p-5 rounded-xl border cursor-pointer transition-all ${
                  selectedBank === 'hdfc'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-2 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30] hover:border-[#335E4B]'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-[#004C8F]/25 border border-[#004C8F]/40 flex items-center justify-center font-bold text-xs text-[#004C8F]">
                    HDFC
                  </div>
                  {selectedBank === 'hdfc' && (
                    <div className="w-5 h-5 rounded-full bg-[#2DE2B5] flex items-center justify-center text-[#061A13]">
                      <Check className="w-3.5 h-3.5 font-bold" />
                    </div>
                  )}
                </div>
                <div className="font-semibold text-sm text-[#F7F3EB]">HDFC Bank</div>
                <div className="text-xs text-[#BAC8BF] mt-1">
                  SmartAutoPay, BillPay &amp; NetBanking Standing Instructions
                </div>
              </div>

              {/* State Bank of India */}
              <div
                onClick={() => setSelectedBank('sbi')}
                className={`p-5 rounded-xl border cursor-pointer transition-all ${
                  selectedBank === 'sbi'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-2 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30] hover:border-[#335E4B]'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-[#280071]/25 border border-[#280071]/40 flex items-center justify-center font-bold text-xs text-[#280071]">
                    SBI
                  </div>
                  {selectedBank === 'sbi' && (
                    <div className="w-5 h-5 rounded-full bg-[#2DE2B5] flex items-center justify-center text-[#061A13]">
                      <Check className="w-3.5 h-3.5 font-bold" />
                    </div>
                  )}
                </div>
                <div className="font-semibold text-sm text-[#F7F3EB]">State Bank of India</div>
                <div className="text-xs text-[#BAC8BF] mt-1">
                  YONO Auto-Debit, INB &amp; NACH e-Mandate parser
                </div>
              </div>

              {/* ICICI Bank */}
              <div
                onClick={() => setSelectedBank('icici')}
                className={`p-5 rounded-xl border cursor-pointer transition-all ${
                  selectedBank === 'icici'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-2 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30] hover:border-[#335E4B]'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-[#F37024]/20 border border-[#F37024]/40 flex items-center justify-center font-bold text-xs text-[#F37024]">
                    ICICI
                  </div>
                  {selectedBank === 'icici' && (
                    <div className="w-5 h-5 rounded-full bg-[#2DE2B5] flex items-center justify-center text-[#061A13]">
                      <Check className="w-3.5 h-3.5 font-bold" />
                    </div>
                  )}
                </div>
                <div className="font-semibold text-sm text-[#F7F3EB]">ICICI Bank</div>
                <div className="text-xs text-[#BAC8BF] mt-1">
                  iMobile Standing Instructions &amp; Card SI regex
                </div>
              </div>

              {/* Axis Bank */}
              <div
                onClick={() => setSelectedBank('axis')}
                className={`p-5 rounded-xl border cursor-pointer transition-all ${
                  selectedBank === 'axis'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-2 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30] hover:border-[#335E4B]'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-[#97144D]/25 border border-[#97144D]/40 flex items-center justify-center font-bold text-xs text-[#97144D]">
                    AXIS
                  </div>
                  {selectedBank === 'axis' && (
                    <div className="w-5 h-5 rounded-full bg-[#2DE2B5] flex items-center justify-center text-[#061A13]">
                      <Check className="w-3.5 h-3.5 font-bold" />
                    </div>
                  )}
                </div>
                <div className="font-semibold text-sm text-[#F7F3EB]">Axis Bank</div>
                <div className="text-xs text-[#BAC8BF] mt-1">
                  Burgundy &amp; Retail statement engine with UPI Autopay
                </div>
              </div>

              {/* Other Bank */}
              <div
                onClick={() => setSelectedBank('other')}
                className={`p-5 rounded-xl border cursor-pointer transition-all sm:col-span-2 lg:col-span-2 ${
                  selectedBank === 'other'
                    ? 'bg-[#0E1F17] border-[#2DE2B5] ring-2 ring-[#2DE2B5]/30'
                    : 'bg-[#0E1F17]/60 border-[#203E30] hover:border-[#335E4B]'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-[#2DE2B5]/15 border border-[#2DE2B5]/30 flex items-center justify-center font-bold text-xs text-[#2DE2B5]">
                    OTHER
                  </div>
                  {selectedBank === 'other' && (
                    <div className="w-5 h-5 rounded-full bg-[#2DE2B5] flex items-center justify-center text-[#061A13]">
                      <Check className="w-3.5 h-3.5 font-bold" />
                    </div>
                  )}
                </div>
                <div className="font-semibold text-sm text-[#F7F3EB]">Other / Generic Bank CSV</div>
                <div className="text-xs text-[#BAC8BF] mt-1">
                  Kotak, PNB, IndusInd, IDFC First, Yes Bank or custom export
                </div>
              </div>
            </div>

            {/* Note banner */}
            <div className="mt-6 p-4 rounded-xl border border-[#203E30] bg-[#0E1F17]/80 text-xs text-[#BAC8BF] flex items-start gap-3">
              <Sparkles className="w-4 h-4 text-[#2DE2B5] shrink-0 mt-0.5" />
              <div>
                <strong className="text-[#F7F3EB]">Intelligent Descriptors Resolver:</strong> Regardless of bank, raw memo strings like <code className="text-[#2DE2B5] font-mono">UPI/P2M/23849182/SPOTIFY/SI</code> are mapped to their true corporate entity and direct cancellation links.
              </div>
            </div>
          </div>
        )}

        {/* STEP 3: Scanning... (Animated Radar & Live Checklist) */}
        {step === 3 && (
          <div className="mt-8 animate-fade-in text-center">
            <span className="font-mono text-[11px] uppercase tracking-wider text-[#2DE2B5] font-semibold">
              STEP 3 OF 3
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F7F3EB] mt-1">
              Scanning your bank statement...
            </h2>
            <p className="text-sm text-[#BAC8BF] mt-1.5 max-w-md mx-auto">
              Our graph engine is matching transaction descriptors against 12,000+ merchant entities.
            </p>

            {/* High-tech Radar Scanner */}
            <div className="my-8 relative w-48 h-48 mx-auto flex items-center justify-center">
              {/* Concentric rings */}
              <div className="absolute inset-0 rounded-full border border-[#2DE2B5]/25" />
              <div className="absolute inset-4 rounded-full border border-[#2DE2B5]/35 animate-radar-pulse" />
              <div className="absolute inset-10 rounded-full border border-[#2DE2B5]/45" />
              
              {/* Rotating Sweep */}
              <div
                className="absolute inset-0 rounded-full animate-radar-sweep pointer-events-none"
                style={{
                  background: 'conic-gradient(from 0deg, transparent 70%, rgba(45, 226, 181, 0.3) 90%, #2DE2B5 100%)'
                }}
              />

              {/* Progress Count-up in Center */}
              <div className="relative z-10 flex flex-col items-center">
                <span className="font-mono text-3xl font-extrabold text-[#F7F3EB] tabular-nums">
                  {scanProgress}%
                </span>
                <span className="font-mono text-[10px] text-[#2DE2B5] uppercase tracking-wider">
                  {scanProgress < 100 ? 'Analyzing' : 'Ready'}
                </span>
              </div>
            </div>

            {/* Live Checklist */}
            <div className="max-w-md mx-auto bg-[#0E1F17] border border-[#203E30] rounded-xl p-5 space-y-3.5 text-left">
              {/* 1. Parsing statement */}
              <div className="flex items-center justify-between text-xs sm:text-sm">
                <div className="flex items-center gap-2.5">
                  {checklist.parsing ? (
                    <CheckCircle2 className="w-4 h-4 text-[#3DDC97] shrink-0" />
                  ) : (
                    <Loader2 className="w-4 h-4 text-[#7E9387] animate-spin shrink-0" />
                  )}
                  <span className={checklist.parsing ? 'text-[#F7F3EB] font-medium' : 'text-[#7E9387]'}>
                    Parsing statement transactions
                  </span>
                </div>
                <span className="font-mono text-[11px] text-[#2DE2B5]">
                  {checklist.parsing ? '142 parsed' : 'Waiting...'}
                </span>
              </div>

              {/* 2. Inferring cadence */}
              <div className="flex items-center justify-between text-xs sm:text-sm">
                <div className="flex items-center gap-2.5">
                  {checklist.cadence ? (
                    <CheckCircle2 className="w-4 h-4 text-[#3DDC97] shrink-0" />
                  ) : checklist.parsing ? (
                    <Loader2 className="w-4 h-4 text-[#2DE2B5] animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-[#203E30] shrink-0" />
                  )}
                  <span className={checklist.cadence ? 'text-[#F7F3EB] font-medium' : 'text-[#7E9387]'}>
                    Inferring cadence &amp; recurring cycles
                  </span>
                </div>
                <span className="font-mono text-[11px] text-[#2DE2B5]">
                  {checklist.cadence ? '10 mandates' : '—'}
                </span>
              </div>

              {/* 3. Resolving merchants in graph */}
              <div className="flex items-center justify-between text-xs sm:text-sm">
                <div className="flex items-center gap-2.5">
                  {checklist.graph ? (
                    <CheckCircle2 className="w-4 h-4 text-[#3DDC97] shrink-0" />
                  ) : checklist.cadence ? (
                    <Loader2 className="w-4 h-4 text-[#2DE2B5] animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-[#203E30] shrink-0" />
                  )}
                  <span className={checklist.graph ? 'text-[#F7F3EB] font-medium' : 'text-[#7E9387]'}>
                    Resolving merchants in graph
                  </span>
                </div>
                <span className="font-mono text-[11px] text-[#8B7CFF]">
                  {checklist.graph ? 'Neo4j linked' : '—'}
                </span>
              </div>

              {/* 4. Flagging risks */}
              <div className="flex items-center justify-between text-xs sm:text-sm">
                <div className="flex items-center gap-2.5">
                  {checklist.risks ? (
                    <CheckCircle2 className="w-4 h-4 text-[#3DDC97] shrink-0" />
                  ) : checklist.graph ? (
                    <Loader2 className="w-4 h-4 text-[#2DE2B5] animate-spin shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-[#203E30] shrink-0" />
                  )}
                  <span className={checklist.risks ? 'text-[#F7F3EB] font-medium' : 'text-[#7E9387]'}>
                    Flagging risks &amp; price hikes
                  </span>
                </div>
                <span className="font-mono text-[11px] text-[#FF5C6C]">
                  {checklist.risks ? '4 flagged' : '—'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Action Controls */}
      <div className="mt-8 pt-6 border-t border-[#203E30]/60 flex flex-col sm:flex-row items-center justify-between gap-4">
        {/* Back Button */}
        {step === 1 ? (
          <button
            type="button"
            onClick={onBackToLogin}
            className="btn-ghost text-xs sm:text-sm w-full sm:w-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Login</span>
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setStep(s => (s - 1) as OnboardingStep)}
            className="btn-ghost text-xs sm:text-sm w-full sm:w-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
        )}

        {/* Security badge in center */}
        <div className="flex items-center gap-1.5 text-[11px] text-[#7E9387]">
          <Lock className="w-3.5 h-3.5 text-[#2DE2B5]" />
          <span>Your statement is processed locally and never sold.</span>
        </div>

        {/* Continue / Complete Button */}
        {step < 3 ? (
          <button
            type="button"
            onClick={() => setStep(s => (s + 1) as OnboardingStep)}
            className="btn-primary text-xs sm:text-sm px-6 h-10 w-full sm:w-auto"
          >
            <span>Continue</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <button
            type="button"
            disabled={scanProgress < 100}
            onClick={onComplete}
            className={`text-xs sm:text-sm px-6 h-10 w-full sm:w-auto ${
              scanProgress === 100 ? 'btn-primary' : 'btn-secondary opacity-60 cursor-not-allowed'
            }`}
          >
            <span>View Radar Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
