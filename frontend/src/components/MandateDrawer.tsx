import { useEffect, useState } from 'react'
import type { Mandate } from '../types'
import { inr, issueOf, ISSUE_LABEL } from '../lib/format'
import {
  X,
  Copy,
  Check,
  ShieldAlert,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Flame,
  CheckCircle2,
  ExternalLink,
  Clock,
  Sparkles,
  Tag
} from 'lucide-react'

type Tone = 'polite' | 'formal' | 'firm_dispute'
type Props = {
  mandate: Mandate
  userName?: string
  onClose: () => void
  onGenerateEmail?: (tone: Tone) => void
  emailSubject?: string
  emailBody?: string
  emailCopied?: boolean
  onCopyEmail?: () => void
  onConfirmCancel?: (id: string) => Promise<void> | void
  onAddTag?: (id: string, tag: string) => Promise<void> | void
}

const TONES: Array<[Tone, string]> = [
  ['polite', 'Polite'],
  ['formal', 'Formal'],
  ['firm_dispute', 'Firm dispute (RBI mandate)']
]

function Spark({ h }: { h: Mandate['history'] }) {
  const v = h.slice(-10).map(x => x.amount),
    mx = Math.max(...v, 1),
    W = 320,
    H = 64,
    bw = W / Math.max(v.length, 1)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="64" role="img" aria-label="Recent charges" className="rounded-lg bg-[#07120D] p-2 border border-[#203E30]">
      {v.map((a, i) => (
        <rect
          key={i}
          x={i * bw + 6}
          y={H - (a / mx) * (H - 12) - 4}
          width={Math.max(bw - 12, 6)}
          height={(a / mx) * (H - 12)}
          rx="3"
          fill="#2DE2B5"
          opacity={i === v.length - 1 ? 1 : 0.45}
        />
      ))}
    </svg>
  )
}

function Node({ x, y, t, s, hi }: { x: number; y: number; t: string; s: string; hi?: boolean }) {
  const cut = (z: string) => (z.length > 15 ? z.slice(0, 14) + '…' : z)
  return (
    <g>
      <rect
        x={x}
        y={y}
        width="114"
        height="46"
        rx="10"
        fill={hi ? '#16382B' : '#0E1F17'}
        stroke={hi ? '#2DE2B5' : '#203E30'}
        strokeWidth="1.2"
      />
      <text x={x + 10} y={y + 20} fill="#F7F3EB" fontSize="12" fontWeight="600">
        {cut(t)}
      </text>
      <text x={x + 10} y={y + 36} fill="#BAC8BF" fontSize="10" fontFamily="monospace">
        {cut(s)}
      </text>
    </g>
  )
}

function Path({ m }: { m: Mandate }) {
  return (
    <svg viewBox="0 0 430 180" width="100%" role="img" aria-label="Graph path from descriptor to merchant, owner and cancellation route" className="rounded-xl bg-[#07120D] p-3 border border-[#203E30]">
      <path d="M124 33H150M264 33H306M207 56V110M264 133H306" stroke="#335E4B" strokeWidth="1.5" strokeDasharray="3 3" fill="none" />
      <Node x={10} y={10} t="Descriptor" s={m.descriptor} />
      <Node x={150} y={10} t={m.merchant_name} s="Merchant" hi />
      <Node x={306} y={10} t={m.parent_name} s="Parent Corp" />
      <Node x={150} y={110} t={m.mechanism_name} s="Payment Rail" />
      <Node x={306} y={110} t="Cancel Route" s="Direct Revocation" hi />
      <text x="12" y="172" fill="#7E9387" fontSize="10" fontFamily="monospace">
        RESOLVES_TO · OWNED_BY · BILLED_VIA · CANCELLED_BY
      </text>
    </svg>
  )
}

