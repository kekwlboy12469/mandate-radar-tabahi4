import React, { useState } from 'react'
import type { Finding, ReconciliationResult } from '../types'
import { inr } from '../lib/format'
import {
  X,
  Check,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Layers,
  ArrowRight,
  Shield,
  CreditCard,
  Building2
} from 'lucide-react'

interface FindingsConfirmationModalProps {
  isOpen: boolean
  onClose: () => void
  findings: Finding[]
  reconciliation?: ReconciliationResult
  onConfirmDecision: (findingId: string, keepMandateIds: string[]) => Promise<void>
}

export const FindingsConfirmationModal: React.FC<FindingsConfirmationModalProps> = ({
  isOpen,
  onClose,
  findings,
  reconciliation,
  onConfirmDecision
}) => {
  // Store selected keep IDs per finding
  const [selections, setSelections] = useState<Record<string, Set<string>>>(() => {
    const initial: Record<string, Set<string>> = {}
    findings.forEach(f => {
      // Default: keep the first or cheapest/primary mandate
      if (f.mandates && f.mandates.length > 0) {
        initial[f.finding_id] = new Set([f.mandates[0].id])
      } else {
        initial[f.finding_id] = new Set()
      }
    })
    return initial
  })

  const [savingStatus, setSavingStatus] = useState<Record<string, 'idle' | 'saving' | 'saved'>>({})

  if (!isOpen) return null

  const toggleKeep = (findingId: string, mandateId: string) => {
    setSelections(prev => {
      const current = prev[findingId] ? new Set(prev[findingId]) : new Set()
      if (current.has(mandateId)) {
        current.delete(mandateId)
      } else {
        current.add(mandateId)
      }
      return { ...prev, [findingId]: current }
    })
  }

  const handleConfirm = async (findingId: string) => {
    const keepIds = Array.from(selections[findingId] || [])
    setSavingStatus(prev => ({ ...prev, [findingId]: 'saving' }))
    try {
      await onConfirmDecision(findingId, keepIds)
      setSavingStatus(prev => ({ ...prev, [findingId]: 'saved' }))
    } catch {
      setSavingStatus(prev => ({ ...prev, [findingId]: 'idle' }))
    }
  }

  const handleConfirmAll = async () => {
    for (const f of findings) {
      const keepIds = Array.from(selections[f.finding_id] || [])
      try {
        await onConfirmDecision(f.finding_id, keepIds)
        setSavingStatus(prev => ({ ...prev, [f.finding_id]: 'saved' }))
      } catch {}
    }
    onClose()
  }

  const totalPotentialSaving = findings.reduce(
    (sum, f) => sum + (f.potential_annual_saving || 0),
    0
  )

  const stillChargingList = reconciliation?.still_charging || []
  const verifiedCancelledList = reconciliation?.verified_cancelled || []

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 text-left animate-fade-in">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/75 backdrop-blur-sm" onClick={onClose} />

      {/* Dialog Window */}
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-[#F8F5EE] border border-[#E8E1D2] rounded-3xl shadow-2xl overflow-hidden flex flex-col z-10 text-[#0F1713]">
        
        {/* Modal Header */}
        <div className="bg-[#0E2419] bg-stipple-forest border-b border-[#EEDBCA]/20 p-6 text-[#F5EEDB] flex items-start justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2DE2B5] animate-ping" />
              <span className="text-xs font-mono uppercase tracking-wider text-[#2DE2B5]">
                Neo4j Live Graph Analysis
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white mt-1">
              Recurring Spend Overlaps &amp; Redundancies
            </h2>
            <p className="text-xs text-[#BAC8BF] mt-1 max-w-xl">
              We mapped your transaction paths through corporate conglomerates, bundles, and capabilities. Select which subscriptions you want to keep.
            </p>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:block text-right">
              <div className="text-[10px] font-mono uppercase text-[#BAC8BF]">Potential Savings</div>
              <div className="text-xl font-mono font-extrabold text-[#2DE2B5]">
                {inr(totalPotentialSaving)}/yr
              </div>
            </div>

            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          
          {/* Reconciliation Alerts (If Second Statement Uploaded) */}
          {stillChargingList.length > 0 && (
            <div className="p-4 rounded-2xl bg-red-50 border border-red-200 space-y-2">
              <div className="flex items-center gap-2 text-red-800 font-bold text-xs">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <span>STILL CHARGING ALERTS DETECTED ({stillChargingList.length})</span>
              </div>
              <p className="text-xs text-red-700">
                The following mandates were marked cancelled but debits appeared outside the 3-day grace window:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                {stillChargingList.map(item => (
                  <div key={item.mandate_id} className="p-3 bg-white rounded-xl border border-red-200 text-xs">
                    <div className="font-bold text-[#0F1713]">{item.merchant_name}</div>
                    <div className="text-[11px] text-red-600 font-mono mt-0.5">
                      Debited ₹{item.amount} on {item.date} (Reminder #{item.reminder_count})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {verifiedCancelledList.length > 0 && (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 space-y-2">
              <div className="flex items-center gap-2 text-emerald-800 font-bold text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>CANCELLATION VERIFIED ({verifiedCancelledList.length})</span>
              </div>
              <p className="text-xs text-emerald-700">
                Zero subsequent charges detected across this statement. Contract successfully closed:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                {verifiedCancelledList.map(item => (
                  <div key={item.mandate_id} className="p-3 bg-white rounded-xl border border-emerald-200 text-xs">
                    <div className="font-bold text-[#0F1713]">{item.merchant_name}</div>
                    <div className="text-[11px] text-emerald-700 font-mono mt-0.5">
                      Saved ₹{item.annual_saving_realized}/year verified!
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Findings List */}
          {findings.length === 0 ? (
            <div className="p-8 text-center text-[#64756B] bg-white rounded-2xl border border-[#E8E1D2]">
              <Sparkles className="w-6 h-6 text-[#2DE2B5] mx-auto mb-2" />
              <div className="font-semibold text-sm text-[#0F1713]">No Redundant Overlaps Found</div>
              <div className="text-xs mt-1">Your recurring portfolio is clean with zero duplicate capabilities or bundles.</div>
            </div>
          ) : (
            <div className="space-y-5">
              {findings.map((f, idx) => {
                const keepSet = selections[f.finding_id] || new Set()
                const status = savingStatus[f.finding_id] || 'idle'

                const typeColor =
                  f.finding_type === 'bundle_overlap'
                    ? 'bg-blue-100 text-blue-800 border-blue-200'
                    : f.finding_type === 'duplicate_vendor'
                    ? 'bg-amber-100 text-amber-800 border-amber-200'
                    : 'bg-purple-100 text-purple-800 border-purple-200'

                const typeLabel =
                  f.finding_type === 'bundle_overlap'
                    ? 'Bundle Inclusion Overlap'
                    : f.finding_type === 'duplicate_vendor'
                    ? 'Multi-Account Duplicate Vendor'
                    : 'Capability / Tool Redundancy'

                return (
                  <div
                    key={f.finding_id || idx}
                    className="p-5 sm:p-6 rounded-3xl bg-white border border-[#E8E1D2] space-y-4 shadow-sm"
                  >
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[#E8E1D2]">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${typeColor}`}>
                            {typeLabel}
                          </span>
                          <span className="text-xs font-mono font-bold text-[#15803D]">
                            Save up to {inr(f.potential_annual_saving)}/yr
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-[#0F1713] mt-1">
                          {f.title}
                        </h3>
                        <p className="text-xs text-[#64756B] mt-0.5">{f.description}</p>
                      </div>

                      {/* Evidence Path pill */}
                      {f.evidence_path?.summary && (
                        <div className="self-start sm:self-auto p-2 bg-[#F8F5EE] border border-[#E8E1D2] rounded-xl text-[10px] font-mono text-[#0E2419]">
                          <strong className="block text-[#64756B] uppercase text-[9px]">Graph Path:</strong>
                          {f.evidence_path.summary}
                        </div>
                      )}
                    </div>

                    {/* Mandates in Overlap Choice */}
                    <div className="space-y-2">
                      <div className="text-[11px] font-mono text-[#64756B] uppercase">
                        Select which service(s) you wish to KEEP:
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {f.mandates.map(m => {
                          const isKept = keepSet.has(m.id)
                          return (
                            <div
                              key={m.id}
                              onClick={() => toggleKeep(f.finding_id, m.id)}
                              className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-start gap-3 ${
                                isKept
                                  ? 'bg-[#C6F6D5]/30 border-[#15803D]'
                                  : 'bg-[#F8F5EE] border-[#E8E1D2] opacity-80'
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={isKept}
                                onChange={() => {}}
                                className="w-4 h-4 mt-0.5 text-[#0E2419] rounded cursor-pointer accent-[#0E2419]"
                              />
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center justify-between">
                                  <span className="font-bold text-xs text-[#0F1713] truncate">
                                    {m.merchant_name}
                                  </span>
                                  <span className="font-mono text-xs font-bold text-[#0E2419]">
                                    {inr(m.annual_committed_cost)}/yr
                                  </span>
                                </div>
                                <div className="text-[11px] text-[#64756B] font-mono truncate">
                                  {m.descriptor}
                                </div>
                                <div className="flex items-center gap-1.5 mt-1.5">
                                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white border border-[#E8E1D2] text-[#64756B]">
                                    {m.mechanism}
                                  </span>
                                  {m.account_label && (
                                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white border border-[#E8E1D2] text-[#64756B]">
                                      {m.account_label}
                                    </span>
                                  )}
                                  <span
                                    className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                                      isKept
                                        ? 'bg-[#15803D] text-white'
                                        : 'bg-red-100 text-red-700'
                                    }`}
                                  >
                                    {isKept ? 'KEEP' : 'SUGGEST CANCEL'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>

                    {/* Action Bar */}
                    <div className="flex items-center justify-between pt-2 border-t border-[#E8E1D2]">
                      <div className="text-xs text-[#64756B]">
                        {keepSet.size === f.mandates.length ? (
                          <span>Keeping all services in this category.</span>
                        ) : (
                          <span>
                            {f.mandates.length - keepSet.size} redundant mandate(s) will be marked{' '}
                            <strong className="text-red-700">"suggested to cancel"</strong>.
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => handleConfirm(f.finding_id)}
                        disabled={status === 'saving'}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                          status === 'saved'
                            ? 'bg-[#15803D] text-white'
                            : 'btn-primary'
                        }`}
                      >
                        {status === 'saving' ? (
                          <span>Saving Choice...</span>
                        ) : status === 'saved' ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Choice Confirmed in Neo4j</span>
                          </>
                        ) : (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Confirm Choice</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-white border-t border-[#E8E1D2] flex flex-col sm:flex-row items-center justify-between gap-3 shrink-0">
          <div className="text-xs text-[#64756B]">
            Decisions are recorded as <code className="font-mono text-[#0E2419]">(:Decision)</code> nodes in Neo4j and anti-joined from future prompts.
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleConfirmAll}
              className="btn-primary text-xs px-5 py-2.5 font-bold cursor-pointer shadow-md flex items-center gap-1.5"
            >
              <Check className="w-4 h-4" />
              <span>Confirm All Choices &amp; Review Mandates</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl border border-[#E8E1D2] text-xs font-semibold hover:bg-[#F2EDE2] text-[#0F1713] cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
