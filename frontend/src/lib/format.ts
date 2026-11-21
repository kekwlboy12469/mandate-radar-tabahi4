export const inr = (v: number) => '₹' + Math.round(v).toLocaleString('en-IN')

export type IssueKey = 'price' | 'trial' | 'zombie' | 'overlap' | 'unk' | 'ok'

export const issueOf = (m: { flag: string; is_recognized: boolean; status?: string }): IssueKey =>
  (m.status === 'flagged_overlap' || m.status === 'suggested_cancel') ? 'overlap'
  : !m.is_recognized ? 'unk'
  : m.flag === 'PRICE_HIKE' ? 'price'
  : m.flag === 'TRIAL_CONVERTED' ? 'trial'
  : m.flag === 'UNUSED_ZOMBIE' ? 'zombie'
  : 'ok'

export const ISSUE_LABEL: Record<IssueKey, string> = {
  price: 'Price creep', trial: 'Trial trap', zombie: 'Unused', overlap: 'Bundle overlap', unk: 'Unrecognised', ok: 'Looks fine'
}