export function MandateDrawer({
  mandate: m,
  userName = 'Rahul Sharma',
  onClose,
  onGenerateEmail,
  emailSubject,
  emailBody,
  emailCopied,
  onCopyEmail,
  onConfirmCancel,
  onAddTag
}: Props) {
  const [tone, setTone] = useState<Tone>('formal')
  const [localCopied, setLocalCopied] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)
  const [cancelledSuccess, setCancelledSuccess] = useState(false)
  const [tags, setTags] = useState<string[]>(m.tags || [])
  const [newTag, setNewTag] = useState('')
  const k = issueOf(m)

  useEffect(() => {
    setTags(m.tags || [])
  }, [m])

  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    addEventListener('keydown', h)
    return () => removeEventListener('keydown', h)
  }, [onClose])

  const copy = async () => {
    if (onCopyEmail) {
      onCopyEmail()
    } else {
      try {
        await navigator.clipboard.writeText(`Subject: ${emailSubject || 'Revocation'}\n\n${emailBody || ''}`)
        setLocalCopied(true)
        setTimeout(() => setLocalCopied(false), 1800)
      } catch {}
    }
  }

  const handleConfirmCancel = async () => {
    if (!onConfirmCancel) return
    setIsCancelling(true)
    try {
      await onConfirmCancel(m.id)
      setCancelledSuccess(true)
    } finally {
      setIsCancelling(false)
    }
  }

  const handleAddTag = async () => {
    const trimmed = newTag.trim()
    if (!trimmed || tags.includes(trimmed)) return
    const updated = [...tags, trimmed]
    setTags(updated)
    setNewTag('')
    if (onAddTag) {
      await onAddTag(m.id, trimmed)
    }
  }

  const defaultNotice = emailBody || `To: ${m.support_email || 'support@merchant.com'}\nSubject: Notice of Mandate Revocation: ${m.merchant_name} [${m.descriptor}]\n\nDear Customer Support Team,\n\nPlease terminate the recurring auto-debit standing instruction registered for ${m.merchant_name} (Descriptor: ${m.descriptor}) effective immediately.\n\nPer the RBI Digital Payments e-mandate framework, I hereby withdraw consent for subsequent debits on my account.\n\nAccount Holder: ${userName}\nMandate Ref: ${m.descriptor}\n\nKindly confirm revocation of this instruction at the earliest.\n\nSincerely,\n${userName}`

  const isAlreadyMarked = m.status === 'marked_cancelled' || cancelledSuccess
  const isVerifiedCancelled = m.status === 'verified_cancelled'
  const isStillCharging = m.status === 'still_charging'

  return (
    <div className="fixed inset-0 z-50 flex justify-end animate-fade-in text-left">
      {/* Scrim */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Slide-over Aside */}
      <aside
        className="relative w-full max-w-lg bg-[#0E1F17] border-l border-[#203E30] h-full overflow-y-auto p-6 sm:p-8 space-y-6 shadow-2xl z-10 text-[#F7F3EB]"
        role="dialog"
        aria-modal="true"
        aria-label={`${m.merchant_name} details`}
      >
        {/* Header */}
        <div className="flex items-start justify-between pb-4 border-b border-[#203E30]">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-semibold inline-block ${
                  k === 'price'
                    ? 'chip-hike'
                    : k === 'trial'
                    ? 'chip-trial'
                    : k === 'zombie'
                    ? 'chip-zombie'
                    : 'chip-safe'
                }`}
              >
                {ISSUE_LABEL[k]}
              </span>

              {/* Status Badge */}
              {isStillCharging && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-950/80 text-red-300 border border-red-500/50 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                  Still Charging Alert
                </span>
              )}
              {isVerifiedCancelled && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  Verified Cancelled
                </span>
              )}
              {isAlreadyMarked && !isVerifiedCancelled && !isStillCharging && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-950/80 text-amber-300 border border-amber-500/50 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-amber-400" />
                  Cancelled
                </span>
              )}
              {m.status === 'suggested_cancel' && !isAlreadyMarked && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-950/80 text-purple-300 border border-purple-500/50 flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-purple-400" />
                  Suggested to Cancel
                </span>
              )}
              {m.status === 'keep_confirmed' && (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-950/80 text-teal-300 border border-teal-500/50 flex items-center gap-1">
                  <Check className="w-3 h-3 text-teal-400" />
                  Keep Confirmed
                </span>
              )}
            </div>

            <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-[#F7F3EB] mt-1">
              {m.merchant_name}
            </h3>
            <div className="font-mono text-xs text-[#BAC8BF] mt-0.5 break-all">
              {m.descriptor}
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-[#162E23] border border-[#203E30] flex items-center justify-center hover:bg-[#203E30] transition-colors"
          >
            <X className="w-4 h-4 text-[#BAC8BF]" />
          </button>
        </div>

        {/* Dynamic Status Notification Banner */}
        {isStillCharging && (
          <div className="p-4 rounded-xl border border-red-500/40 bg-red-950/40 text-xs text-red-200 space-y-1">
            <div className="flex items-center gap-2 font-bold text-red-300 text-sm">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>STILL CHARGING ALERT (Reminder #{m.reminder_count || 1})</span>
            </div>
            <p className="leading-relaxed text-red-200/90">
              A subsequent debit of ₹{m.latest_amount} was detected on {m.last_charged} outside the 3-day cancellation grace window.
              Please file an immediate dispute with your bank or cancel the mandate directly in your banking app.
            </p>
          </div>
        )}

        {isVerifiedCancelled && (
          <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/40 text-xs text-emerald-200 space-y-1">
            <div className="flex items-center gap-2 font-bold text-emerald-300 text-sm">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>VERIFIED CANCELLED</span>
            </div>
            <p className="leading-relaxed text-emerald-200/90">
              Subsequent statement verified: Zero charges detected. Potential annual contractual savings of ₹{(m.annual_committed_cost || 0).toLocaleString('en-IN')} successfully realized.
            </p>
          </div>
        )}

        {isAlreadyMarked && !isVerifiedCancelled && !isStillCharging && (
          <div className="p-4 rounded-xl border border-amber-500/40 bg-amber-950/40 text-xs text-amber-200 space-y-1">
            <div className="flex items-center gap-2 font-bold text-amber-300 text-sm">
              <Clock className="w-4 h-4 text-amber-400 shrink-0" />
              <span>CANCELLED · AWAITING RECONCILIATION</span>
            </div>
            <p className="leading-relaxed text-amber-200/90">
              Cancelled on {m.marked_cancelled_on || 'recently'}. Upload your next bank statement to automatically verify zero subsequent debits.
            </p>
          </div>
        )}

        {m.status === 'suggested_cancel' && !isAlreadyMarked && (
          <div className="p-4 rounded-xl border border-purple-500/40 bg-purple-950/40 text-xs text-purple-200 space-y-1">
            <div className="flex items-center gap-2 font-bold text-purple-300 text-sm">
              <Sparkles className="w-4 h-4 text-purple-400 shrink-0" />
              <span>SUGGESTED TO CANCEL</span>
            </div>
            <p className="leading-relaxed text-purple-200/90">
              Identified as a redundant subscription by graph overlap analysis. Cancelling this will save ₹{(m.annual_committed_cost || 0).toLocaleString('en-IN')}/year without losing capability.
            </p>
          </div>
        )}

        {/* Flag Reason Alert Banner */}
        <div className="p-3.5 rounded-xl border border-[#203E30] bg-[#162E23]/70 text-xs text-[#BAC8BF] leading-relaxed">
          <strong className="text-[#F7F3EB] block mb-1">Reason for Flag:</strong>
          {m.flag_reason}
        </div>

        {/* Last Charges History */}
        <div>
          <h4 className="text-xs font-mono uppercase text-[#BAC8BF] mb-2">Transaction History</h4>
          <Spark h={m.history} />
          <p className="text-[11px] font-mono text-[#7E9387] mt-1.5">
            {m.charge_count} charges since {m.first_seen}. Latest charge: {inr(m.latest_amount)}.
          </p>
        </div>

        {/* Graph Identification */}
        <div>
          <h4 className="text-xs font-mono uppercase text-[#BAC8BF] mb-2">Graph Entity Resolution</h4>
          {m.is_recognized ? (
            <Path m={m} />
          ) : (
            <div className="p-4 rounded-xl border border-[#203E30] bg-[#07120D] text-xs text-[#BAC8BF]">
              No verified match found for this memo string.
            </div>
          )}
          <p className="text-[11px] font-mono text-[#7E9387] mt-1.5">
            Parent Corp: <strong className="text-[#F7F3EB]">{m.parent_name}</strong> · Rail: <strong className="text-[#2DE2B5]">{m.mechanism_name}</strong>
          </p>
        </div>

        {/* How to Stop / Cancellation Steps */}
        <div>
          <h4 className="text-xs font-mono uppercase text-[#BAC8BF] mb-2">How to Stop This Mandate</h4>
          <ol className="space-y-2 list-decimal list-inside text-xs text-[#BAC8BF] bg-[#07120D] p-4 rounded-xl border border-[#203E30]">
            {m.cancellation_steps.map((step, idx) => (
              <li key={idx} className="leading-relaxed">
                <span className="text-[#F7F3EB]">{step}</span>
              </li>
            ))}
          </ol>
          {m.pitfall && (
            <div className="mt-2.5 p-3 rounded-lg border border-[#FFB547]/30 bg-[#FFB547]/10 text-xs text-[#FFB547] flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-[#FFB547]" />
              <span>{m.pitfall}</span>
            </div>
          )}

          {/* Direct Cancellation Action Button */}
          <div className="mt-4">
            {isVerifiedCancelled ? (
              <div className="w-full py-2.5 px-3 rounded-xl bg-emerald-950/50 border border-emerald-500/40 text-xs text-emerald-300 font-semibold flex items-center justify-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>Verified Cancelled (Zero charges in subsequent statement)</span>
              </div>
            ) : isAlreadyMarked ? (
              <div className="w-full py-2.5 px-3 rounded-xl bg-amber-950/50 border border-amber-500/40 text-xs text-amber-300 font-semibold flex items-center justify-center gap-2">
                <Clock className="w-4 h-4 text-amber-400" />
                <span>Cancelled ({m.marked_cancelled_on || 'Today'}) · Awaiting Statement Verification</span>
              </div>
            ) : (
              <button
                onClick={handleConfirmCancel}
                disabled={isCancelling}
                className="w-full py-3 px-4 rounded-xl bg-[#DC2626] hover:bg-[#B91C1C] text-white text-xs font-bold transition-all shadow-lg flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                <Check className="w-4 h-4" />
                <span>{isCancelling ? 'Recording Cancellation...' : 'Confirm I Have Cancelled in App'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Account Details, Billing Type & Tags */}
        <div className="p-4 rounded-xl border border-[#203E30] bg-[#07120D] text-xs space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[#BAC8BF]">Account Source:</span>
            <span className="font-mono text-[#F7F3EB] font-medium bg-[#162E23] px-2 py-0.5 rounded border border-[#203E30]">
              {m.account_label || 'Primary Account'}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-[#BAC8BF]">Contract Billing Type:</span>
            <span className="font-mono text-[#2DE2B5] font-medium">
              {m.billing_type === 'usage_based' ? 'Usage-Based (Variable Metered)' : 'Fixed Contractual'}
            </span>
          </div>

          <div className="pt-2 border-t border-[#203E30]/60">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[#BAC8BF] font-mono text-[10px] uppercase flex items-center gap-1">
                <Tag className="w-3 h-3 text-[#2DE2B5]" />
                User Scoped Tags
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-1.5">
              {tags.map(t => (
                <span key={t} className="px-2 py-0.5 rounded-md bg-[#162E23] text-[11px] font-mono text-[#2DE2B5] border border-[#203E30]">
                  #{t}
                </span>
              ))}
              <div className="flex items-center gap-1">
                <input
                  type="text"
                  placeholder="+ Add tag..."
                  value={newTag}
                  onChange={e => setNewTag(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddTag()
                    }
                  }}
                  className="px-2 py-0.5 rounded-md bg-[#0E1F17] border border-[#203E30] text-[11px] text-[#F7F3EB] placeholder-[#7E9387] w-24 focus:outline-none focus:border-[#2DE2B5]"
                />
                {newTag && (
                  <button
                    onClick={handleAddTag}
                    className="px-2 py-0.5 rounded bg-[#2DE2B5] text-[#061A13] text-[10px] font-bold cursor-pointer"
                  >
                    Add
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Revocation Notice Notice Generator */}
        <div>
          <h4 className="text-xs font-mono uppercase text-[#BAC8BF] mb-2">Statutory Revocation Notice (RBI Master Direction)</h4>
          <div className="flex gap-2 mb-2.5">
            {TONES.map(([t, label]) => (
              <button
                key={t}
                onClick={() => {
                  setTone(t)
                  onGenerateEmail?.(t)
                }}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                  tone === t
                    ? 'bg-[#2DE2B5] text-[#061A13] font-bold shadow-sm'
                    : 'bg-[#162E23] text-[#BAC8BF] hover:text-[#F7F3EB]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <textarea
            readOnly
            value={defaultNotice}
            rows={7}
            className="w-full p-3 font-mono text-[11px] bg-[#07120D] border border-[#203E30] rounded-xl text-[#BAC8BF] focus:outline-none leading-relaxed"
          />

          <button
            onClick={copy}
            className="w-full mt-3 h-10 btn-primary text-xs font-semibold"
          >
            {localCopied || emailCopied ? (
              <>
                <Check className="w-4 h-4 text-[#061A13]" />
                <span>Notice Copied to Clipboard</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>Copy Notice &amp; Direct Link</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </div>
  )
}
