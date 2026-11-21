import React, { useEffect, useState } from 'react'
import { AlertCircle, TrendingUp, ShieldAlert, Zap } from 'lucide-react'

interface RadarHeroPanelProps {
  compact?: boolean
  className?: string
  onExploreMandate?: (merchant: string) => void
}

interface Blip {
  id: string
  name: string
  parent?: string
  angle: number // degrees (0 at top, clockwise)
  radius: number // percentage from center (0 to 100)
  amount: number
  cadence: string
  flag?: 'PRICE_HIKE' | 'ZOMBIE' | 'SAFE' | 'TRIAL'
  rail: string
  color?: string
}

const BLIPS: Blip[] = [
  { id: 'spotify', name: 'Spotify', angle: 55, radius: 46, amount: 1199, cadence: 'yr', flag: 'PRICE_HIKE', rail: 'UPI_AUTOPAY', color: '#1DB954' },
  { id: 'youtube', name: 'YouTube', parent: 'Alphabet', angle: 28, radius: 78, amount: 189, cadence: 'mo', flag: 'SAFE', rail: 'PLAY_STORE', color: '#FF0000' },
  { id: 'netflix', name: 'Netflix', angle: 305, radius: 62, amount: 649, cadence: 'mo', flag: 'ZOMBIE', rail: 'CARD_SI', color: '#E50914' },
  { id: 'prime', name: 'Amazon Prime', parent: 'Amazon', angle: 210, radius: 68, amount: 1499, cadence: 'yr', flag: 'SAFE', rail: 'CARD_SI', color: '#FF9900' },
  { id: 'audible', name: 'Audible', parent: 'Amazon', angle: 245, radius: 76, amount: 199, cadence: 'mo', flag: 'ZOMBIE', rail: 'CARD_SI', color: '#F8991D' },
  { id: 'hotstar', name: 'Hotstar', parent: 'Disney', angle: 338, radius: 82, amount: 899, cadence: 'yr', flag: 'TRIAL', rail: 'UPI_AUTOPAY', color: '#1B365D' }
]

const PARENT_NODES = [
  { id: 'alphabet', name: 'Alphabet', angle: 42, radius: 90 },
  { id: 'amazon', name: 'Amazon', angle: 228, radius: 88 },
  { id: 'disney', name: 'Disney', angle: 320, radius: 92 }
]

