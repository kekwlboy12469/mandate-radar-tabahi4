import { useEffect, useRef, useState } from 'react'
import type { Mandate } from '../App'
import { inr, issueOf, ISSUE_LABEL, type IssueKey } from '../lib/format'

type Props = {
  mandates: Mandate[]
  total: number
  cancelled: Set<string>
  loading: boolean
  overlaps?: any[]
  reconciliation?: any
  onToggle: (id: string) => void
  onCancelFlagged: () => void
  onClear: () => void
  onOpen: (m: Mandate) => void
  onConfirmOverlaps?: (keptIds: string[], cancelIds: string[]) => Promise<void>
  onConfirmCancellation?: (mandateId: string) => Promise<void>
}

function useTween(target: number) {
  const [v, setV] = useState(target)
  const from = useRef(target)
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { setV(target); from.current = target; return }
    const a = from.current, t0 = performance.now()
    let raf = 0
    const step = (t: number) => {
      const k = Math.min(1, (t - t0) / 450)
      const val = a + (target - a) * (1 - Math.pow(1 - k, 3))
      setV(val); from.current = val
      if (k < 1) raf = requestAnimationFrame(step)
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [target])
  return v
}

export function RadarView({
  mandates,
  total,
  cancelled,
  loading,
  overlaps = [],
  reconciliation,
  onToggle,
  onCancelFlagged,
  onClear,
  onOpen,
  onConfirmOverlaps,
  onConfirmCancellation
}: Props) {
  const [filter, setFilter] = useState<'all' | IssueKey>('all')
  const [showOverlapModal, setShowOverlapModal] = useState(false)
  const [selectedKept, setSelectedKept] = useState<Record<string, boolean>>({})
  const [cancellingMandate, setCancellingMandate] = useState<Mandate | null>(null)
  const [submittingDecision, setSubmittingDecision] = useState(false)

  // Initialize selected kept for overlaps
  useEffect(() => {
    if (overlaps.length > 0) {
      const initial: Record<string, boolean> = {}
      overlaps.forEach(o => {
        const parentId = o.parent_mandate?.id || o.parent_mandate?.merchant_id
        const incId = o.included_mandate?.id || o.included_mandate?.merchant_id
        if (parentId) initial[parentId] = true // Keep primary parent bundle by default
        if (incId) initial[incId] = false // Redundant bundle unchecked by default
      })
      setSelectedKept(initial)
    }
  }, [overlaps])

  const saved = mandates.filter(m => cancelled.has(m.id)).reduce((s, m) => s + m.annual_committed_cost, 0)
  const keep = Math.max(0, total - saved)
  const shown = useTween(keep)
  const counts: Record<string, number> = { all: mandates.length }
  mandates.forEach(m => { const k = issueOf(m); counts[k] = (counts[k] || 0) + 1 })
  const rows = mandates.filter(m => filter === 'all' || issueOf(m) === filter)
  const chips: Array<['all' | IssueKey, string]> = [
    ['all', 'All mandates'],
    ['overlap', 'Bundle overlap'],
    ['price', 'Price creep'],
    ['trial', 'Trial trap'],
    ['zombie', 'Unused'],
    ['unk', 'Unrecognised']
  ]

  const totalOverlapSavings = overlaps.reduce((sum, o) => sum + (o.potential_annual_saving || 0), 0)

  const handleDecisionSubmit = async () => {
    if (!onConfirmOverlaps) return
    setSubmittingDecision(true)
    try {
      const keptIds: string[] = []
      const cancelIds: string[] = []
      overlaps.forEach(o => {
        const pId = o.parent_mandate?.id
        const cId = o.included_mandate?.id
        if (pId) {
          if (selectedKept[pId]) keptIds.push(pId); else cancelIds.push(pId)
        }
        if (cId) {
          if (selectedKept[cId]) keptIds.push(cId); else cancelIds.push(cId)
        }
      })
      await onConfirmOverlaps(keptIds, cancelIds)
      setShowOverlapModal(false)
    } catch (err) {
      console.error('Error confirming overlap decision:', err)
    } finally {
      setSubmittingDecision(false)
    }
  }

  const handleConfirmCancelAction = async () => {
    if (!cancellingMandate || !onConfirmCancellation) return
    try {
      await onConfirmCancellation(cancellingMandate.id)
      setCancellingMandate(null)
    } catch (err) {
      console.error('Error confirming cancellation:', err)
    }
  }

  return (
    <div className="mr">
      {/* 1. OVERLAP DETECTION BANNER */}
      {overlaps.length > 0 && (
        <div className="card-glass p-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-sm">!</div>
            <div>
              <div className="font-semibold text-sm text-white">
                {overlaps.length} Redundant Bundle Overlap{overlaps.length > 1 ? 's' : ''} Identified in Neo4j
              </div>
              <div className="text-xs text-neutral-300">
                One paid service already bundles another (e.g. YouTube Premium includes YouTube Music). Potential savings: <strong>{inr(totalOverlapSavings)}/year</strong>.
              </div>
            </div>
          </div>
          <button
            onClick={() => setShowOverlapModal(true)}
            className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-bold text-xs transition shadow-sm whitespace-nowrap"
          >
            Review Overlaps
          </button>
        </div>
      )}

      {/* 2. RECONCILIATION ALERTS */}
      {reconciliation?.still_charging && reconciliation.still_charging.length > 0 && (
        <div className="card-glass p-4 rounded-2xl border border-red-500/30 bg-red-500/10 flex flex-col gap-2.5 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-red-400 font-bold text-sm flex items-center gap-2">
              ⚠️ Warning: Still Charging on Cancelled Mandates ({reconciliation.still_charging.length})
            </span>
            <span className="text-xs text-neutral-400">Escalation & Dispute Recommended</span>
          </div>
          {reconciliation.still_charging.map((sc: any) => (
            <div key={sc.mandate_id} className="text-xs text-neutral-200 bg-red-950/40 p-3 rounded-xl border border-red-800/40 flex flex-col sm:flex-row justify-between sm:items-center gap-2">
              <div>
                <strong>{sc.merchant_name}</strong> debited ₹{sc.amount} on {sc.latest_charge_date} after cancellation was confirmed on {sc.cancel_confirmed_at}.
              </div>
              <div className="flex items-center gap-2">
                <span className="text-red-400 font-mono text-[11px] bg-red-900/40 px-2 py-0.5 rounded">Reminder #{sc.reminder_count}</span>
                <button
                  onClick={() => {
                    const m = mandates.find(x => x.id === sc.mandate_id)
                    if (m) setCancellingMandate(m)
                  }}
                  className="px-2.5 py-1 rounded bg-red-600 hover:bg-red-500 text-white font-semibold text-xs transition"
                >
                  Cancel Again
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {reconciliation?.verified_cancelled && reconciliation.verified_cancelled.length > 0 && (
        <div className="card-glass p-3.5 rounded-2xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs flex items-center gap-2.5 mb-4">
          <span className="font-bold">✓</span>
          <div>
            <strong>Verified Cancelled:</strong> Zero debits detected for {reconciliation.verified_cancelled.map((vc: any) => vc.merchant_name).join(', ')} across the statement billing period.
          </div>
        </div>
      )}

      {/* 3. HERO COMMITTED COST SECTION */}
      <section className="hero">
        <div className="big">
          <p>Committed every year across {mandates.length - cancelled.size} mandates</p>
          <div className="num">{loading ? '…' : inr(shown)}<small>/ year</small></div>
          <div className="meter" aria-hidden="true"><i style={{ width: total ? `${(keep / total) * 100}%` : '100%' }} /><b /></div>
          <div className="legend"><span>Keeping <strong>{inr(keep)}</strong></span><span>Cancelling <strong>{inr(saved)}</strong></span></div>
        </div>
        <div className="save">
          <div>
            <h2>Tick the ones you don’t want</h2>
            <p>The total updates as you choose. Nothing is cancelled until you follow the steps for each one.</p>
          </div>
          <div>
            <p>You would save</p>
            <div className="v">{inr(saved)}</div>
            <div className="acts">
              <button onClick={onCancelFlagged}>Tick all flagged</button>
              {cancelled.size > 0 && <button onClick={onClear}>Clear</button>}
            </div>
          </div>
        </div>
      </section>

      {/* 4. FILTER CHIPS */}
      <div className="chips" role="group" aria-label="Filter mandates">
        {chips.map(([k, l]) => (
          <button key={k} className="chip" aria-pressed={filter === k} onClick={() => setFilter(k)}>
            {l}<em>{counts[k] || 0}</em>
          </button>
        ))}
      </div>

      {/* 5. MANDATE LIST */}
      <div className="list">
        {rows.map(m => {
          const k = issueOf(m), cut = cancelled.has(m.id)
          const isSuggested = m.status === 'suggested_cancel'
          const isMarkedCancelled = m.status === 'cancel_confirmed_by_user'
          const isStillCharging = m.status === 'still_charging'
          const isVerifiedCancelled = m.status === 'verified_cancelled'

          return (
            <div key={m.id} className={`row ${cut || isMarkedCancelled || isVerifiedCancelled ? 'cut' : ''}`} onClick={() => onOpen(m)}>
              <input type="checkbox" checked={cut} aria-label={`Cancel ${m.merchant_name}`}
                onClick={e => e.stopPropagation()} onChange={() => onToggle(m.id)} />
              <div>
                <div className="nm flex items-center gap-2">
                  <span>{m.merchant_name}</span>
                  {isSuggested && (
                    <button
                      onClick={e => { e.stopPropagation(); setCancellingMandate(m) }}
                      className="text-[11px] font-semibold px-2 py-0.5 rounded bg-rose-600/30 text-rose-300 hover:bg-rose-600 hover:text-white transition"
                    >
                      Cancel this mandate
                    </button>
                  )}
                </div>
                <div className="ds">{m.descriptor}</div>
              </div>
              <div className="mech">{m.mechanism_name}</div>
              <div className="tg">
                {isStillCharging ? (
                  <span className="tag t-charging">Still charging!</span>
                ) : isVerifiedCancelled ? (
                  <span className="tag t-verified">Verified cancelled</span>
                ) : isMarkedCancelled ? (
                  <span className="tag t-cancelled">Marked cancelled</span>
                ) : isSuggested ? (
                  <span className="tag t-overlap">Suggested to cancel</span>
                ) : m.status === 'keep_confirmed' ? (
                  <span className="tag t-ok">Keep confirmed</span>
                ) : (
                  <span className={`tag t-${k}`}>{ISSUE_LABEL[k]}</span>
                )}
              </div>
              <div className="amt">{inr(m.annual_committed_cost)}<span>{inr(m.latest_amount)} · {m.cadence.toLowerCase()}</span></div>
            </div>
          )
        })}
        {!loading && rows.length === 0 && <div className="empty">No mandates match this filter. Choose another one above.</div>}
      </div>

      {/* 6. OVERLAP CONFIRMATION MODAL */}
      {showOverlapModal && (
        <div className="mr">
          <div className="scrim on" onClick={() => setShowOverlapModal(false)} />
          <aside className="on" role="dialog" aria-modal="true" aria-label="Review Overlap Groups" style={{ width: 'min(540px, 100%)' }}>
            <button className="x" onClick={() => setShowOverlapModal(false)} aria-label="Close">✕</button>
            <span className="tag t-overlap">Bundle Overlap Confirmation</span>
            <h3>Review Overlapping Services</h3>
            <p className="note">
              Neo4j discovered that one of your paid subscriptions bundles another active subscription. Choose which payments to keep.
            </p>

            <div className="space-y-4 my-6">
              {overlaps.map((o: any, idx: number) => {
                const pId = o.parent_mandate?.id
                const cId = o.included_mandate?.id
                return (
                  <div key={idx} className="card-glass p-4 rounded-xl border border-white/[0.08] space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="m-0 text-white font-bold text-sm">
                          {o.parent_service} ➔ {o.included_service}
                        </h4>
                        <p className="text-xs text-neutral-400 m-0 mt-1">
                          {o.path_explanation}
                        </p>
                      </div>
                      <span className="text-xs font-bold text-amber-400">Save {inr(o.potential_annual_saving)}/yr</span>
                    </div>

                    <div className="space-y-2 pt-2 border-t border-white/[0.08] text-xs">
                      {pId && (
                        <label className="flex items-center gap-2 cursor-pointer text-neutral-200">
                          <input
                            type="checkbox"
                            checked={!!selectedKept[pId]}
                            onChange={e => setSelectedKept(prev => ({ ...prev, [pId]: e.target.checked }))}
                            className="accent-indigo-500"
                          />
                          <span>Keep <strong>{o.parent_service}</strong> (Bundle)</span>
                        </label>
                      )}
                      {cId && (
                        <label className="flex items-center gap-2 cursor-pointer text-neutral-200">
                          <input
                            type="checkbox"
                            checked={!!selectedKept[cId]}
                            onChange={e => setSelectedKept(prev => ({ ...prev, [cId]: e.target.checked }))}
                            className="accent-indigo-500"
                          />
                          <span>Keep <strong>{o.included_service}</strong> (Redundant)</span>
                        </label>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            <button
              onClick={handleDecisionSubmit}
              disabled={submittingDecision}
              className="cta w-full"
            >
              {submittingDecision ? 'Saving in Neo4j...' : 'Confirm Overlap Choices'}
            </button>
          </aside>
        </div>
      )}

      {/* 7. MECHANISM-SPECIFIC CANCELLATION POPUP */}
      {cancellingMandate && (
        <div className="mr">
          <div className="scrim on" onClick={() => setCancellingMandate(null)} />
          <aside className="on" role="dialog" aria-modal="true" aria-label="Cancel Mandate Guidance">
            <button className="x" onClick={() => setCancellingMandate(null)} aria-label="Close">✕</button>
            <span className="tag t-trial">Cancellation Guidance</span>
            <h3>Cancel {cancellingMandate.merchant_name}</h3>
            <div className="ds">{cancellingMandate.descriptor}</div>

            <p className="note">
              To cancel this mandate, perform the statutory cancellation step in your banking app or merchant portal using the rail guidance below.
            </p>

            <h4>Billed via: {cancellingMandate.mechanism_name}</h4>
            <ol>
              {cancellingMandate.cancellation_steps.map((step, i) => (
                <li key={i} className="text-sm">{step}</li>
              ))}
            </ol>

            {cancellingMandate.pitfall && (
              <p className="note text-xs border border-amber-500/20 bg-amber-500/10 text-amber-200">
                <strong>Pitfall:</strong> {cancellingMandate.pitfall}
              </p>
            )}

            <div className="mt-8 space-y-3">
              <button
                onClick={handleConfirmCancelAction}
                className="cta w-full"
              >
                Confirm I Have Cancelled in App
              </button>
              <button
                onClick={() => setCancellingMandate(null)}
                className="w-full text-xs text-neutral-400 hover:text-white py-2"
              >
                Cancel / Return
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  )
}
