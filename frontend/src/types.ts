export type BillingType = 'fixed' | 'usage_based'

export type MandateStatus =
  | 'active'
  | 'flagged'
  | 'keep_confirmed'
  | 'suggested_cancel'
  | 'marked_cancelled'
  | 'verified_cancelled'
  | 'still_charging'

export interface ChargeHistory {
  id: string
  date: string
  amount: number
  descriptor: string
}

export interface Mandate {
  id: string
  merchant_id?: string
  merchant_name: string
  category?: string
  parent_id?: string
  parent_name?: string
  descriptor: string
  is_recognized: boolean
  cadence: 'MONTHLY' | 'ANNUAL' | 'QUARTERLY' | 'WEEKLY' | string
  latest_amount: number
  initial_amount?: number
  annual_committed_cost: number
  charge_count: number
  first_seen: string
  last_charged: string
  mechanism: string
  mechanism_name: string
  flag: 'HEALTHY' | 'PRICE_HIKE' | 'TRIAL_CONVERTED' | 'UNUSED_ZOMBIE' | string
  flag_reason?: string
  confidence_score?: number
  savings_if_cancelled?: number
  pitfall?: string
  support_email?: string
  cancellation_steps: string[]
  history: ChargeHistory[]
  status?: MandateStatus
  marked_cancelled_on?: string
  verified_cancelled_on?: string
  reminder_count?: number
  billing_type?: BillingType
  account_label?: string
  account_id?: string
  tags?: string[]
}

export interface GraphEvidence {
  nodes: Array<{ id: string; label: string; [key: string]: any }>
  relationships: Array<{ type: string; from: string; to: string; [key: string]: any }>
  summary?: string
}

export interface Finding {
  finding_id: string
  finding_type: 'bundle_overlap' | 'capability_overlap' | 'duplicate_vendor' | 'price_creep' | 'zombie'
  title: string
  description: string
  mandates: Mandate[]
  potential_annual_saving: number
  evidence_path?: GraphEvidence
  status?: 'pending' | 'resolved'
  chosen_action?: string
  confirmed_mandate_ids?: string[]
}

export interface ReconciliationResult {
  still_charging: Array<{
    mandate_id: string
    merchant_name: string
    descriptor: string
    amount: number
    date: string
    charge_count: number
    marked_cancelled_on: string
    reminder_count: number
    action_required: string
  }>
  verified_cancelled: Array<{
    mandate_id: string
    merchant_name: string
    descriptor: string
    marked_cancelled_on: string
    verified_on: string
    annual_saving_realized: number
  }>
  pending_verification: Array<{
    mandate_id: string
    merchant_name: string
    marked_cancelled_on: string
    days_since_cancellation: number
  }>
}

export interface StatementUploadResponse {
  success: boolean
  account_label: string
  mandates_found: number
  mandates: Mandate[]
  findings: Finding[]
  reconciliation: ReconciliationResult
  potential_annual_savings: number
  message?: string
}

export interface SpendConcentration {
  total_spend: number
  by_category: Record<string, number>
  by_vendor: Record<string, number>
  by_account: Record<string, number>
  by_tag: Record<string, number>
  by_mechanism: Record<string, number>
  by_billing_type: Record<string, number>
}
