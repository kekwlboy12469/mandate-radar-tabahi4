import type { Mandate } from '../App'

export const SAMPLE_MANDATES: Mandate[] = [
  {
    id: 'mand-spotify',
    merchant_id: 'merch-spotify',
    merchant_name: 'Spotify Premium Individual',
    category: 'Audio Streaming',
    parent_id: 'parent-spotify',
    parent_name: 'Spotify AB',
    descriptor: 'UPI/P2M/23849182/SPOTIFY/SI',
    is_recognized: true,
    cadence: 'ANNUAL',
    latest_amount: 1199,
    initial_amount: 999,
    annual_committed_cost: 1199,
    charge_count: 2,
    first_seen: '2024-09-12',
    last_charged: '2025-09-12',
    mechanism: 'UPI_AUTOPAY',
    mechanism_name: 'UPI Autopay (HDFC Bank)',
    flag: 'PRICE_HIKE',
    flag_reason: 'Annual renewal price increased from ₹999 to ₹1,199 (+20% / +12% YoY baseline).',
    confidence_score: 0.98,
    savings_if_cancelled: 1199,
    pitfall: 'Silent renewal debit without pre-debit SMS warning on older UPI handle.',
    support_email: 'support@spotify.com',
    cancellation_steps: [
      'Open BHIM / PhonePe / GPay app linked to HDFC Bank.',
      'Navigate to Profile > Autopay / Mandates.',
      'Locate "Spotify India Pvt Ltd" mandate.',
      'Tap "Pause" or "Cancel Mandate" and authenticate with UPI PIN.'
    ],
    history: [
      { id: 'tx-sp-1', date: '2024-09-12', amount: 999, descriptor: 'UPI/P2M/23849182/SPOTIFY/SI' },
      { id: 'tx-sp-2', date: '2025-09-12', amount: 1199, descriptor: 'UPI/P2M/23849182/SPOTIFY/SI' }
    ]
  },
  {
    id: 'mand-netflix',
    merchant_id: 'merch-netflix',
    merchant_name: 'Netflix Standard (HD)',
    category: 'Video Streaming',
    parent_id: 'parent-netflix',
    parent_name: 'Netflix Inc',
    descriptor: 'NETFLIX-MUM-SI-49102-CARD',
    is_recognized: true,
    cadence: 'MONTHLY',
    latest_amount: 649,
    initial_amount: 649,
    annual_committed_cost: 7788,
    charge_count: 14,
    first_seen: '2024-07-04',
    last_charged: '2025-10-04',
    mechanism: 'CARD_SI',
    mechanism_name: 'Card Standing Instruction (ICICI Coral)',
    flag: 'UNUSED_ZOMBIE',
    flag_reason: 'Account linked with 0 login events in last 90 days. High zombie bleed.',
    confidence_score: 0.99,
    savings_if_cancelled: 7788,
    pitfall: 'Credit card e-mandate continues cycling even if mobile app is uninstalled.',
    support_email: 'support@netflix.com',
    cancellation_steps: [
      'Go to netflix.com/youraccount in mobile/desktop browser.',
      'Click "Cancel Membership" under Membership & Billing.',
      'Alternatively, visit ICICI NetBanking > Cards > Recurring Transactions > Revoke SI.'
    ],
    history: [
      { id: 'tx-nf-1', date: '2025-08-04', amount: 649, descriptor: 'NETFLIX-MUM-SI-49102' },
      { id: 'tx-nf-2', date: '2025-09-04', amount: 649, descriptor: 'NETFLIX-MUM-SI-49102' },
      { id: 'tx-nf-3', date: '2025-10-04', amount: 649, descriptor: 'NETFLIX-MUM-SI-49102' }
    ]
  },
  {
    id: 'mand-youtube',
    merchant_id: 'merch-youtube',
    merchant_name: 'YouTube Premium Family',
    category: 'Video & Music',
    parent_id: 'parent-alphabet',
    parent_name: 'Alphabet Inc',
    descriptor: 'GOOGLE*YOUTUBE G.CO/HELPPAY# IN',
    is_recognized: true,
    cadence: 'MONTHLY',
    latest_amount: 189,
    initial_amount: 189,
    annual_committed_cost: 2268,
    charge_count: 12,
    first_seen: '2024-10-18',
    last_charged: '2025-10-18',
    mechanism: 'PLAY_STORE',
    mechanism_name: 'Google Play Store Subscription',
    flag: 'HEALTHY',
    flag_reason: 'Active user activity across 4 family members.',
    confidence_score: 0.96,
    savings_if_cancelled: 2268,
    pitfall: 'Charges Google India Digital Services Pvt Ltd on CC statement.',
    support_email: 'support-in@google.com',
    cancellation_steps: [
      'Open Play Store app on Android device.',
      'Tap Profile icon > Payments & subscriptions > Subscriptions.',
      'Select YouTube Premium and tap "Cancel subscription".'
    ],
    history: [
      { id: 'tx-yt-1', date: '2025-08-18', amount: 189, descriptor: 'GOOGLE*YOUTUBE G.CO/HELPPAY#' },
      { id: 'tx-yt-2', date: '2025-09-18', amount: 189, descriptor: 'GOOGLE*YOUTUBE G.CO/HELPPAY#' },
      { id: 'tx-yt-3', date: '2025-10-18', amount: 189, descriptor: 'GOOGLE*YOUTUBE G.CO/HELPPAY#' }
    ]
  },
  {
    id: 'mand-prime',
    merchant_id: 'merch-prime',
    merchant_name: 'Amazon Prime Annual',
    category: 'Ecommerce & Streaming',
    parent_id: 'parent-amazon',
    parent_name: 'Amazon.com Inc',
    descriptor: 'AMAZON PAY INDIA PRIME MANDATE',
    is_recognized: true,
    cadence: 'ANNUAL',
    latest_amount: 1499,
    initial_amount: 1499,
    annual_committed_cost: 1499,
    charge_count: 3,
    first_seen: '2023-11-20',
    last_charged: '2024-11-20',
    mechanism: 'CARD_SI',
    mechanism_name: 'Card SI (HDFC Millennia)',
    flag: 'HEALTHY',
    flag_reason: 'Frequent deliveries and active Prime Video streaming.',
    confidence_score: 0.97,
    savings_if_cancelled: 1499,
    pitfall: 'Annual auto-charge requires opt-out 48 hrs before renewal window.',
    support_email: 'cis@amazon.in',
    cancellation_steps: [
      'Open Amazon App > Your Account > Manage Prime Membership.',
      'Select "End Membership" or visit HDFC e-mandate portal to revoke.'
    ],
    history: [
      { id: 'tx-amz-1', date: '2024-11-20', amount: 1499, descriptor: 'AMAZON PAY INDIA PRIME' }
    ]
  },
  {
    id: 'mand-audible',
    merchant_id: 'merch-audible',
    merchant_name: 'Audible India Monthly',
    category: 'Audiobooks',
    parent_id: 'parent-amazon',
    parent_name: 'Amazon.com Inc',
    descriptor: 'AUDIBLE*IN RECURRING MUMBAI',
    is_recognized: true,
    cadence: 'MONTHLY',
    latest_amount: 199,
    initial_amount: 199,
    annual_committed_cost: 2388,
    charge_count: 8,
    first_seen: '2025-02-14',
    last_charged: '2025-10-14',
    mechanism: 'CARD_SI',
    mechanism_name: 'Card SI (ICICI Bank)',
    flag: 'UNUSED_ZOMBIE',
    flag_reason: '5 unspent audio credits accumulated. Zero hours listened in 4 months.',
    confidence_score: 0.95,
    savings_if_cancelled: 2388,
    pitfall: 'Cancelling before spending credits forfeits existing credit balance.',
    support_email: 'customersupport@audible.in',
    cancellation_steps: [
      'Go to audible.in/account/overview in browser (not app).',
      'Click "Cancel membership" at bottom of page.',
      'Spend remaining 5 credits before final confirmation.'
    ],
    history: [
      { id: 'tx-aud-1', date: '2025-08-14', amount: 199, descriptor: 'AUDIBLE*IN RECURRING' },
      { id: 'tx-aud-2', date: '2025-09-14', amount: 199, descriptor: 'AUDIBLE*IN RECURRING' },
      { id: 'tx-aud-3', date: '2025-10-14', amount: 199, descriptor: 'AUDIBLE*IN RECURRING' }
    ]
  },
  {
    id: 'mand-hotstar',
    merchant_id: 'merch-hotstar',
    merchant_name: 'Disney+ Hotstar Super',
    category: 'Video Streaming',
    parent_id: 'parent-disney',
    parent_name: 'The Walt Disney Company',
    descriptor: 'NOVI DIGITAL ENTERTAINMENT UPI',
    is_recognized: true,
    cadence: 'ANNUAL',
    latest_amount: 899,
    initial_amount: 899,
    annual_committed_cost: 899,
    charge_count: 1,
    first_seen: '2025-04-10',
    last_charged: '2025-04-10',
    mechanism: 'UPI_AUTOPAY',
    mechanism_name: 'UPI Autopay (Axis Bank)',
    flag: 'TRIAL_CONVERTED',
    flag_reason: 'Auto-converted from promo ICC World Cup trial into annual recurring mandate.',
    confidence_score: 0.94,
    savings_if_cancelled: 899,
    pitfall: 'Shows under billing legal entity "NOVI DIGITAL" rather than Hotstar.',
    support_email: 'subscription@hotstar.com',
    cancellation_steps: [
      'Open Axis Mobile or UPI App > Autopay Mandates.',
      'Search for "Novi Digital Entertainment Pvt Ltd".',
      'Click "Revoke Mandate" and enter UPI PIN.'
    ],
    history: [
      { id: 'tx-hs-1', date: '2025-04-10', amount: 899, descriptor: 'NOVI DIGITAL ENTERTAINMENT UPI' }
    ]
  },
  {
    id: 'mand-cult',
    merchant_id: 'merch-cult',
    merchant_name: 'Cult.fit Pass Elite',
    category: 'Fitness & Health',
    parent_id: 'parent-cult',
    parent_name: 'Curefit Healthcare Pvt Ltd',
    descriptor: 'CUREFIT NACH DEBIT BLR 98124',
    is_recognized: true,
    cadence: 'MONTHLY',
    latest_amount: 1750,
    initial_amount: 1750,
    annual_committed_cost: 21000,
    charge_count: 6,
    first_seen: '2025-04-01',
    last_charged: '2025-10-01',
    mechanism: 'NACH',
    mechanism_name: 'NACH e-Mandate (HDFC Salary A/C)',
    flag: 'UNUSED_ZOMBIE',
    flag_reason: 'Last gym workout check-in was 78 days ago. Monthly automated deduction.',
    confidence_score: 0.97,
    savings_if_cancelled: 21000,
    pitfall: 'NACH mandates require formal bank stop-payment or merchant cancellation.',
    support_email: 'hello@cult.fit',
    cancellation_steps: [
      'Open Cult.fit app > Profile > Memberships.',
      'Tap "Pause Membership" or "Request Cancellation".',
      'Visit HDFC NetBanking > Accounts > Transact > Stop Payment / Mandate Cancel.'
    ],
    history: [
      { id: 'tx-cf-1', date: '2025-08-01', amount: 1750, descriptor: 'CUREFIT NACH DEBIT' },
      { id: 'tx-cf-2', date: '2025-09-01', amount: 1750, descriptor: 'CUREFIT NACH DEBIT' },
      { id: 'tx-cf-3', date: '2025-10-01', amount: 1750, descriptor: 'CUREFIT NACH DEBIT' }
    ]
  },
  {
    id: 'mand-chatgpt',
    merchant_id: 'merch-chatgpt',
    merchant_name: 'ChatGPT Plus Subscription',
    category: 'AI & Developer Tools',
    parent_id: 'parent-openai',
    parent_name: 'OpenAI LLC',
    descriptor: 'OPENAI *CHATGPT SUBSCRIPTION CA',
    is_recognized: true,
    cadence: 'MONTHLY',
    latest_amount: 1999,
    initial_amount: 1999,
    annual_committed_cost: 23988,
    charge_count: 10,
    first_seen: '2024-12-05',
    last_charged: '2025-10-05',
    mechanism: 'CARD_SI',
    mechanism_name: 'International Card SI (Axis Bank)',
    flag: 'HEALTHY',
    flag_reason: 'Daily productivity usage. Standard $20/month + GST conversion.',
    confidence_score: 0.99,
    savings_if_cancelled: 23988,
    pitfall: 'Subject to 3.5% foreign currency markup unless billed via Stripe INR.',
    support_email: 'support@openai.com',
    cancellation_steps: [
      'Visit chat.openai.com > Click profile name at bottom left.',
      'Select "My Plan" > "Manage my subscription".',
      'Click "Cancel Plan" on Stripe billing customer portal.'
    ],
    history: [
      { id: 'tx-gpt-1', date: '2025-08-05', amount: 1999, descriptor: 'OPENAI *CHATGPT SUBSCRIPTION' },
      { id: 'tx-gpt-2', date: '2025-09-05', amount: 1999, descriptor: 'OPENAI *CHATGPT SUBSCRIPTION' },
      { id: 'tx-gpt-3', date: '2025-10-05', amount: 1999, descriptor: 'OPENAI *CHATGPT SUBSCRIPTION' }
    ]
  },
  {
    id: 'mand-canva',
    merchant_id: 'merch-canva',
    merchant_name: 'Canva Pro Annual',
    category: 'Design & Graphics',
    parent_id: 'parent-canva',
    parent_name: 'Canva Pty Ltd',
    descriptor: 'CANVA*PRO SUBSCRIPTION SYDNEY',
    is_recognized: true,
    cadence: 'ANNUAL',
    latest_amount: 3899,
    initial_amount: 3899,
    annual_committed_cost: 3899,
    charge_count: 2,
    first_seen: '2024-03-22',
    last_charged: '2025-03-22',
    mechanism: 'CARD_SI',
    mechanism_name: 'Card SI (ICICI Bank)',
    flag: 'HEALTHY',
    flag_reason: 'Actively used for marketing collateral and decks.',
    confidence_score: 0.97,
    savings_if_cancelled: 3899,
    pitfall: 'Requires cancellation 7 days before annual billing cycle.',
    support_email: 'support@canva.com',
    cancellation_steps: [
      'Log into canva.com > Account settings > Billing & plans.',
      'Under "Subscriptions for your team", click "Cancel plan".'
    ],
    history: [
      { id: 'tx-can-1', date: '2025-03-22', amount: 3899, descriptor: 'CANVA*PRO SUBSCRIPTION' }
    ]
  },
  {
    id: 'mand-truecaller',
    merchant_id: 'merch-truecaller',
    merchant_name: 'Truecaller Premium Connect',
    category: 'Communication',
    parent_id: 'parent-truecaller',
    parent_name: 'Truecaller AB',
    descriptor: 'GOOGLE*TRUECALLER G.CO/HELPPAY',
    is_recognized: true,
    cadence: 'ANNUAL',
    latest_amount: 695,
    initial_amount: 695,
    annual_committed_cost: 695,
    charge_count: 1,
    first_seen: '2025-01-15',
    last_charged: '2025-01-15',
    mechanism: 'PLAY_STORE',
    mechanism_name: 'Google Play Store Subscription',
    flag: 'HEALTHY',
    flag_reason: 'Spam call blocking active daily.',
    confidence_score: 0.95,
    savings_if_cancelled: 695,
    pitfall: 'Auto-renews through Google Play balance or linked UPI.',
    support_email: 'support@truecaller.com',
    cancellation_steps: [
      'Open Google Play Store > Subscriptions > Truecaller > Cancel.'
    ],
    history: [
      { id: 'tx-tc-1', date: '2025-01-15', amount: 695, descriptor: 'GOOGLE*TRUECALLER G.CO/HELPPAY' }
    ]
  }
]

export const SAMPLE_HERO_METRICS = {
  annual_committed_total: 65623,
  monthly_equivalent: 5468,
  potential_savings: 31176, // Netflix (7788) + Audible (2388) + Cult.fit (21000)
  total_mandates_found: 10,
  flagged_issues_count: 5 // 3 zombies + 1 price hike + 1 trial trap
}