export const RadarHeroPanel: React.FC<RadarHeroPanelProps> = ({
  compact = false,
  className = '',
  onExploreMandate
}) => {
  const [sweepAngle, setSweepAngle] = useState(0)
  const [activeBlip, setActiveBlip] = useState<string | null>(null)
  const [hoveredBlip, setHoveredBlip] = useState<Blip | null>(null)

  // Continuously rotate sweep angle to trigger blip illumination
  useEffect(() => {
    let animationFrameId: number
    let startTimestamp: number | null = null
    const duration = 5500 // 5.5s per revolution

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp
      const elapsed = timestamp - startTimestamp
      const angle = (elapsed % duration) / duration * 360
      setSweepAngle(angle)

      // Check proximity to blips (trigger active ping when sweep passes within 15 degrees)
      const nearby = BLIPS.find(b => {
        const diff = Math.abs(b.angle - angle)
        return diff < 12 || Math.abs(diff - 360) < 12
      })
      if (nearby) {
        setActiveBlip(nearby.id)
      }

      animationFrameId = requestAnimationFrame(step)
    }

    animationFrameId = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animationFrameId)
  }, [])

  // Helper to convert polar (angle in deg, radius in %) to cartesian (% from center)
  const getCoordinates = (angleDeg: number, radiusPercent: number) => {
    // 0 deg is top (12 o'clock), 90 deg is right (3 o'clock)
    const rad = (angleDeg - 90) * (Math.PI / 180)
    // Scale radius to fit inside circular viewport (max 46% so nodes don't overflow)
    const r = (radiusPercent / 100) * 44
    const x = 50 + r * Math.cos(rad)
    const y = 50 + r * Math.sin(rad)
    return { x, y }
  }

  return (
    <div
      className={`relative w-full overflow-hidden flex flex-col items-center justify-center select-none ${
        compact ? 'h-[280px] sm:h-[340px]' : 'h-full min-h-[580px] lg:min-h-[700px]'
      } ${className}`}
      style={{
        background: 'radial-gradient(ellipse at 50% 50%, #0E241B 0%, #081510 50%, #050E0A 100%)'
      }}
    >
      {/* Background Coordinate Grid */}
      <div
        className="absolute inset-0 opacity-[0.07] pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(247, 243, 235, 0.4) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(247, 243, 235, 0.4) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px'
        }}
      />

      {/* Top Banner Tagline */}
      <div className="absolute top-6 left-8 z-20 pointer-events-none">
        <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-[#2DE2B5]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#2DE2B5] animate-ping" />
          YOUR MONEY, IN VIEW
        </div>
        <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#F7F3EB] mt-1">
          Nothing off the radar.
        </h3>
        <p className="text-xs sm:text-sm text-[#BAC8BF]">
          Subscriptions. Mandates. Standing instructions.
        </p>
      </div>

      {/* Radar Container */}
      <div className="relative w-[340px] h-[340px] sm:w-[460px] sm:h-[460px] md:w-[540px] md:h-[540px] flex items-center justify-center">
        
        {/* Concentric Circles */}
        {[20, 40, 60, 80, 100].map((radius, idx) => (
          <div
            key={radius}
            className="absolute rounded-full border border-[#2DE2B5]/15 transition-all duration-300"
            style={{
              width: `${radius}%`,
              height: `${radius}%`,
              boxShadow: idx === 4 ? '0 0 40px rgba(45, 226, 181, 0.04)' : undefined
            }}
          />
        ))}

        {/* Crosshair Axes */}
        <div className="absolute w-full h-[1px] bg-[#2DE2B5]/10" />
        <div className="absolute h-full w-[1px] bg-[#2DE2B5]/10" />

        {/* Diagonal Reference Axes */}
        <div className="absolute w-full h-[1px] bg-[#2DE2B5]/5 rotate-45" />
        <div className="absolute w-full h-[1px] bg-[#2DE2B5]/5 -rotate-45" />

        {/* Degree Markers */}
        <span className="absolute top-2 text-[10px] font-mono text-[#7E9387]">0° / N</span>
        <span className="absolute right-2 text-[10px] font-mono text-[#7E9387]">90° / E</span>
        <span className="absolute bottom-2 text-[10px] font-mono text-[#7E9387]">180° / S</span>
        <span className="absolute left-2 text-[10px] font-mono text-[#7E9387]">270° / W</span>

        {/* Rotating Radar Sweep Cone */}
        <div
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            transform: `rotate(${sweepAngle}deg)`,
            transformOrigin: '50% 50%',
            background: `conic-gradient(from 0deg, transparent 0deg, transparent 270deg, rgba(45, 226, 181, 0.03) 300deg, rgba(45, 226, 181, 0.18) 350deg, rgba(45, 226, 181, 0.55) 360deg)`
          }}
        />

        {/* Leading Laser Line of Sweep */}
        <div
          className="absolute w-[50%] h-[1.5px] origin-left pointer-events-none"
          style={{
            left: '50%',
            top: '50%',
            transform: `rotate(${sweepAngle - 90}deg)`,
            background: 'linear-gradient(90deg, rgba(45, 226, 181, 0.95) 0%, rgba(45, 226, 181, 0.3) 80%, transparent 100%)',
            boxShadow: '0 0 10px #2DE2B5, 0 0 20px rgba(45, 226, 181, 0.5)'
          }}
        />

        {/* Center Radar Beacon */}
        <div className="absolute z-10 w-3 h-3 rounded-full bg-[#2DE2B5] shadow-[0_0_12px_#2DE2B5]">
          <div className="absolute inset-0 rounded-full bg-[#2DE2B5] animate-ping opacity-60" />
        </div>

        {/* SVG Graph Edges (Connecting Merchants to Parent Nodes) */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
          {/* YouTube -> Alphabet */}
          {(() => {
            const yt = getCoordinates(28, 78)
            const alph = getCoordinates(42, 90)
            return (
              <line
                x1={`${yt.x}%`}
                y1={`${yt.y}%`}
                x2={`${alph.x}%`}
                y2={`${alph.y}%`}
                stroke="rgba(139, 124, 255, 0.35)"
                strokeWidth="1.2"
                strokeDasharray="3 3"
              />
            )
          })()}

          {/* Prime & Audible -> Amazon */}
          {(() => {
            const p = getCoordinates(210, 68)
            const a = getCoordinates(245, 76)
            const amz = getCoordinates(228, 88)
            return (
              <>
                <line
                  x1={`${p.x}%`}
                  y1={`${p.y}%`}
                  x2={`${amz.x}%`}
                  y2={`${amz.y}%`}
                  stroke="rgba(139, 124, 255, 0.35)"
                  strokeWidth="1.2"
                  strokeDasharray="3 3"
                />
                <line
                  x1={`${a.x}%`}
                  y1={`${a.y}%`}
                  x2={`${amz.x}%`}
                  y2={`${amz.y}%`}
                  stroke="rgba(139, 124, 255, 0.35)"
                  strokeWidth="1.2"
                  strokeDasharray="3 3"
                />
              </>
            )
          })()}

          {/* Hotstar -> Disney */}
          {(() => {
            const hs = getCoordinates(338, 82)
            const dis = getCoordinates(320, 92)
            return (
              <line
                x1={`${hs.x}%`}
                y1={`${hs.y}%`}
                x2={`${dis.x}%`}
                y2={`${dis.y}%`}
                stroke="rgba(139, 124, 255, 0.35)"
                strokeWidth="1.2"
                strokeDasharray="3 3"
              />
            )
          })()}
        </svg>

        {/* Parent Company Nodes */}
        {PARENT_NODES.map(p => {
          const coords = getCoordinates(p.angle, p.radius)
          return (
            <div
              key={p.id}
              className="absolute z-10 flex items-center gap-1.5 -translate-x-1/2 -translate-y-1/2 pointer-events-none"
              style={{ left: `${coords.x}%`, top: `${coords.y}%` }}
            >
              <div className="w-2 h-2 rounded-full bg-[#8B7CFF] shadow-[0_0_8px_#8B7CFF]" />
              <span className="font-mono text-[10px] text-[#8B7CFF] opacity-80 whitespace-nowrap">
                {p.name}
              </span>
            </div>
          )
        })}

        {/* Merchant Blips */}
        {BLIPS.map(blip => {
          const coords = getCoordinates(blip.angle, blip.radius)
          const isSweepLit = activeBlip === blip.id
          const isHovered = hoveredBlip?.id === blip.id

          return (
            <div
              key={blip.id}
              className="absolute z-20 group -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-transform duration-200 hover:scale-110"
              style={{ left: `${coords.x}%`, top: `${coords.y}%` }}
              onMouseEnter={() => setHoveredBlip(blip)}
              onMouseLeave={() => setHoveredBlip(null)}
              onClick={() => onExploreMandate?.(blip.name)}
            >
              <div className="relative flex items-center">
                {/* Glowing Radar Blip Dot */}
                <div
                  className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                    isSweepLit
                      ? 'bg-[#2DE2B5] scale-150 shadow-[0_0_14px_#2DE2B5]'
                      : 'bg-[#2DE2B5]/80 shadow-[0_0_6px_#2DE2B5]'
                  }`}
                  style={{
                    backgroundColor: blip.flag === 'ZOMBIE' ? '#FF5C6C' : blip.flag === 'PRICE_HIKE' ? '#FFB547' : '#2DE2B5',
                    boxShadow: isSweepLit
                      ? `0 0 16px ${blip.flag === 'ZOMBIE' ? '#FF5C6C' : blip.flag === 'PRICE_HIKE' ? '#FFB547' : '#2DE2B5'}`
                      : undefined
                  }}
                >
                  {isSweepLit && (
                    <div className="absolute inset-0 rounded-full animate-ping bg-current opacity-75" />
                  )}
                </div>

                {/* Blip Name Tag */}
                <span className="ml-2 font-sans text-[11px] font-medium tracking-tight text-[#F7F3EB]/90 whitespace-nowrap drop-shadow-[0_1px_4px_rgba(0,0,0,0.8)]">
                  {blip.name}
                </span>

                {/* Hover Details Tooltip */}
                {isHovered && (
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 p-2 bg-[#0E1F17]/95 border border-[#2DE2B5]/40 rounded-lg shadow-xl text-left min-w-[130px] z-50 pointer-events-none backdrop-blur-md animate-fade-in">
                    <div className="text-[11px] font-semibold text-[#F7F3EB]">{blip.name}</div>
                    <div className="text-[12px] font-mono font-bold text-[#2DE2B5]">
                      ₹{blip.amount.toLocaleString('en-IN')}/{blip.cadence}
                    </div>
                    <div className="text-[9px] font-mono text-[#BAC8BF] mt-0.5">{blip.rail}</div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Floating Glass Overlays (Exact Match to User Image 1) */}
      
      {/* 1. Main Committed Total Glass Card (Bottom Left) */}
      <div className="absolute bottom-6 left-6 z-30 max-w-[280px] sm:max-w-[320px] p-4 sm:p-5 rounded-xl border border-white/10 bg-[#0E1F17]/80 backdrop-blur-md shadow-2xl transition-all duration-300 hover:border-[#2DE2B5]/40 hover:bg-[#0E1F17]/90">
        <div className="flex items-baseline gap-1">
          <span className="font-mono text-3xl sm:text-4xl font-bold tracking-tight text-[#F7F3EB] tabular-nums">
            ₹65,623
          </span>
          <span className="text-xs sm:text-sm font-medium text-[#BAC8BF]">/ year</span>
        </div>
        <p className="text-xs text-[#BAC8BF] mt-1">
          committed across 10 mandates
        </p>
        <div className="mt-2.5 flex items-center gap-1.5 text-[11px] font-medium text-[#2DE2B5]">
          <Zap className="w-3.5 h-3.5" />
          <span>Graph-verified via Neo4j entity resolver</span>
        </div>
      </div>

      {/* 2. Top-Right Floating Card: 3 Zombie Charges Found */}
      <div className="absolute top-12 right-6 z-30 flex items-center gap-2 px-3.5 py-2 rounded-lg border border-[#FF5C6C]/40 bg-[#0E1F17]/85 backdrop-blur-md shadow-lg transition-transform hover:scale-105">
        <div className="w-2 h-2 rounded-full bg-[#FF5C6C] animate-pulse" />
        <span className="text-xs font-semibold text-[#FF5C6C] tracking-wide">
          3 zombie charges found
        </span>
      </div>

      {/* 3. Bottom-Right Floating Card: Price Hike Detected */}
      <div className="absolute bottom-10 right-6 z-30 flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[#FFB547]/40 bg-[#0E1F17]/85 backdrop-blur-md shadow-lg transition-transform hover:scale-105">
        <TrendingUp className="w-4 h-4 text-[#FFB547]" />
        <span className="text-xs font-semibold text-[#FFB547]">
          Price hike detected: +12% on Spotify
        </span>
      </div>
    </div>
  )
}
