import React, { useState, useRef, useEffect } from 'react'
import {
  X,
  Lock,
  Mail,
  User,
  ArrowRight,
  Eye,
  EyeOff,
  Sparkles,
  Smartphone,
  CheckCircle2,
  Loader2,
  AlertCircle
} from 'lucide-react'
import { GoogleLogin } from '@react-oauth/google'
import { auth, RecaptchaVerifier, signInWithPhoneNumber, ConfirmationResult } from '../lib/firebase'

interface AuthModalProps {
  isOpen: boolean
  initialMode?: 'signin' | 'signup'
  onClose: () => void
  onSuccess: (user?: { name: string; email: string; phone?: string; isDemo?: boolean }) => void
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  initialMode = 'signin',
  onClose,
  onSuccess
}) => {
  const [tab, setTab] = useState<'signin' | 'signup' | 'phone'>(
    initialMode === 'signup' ? 'signup' : 'signin'
  )
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [toastMsg, setToastMsg] = useState<string | null>(null)

  // Phone OTP state
  const [phoneNumber, setPhoneNumber] = useState('')
  const [phoneFullName, setPhoneFullName] = useState('')
  const [otpStep, setOtpStep] = useState<'entry' | 'code'>('entry')
  const [otp, setOtp] = useState(['', '', '', '', '', ''])
  const [otpTimer, setOtpTimer] = useState(60)
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null)
  const otpRefs = useRef<(HTMLInputElement | null)[]>([])
  const recaptchaVerifierRef = useRef<RecaptchaVerifier | null>(null)

  useEffect(() => {
    if (initialMode === 'signup') {
      setTab('signup')
    } else {
      setTab('signin')
    }
  }, [initialMode, isOpen])

  useEffect(() => {
    if (toastMsg) {
      const timer = setTimeout(() => setToastMsg(null), 3500)
      return () => clearTimeout(timer)
    }
  }, [toastMsg])

  useEffect(() => {
    if (tab === 'phone' && otpStep === 'code' && otpTimer > 0) {
      const interval = setInterval(() => setOtpTimer(t => t - 1), 1000)
      return () => clearInterval(interval)
    }
  }, [tab, otpStep, otpTimer])

  useEffect(() => {
    return () => {
      if (recaptchaVerifierRef.current) {
        try { recaptchaVerifierRef.current.clear() } catch {}
        recaptchaVerifierRef.current = null
      }
    }
  }, [])

  if (!isOpen) return null

  const handleOtpChange = (idx: number, value: string) => {
    if (!/^\d*$/.test(value)) return
    const newOtp = [...otp]
    newOtp[idx] = value.slice(-1)
    setOtp(newOtp)
    if (value && idx < 5) {
      otpRefs.current[idx + 1]?.focus()
    }
  }

  const handleOtpKeyDown = (idx: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otp[idx] && idx > 0) {
      otpRefs.current[idx - 1]?.focus()
    }
  }

  // --- Email/Password Submit (Sign In & Sign Up) ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setErrorMessage('')

    try {
      if (tab === 'signup') {
        const res = await fetch('/api/v1/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            password,
            full_name: fullName.trim() || 'Account Holder'
          })
        })
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || 'Registration failed. Please check your credentials.')
        }

        if (data.access_token) {
          localStorage.setItem('mandate_radar_token', data.access_token)
        }

        const userObj = {
          id: data.user_id,
          name: data.full_name,
          email: data.email,
          phone: '',
          accountLabel: `${data.full_name.split(' ')[0]}'s Mandate Radar`,
          isDemo: false
        }
        try {
          localStorage.setItem('mandate_radar_user', JSON.stringify(userObj))
        } catch {}

        setIsLoading(false)
        setToastMsg(`Account created! Welcome, ${userObj.name}.`)
        setTimeout(() => {
          onSuccess(userObj)
        }, 300)

      } else {
        // Sign In
        const res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: email.trim().toLowerCase(),
            password
          })
        })
        const data = await res.json()
        if (!res.ok) {
          throw new Error(data.detail || 'Invalid email or password.')
        }

        if (data.access_token) {
          localStorage.setItem('mandate_radar_token', data.access_token)
        }

        const userObj = {
          id: data.user_id,
          name: data.full_name,
          email: data.email,
          phone: '',
          accountLabel: `${data.full_name.split(' ')[0]}'s Mandate Radar`,
          isDemo: false
        }
        try {
          localStorage.setItem('mandate_radar_user', JSON.stringify(userObj))
        } catch {}

        setIsLoading(false)
        setToastMsg(`Welcome back, ${userObj.name}!`)
        setTimeout(() => {
          onSuccess(userObj)
        }, 300)
      }
    } catch (err: any) {
      setIsLoading(false)
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.')
    }
  }

  // --- Real Google OAuth 2.0 Handler ---
  const handleGoogleSuccess = async (credentialResponse: any) => {
    if (!credentialResponse?.credential) {
      setErrorMessage('Google authentication did not return a valid token credential.')
      return
    }

    setIsLoading(true)
    setErrorMessage('')

    try {
      const res = await fetch('/api/v1/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          credential: credentialResponse.credential
        })
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Google authentication failed.')
      }

      if (data.access_token) {
        localStorage.setItem('mandate_radar_token', data.access_token)
      }

      const userObj = {
        id: data.user_id,
        name: data.full_name,
        email: data.email,
        phone: '',
        accountLabel: `${data.full_name.split(' ')[0]}'s Mandate Radar`,
        isDemo: false
      }
      try {
        localStorage.setItem('mandate_radar_user', JSON.stringify(userObj))
      } catch {}

      setIsLoading(false)
      setToastMsg(`Signed in as ${userObj.name}!`)
      setTimeout(() => {
        onSuccess(userObj)
      }, 300)
    } catch (err: any) {
      setIsLoading(false)
      setErrorMessage(err.message || 'Failed to authenticate Google account.')
    }
  }

  // --- 1-Click Instant Demo Session ---
  const handleDemoLogin = () => {
    setToastMsg('Launching demo session (Arun Sharma)...')
    setTimeout(() => {
      onSuccess({
        name: 'Arun Sharma',
        email: 'arun.sharma@example.com',
        phone: '+91 98201 48210',
        isDemo: true
      })
    }, 300)
  }

  // --- Phone Auth Step 1: Send Code ---
  const handleSendPhoneOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    const clean = phoneNumber.replace(/\D/g, '')
    if (clean.length < 10) {
      setErrorMessage('Please enter a valid 10-digit Indian mobile number.')
      return
    }

    setIsLoading(true)
    setErrorMessage('')

    try {
      if (!recaptchaVerifierRef.current) {
        recaptchaVerifierRef.current = new RecaptchaVerifier(auth, 'firebase-recaptcha-container', {
          size: 'invisible'
        })
      }

      const fullE164Phone = `+91${clean.slice(-10)}`
      const confirmation = await signInWithPhoneNumber(auth, fullE164Phone, recaptchaVerifierRef.current)
      setConfirmationResult(confirmation)
      setOtp(['', '', '', '', '', ''])
      setOtpTimer(60)
      setOtpStep('code')
      setIsLoading(false)
      setToastMsg(`Verification code sent to ${fullE164Phone}`)
    } catch (err: any) {
      console.error('Firebase phone auth error:', err)
      setIsLoading(false)
      if (recaptchaVerifierRef.current) {
        try { recaptchaVerifierRef.current.clear() } catch {}
        recaptchaVerifierRef.current = null
      }
      const code = err?.code || ''
      let msg = err?.message || 'Failed to dispatch SMS verification code.'
      if (code === 'auth/unauthorized-domain') {
        msg = `Domain "${window.location.hostname}" is not authorized in Firebase Console.`
      } else if (code === 'auth/billing-not-enabled' || code === 'auth/quota-exceeded') {
        msg = 'Carrier SMS quota reached. Please use a Firebase Test Number (e.g. +91 9999999999).'
      }
      setErrorMessage(msg)
    }
  }

  // --- Phone Auth Step 2: Verify Code ---
  const handleVerifyPhoneOtp = async (e: React.FormEvent) => {
    e.preventDefault()
    const code = otp.join('')
    if (code.length !== 6) {
      setErrorMessage('Please enter the full 6-digit verification code.')
      return
    }

    if (!confirmationResult) {
      setErrorMessage('Verification session expired. Please request a new code.')
      setOtpStep('entry')
      return
    }

    setIsLoading(true)
    setErrorMessage('')

    try {
      const userCredential = await confirmationResult.confirm(code)
      const idToken = await userCredential.user.getIdToken()

      const res = await fetch('/api/v1/auth/phone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          idToken,
          full_name: phoneFullName.trim() || undefined
        })
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Phone authentication failed on server.')
      }

      if (data?.access_token) {
        localStorage.setItem('mandate_radar_token', data.access_token)
      }

      const userObj = {
        id: data.user_id,
        name: data.full_name,
        email: data.email,
        phone: `+91 ${phoneNumber.replace(/\D/g, '').slice(-10)}`,
        accountLabel: `${data.full_name.split(' ')[0]}'s Mandate Radar`,
        isDemo: false
      }
      try {
        localStorage.setItem('mandate_radar_user', JSON.stringify(userObj))
      } catch {}

      setIsLoading(false)
      setToastMsg(`Verified! Welcome ${userObj.name}.`)
      setTimeout(() => {
        onSuccess(userObj)
      }, 300)
    } catch (err: any) {
      setIsLoading(false)
      setErrorMessage(err.message || 'Invalid or expired verification code. Please retry.')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in text-left">
      <div id="firebase-recaptcha-container"></div>

      <div className="relative w-full max-w-[440px] bg-[#07110C] border border-[rgba(238,219,202,0.2)] rounded-[32px] p-6 sm:p-8 shadow-2xl text-[#FAF8F5]">
        
        {/* Floating Toast */}
        {toastMsg && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-[#2DE2B5] text-[#07110C] font-semibold text-xs shadow-xl animate-fade-in whitespace-nowrap">
            <CheckCircle2 className="w-4 h-4 text-[#07110C] shrink-0" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/80 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#143323] border border-[#2DE2B5]/30 text-[#2DE2B5] text-xs font-mono font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            <span>MANDATE RADAR</span>
          </div>
          <h2 className="text-xl font-bold tracking-tight text-white">
            {tab === 'signup' ? 'Create Your Account' : tab === 'phone' ? 'Phone Verification' : 'Welcome Back'}
          </h2>
          <p className="text-xs text-[#9BAEA2] mt-1">
            {tab === 'signup'
              ? 'Unmask recurring subscriptions and parent conglomerate exposure.'
              : tab === 'phone'
              ? 'Sign in securely with instant phone authentication.'
              : 'Sign in to access your portfolio radar and recurring auto-debits.'}
          </p>
        </div>

        {/* Clean Auth Tabs (Sign In | Create Account | Phone) */}
        <div className="flex p-1 bg-[#0E1F17] border border-white/10 rounded-xl mb-5">
          <button
            type="button"
            onClick={() => { setTab('signin'); setErrorMessage('') }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              tab === 'signin'
                ? 'bg-[#2DE2B5] text-[#07110C] shadow-sm font-bold'
                : 'text-[#9BAEA2] hover:text-white'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('signup'); setErrorMessage('') }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              tab === 'signup'
                ? 'bg-[#2DE2B5] text-[#07110C] shadow-sm font-bold'
                : 'text-[#9BAEA2] hover:text-white'
            }`}
          >
            Create Account
          </button>
          <button
            type="button"
            onClick={() => { setTab('phone'); setErrorMessage('') }}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              tab === 'phone'
                ? 'bg-[#2DE2B5] text-[#07110C] shadow-sm font-bold'
                : 'text-[#9BAEA2] hover:text-white'
            }`}
          >
            Phone
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* TAB 1 & 2: Email & Password (Sign In / Create Account) */}
        {tab !== 'phone' ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            {tab === 'signup' && (
              <div>
                <label className="block text-xs font-medium text-[#EEDBCA] mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9BAEA2]" />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={e => setFullName(e.target.value)}
                    placeholder="e.g. Rahul Sharma"
                    className="w-full pl-10 pr-4 py-2.5 text-xs bg-[#0E1F17] border border-white/15 text-white rounded-xl focus:border-[#2DE2B5] focus:outline-none transition-colors"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[#EEDBCA] mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9BAEA2]" />
                <input
                  type="email"
                  required
                  autoFocus={tab === 'signin'}
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-10 pr-4 py-2.5 text-xs bg-[#0E1F17] border border-white/15 text-white rounded-xl focus:border-[#2DE2B5] focus:outline-none transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[#EEDBCA] mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9BAEA2]" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-2.5 text-xs bg-[#0E1F17] border border-white/15 text-white rounded-xl focus:border-[#2DE2B5] focus:outline-none transition-colors font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9BAEA2] hover:text-white transition-colors cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Glowing Submit Button */}
            <button
              type="submit"
              disabled={isLoading || !email || !password}
              className="w-full h-11 bg-[#2DE2B5] text-[#07110C] font-bold text-sm rounded-xl hover:brightness-105 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-[#2DE2B5]/20 cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#07110C]" />
                  <span>{tab === 'signup' ? 'Creating Account...' : 'Signing In...'}</span>
                </>
              ) : (
                <>
                  <span>{tab === 'signup' ? 'Create Free Account' : 'Sign In'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>

            {/* Google OAuth Section */}
            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10" />
              </div>
              <div className="relative flex justify-center text-[11px] uppercase tracking-wider">
                <span className="bg-[#07110C] px-2 text-[#9BAEA2]">Or continue with</span>
              </div>
            </div>

            <div className="flex justify-center">
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => {
                  setErrorMessage('Google Sign-In was cancelled or failed.')
                }}
                theme="filled_black"
                shape="pill"
                size="large"
                text="continue_with"
                width="340"
              />
            </div>

            {/* 1-Click Instant Demo Button */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleDemoLogin}
                className="w-full py-2.5 px-3 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 text-xs text-[#EEDBCA] flex items-center justify-center gap-2 transition-all cursor-pointer font-medium"
              >
                <Sparkles className="w-4 h-4 text-[#2DE2B5]" />
                <span>Explore Sample Portfolio (Instant Demo Mode)</span>
              </button>
            </div>
          </form>
        ) : (
          /* TAB 3: Phone Sign-In (Firebase) */
          <div>
            {otpStep === 'entry' ? (
              <form onSubmit={handleSendPhoneOtp} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-[#EEDBCA] mb-1.5">
                    Mobile Phone Number (India)
                  </label>
                  <div className="flex gap-2">
                    <div className="w-14 px-3 py-2.5 text-xs bg-[#0E1F17] border border-white/15 text-[#9BAEA2] font-mono rounded-xl flex items-center justify-center">
                      +91
                    </div>
                    <input
                      type="tel"
                      required
                      autoFocus
                      maxLength={10}
                      value={phoneNumber}
                      onChange={e => setPhoneNumber(e.target.value.replace(/\D/g, ''))}
                      placeholder="98765 43210"
                      className="flex-1 px-3.5 py-2.5 text-xs bg-[#0E1F17] border border-white/15 text-white rounded-xl focus:border-[#2DE2B5] focus:outline-none font-mono"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#EEDBCA] mb-1.5">
                    Full Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={phoneFullName}
                    onChange={e => setPhoneFullName(e.target.value)}
                    placeholder="e.g. Rahul Sharma"
                    className="w-full px-3.5 py-2.5 text-xs bg-[#0E1F17] border border-white/15 text-white rounded-xl focus:border-[#2DE2B5] focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || phoneNumber.replace(/\D/g, '').length < 10}
                  className="w-full h-11 bg-[#2DE2B5] text-[#07110C] font-bold text-sm rounded-xl hover:brightness-105 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-[#2DE2B5]/20 cursor-pointer"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-[#07110C]" />
                      <span>Sending Code...</span>
                    </>
                  ) : (
                    <>
                      <span>Send Verification Code</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            ) : (
              /* OTP Code Step */
              <form onSubmit={handleVerifyPhoneOtp} className="space-y-4">
                <div className="text-center mb-2">
                  <p className="text-xs text-[#9BAEA2]">
                    Enter the 6-digit verification code sent to <strong className="text-white">+91 {phoneNumber}</strong>
                  </p>
                </div>

                <div className="flex gap-2 justify-center">
                  {otp.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={el => (otpRefs.current[idx] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={e => handleOtpChange(idx, e.target.value)}
                      onKeyDown={e => handleOtpKeyDown(idx, e)}
                      className="w-10 h-12 text-center font-mono font-bold text-lg bg-[#0E1F17] border border-white/15 text-white rounded-xl focus:border-[#2DE2B5] focus:outline-none"
                    />
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={isLoading || otp.join('').length !== 6}
                  className="w-full h-11 bg-[#2DE2B5] text-[#07110C] font-bold text-sm rounded-xl hover:brightness-105 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-[#2DE2B5]/20 cursor-pointer"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin text-[#07110C]" />
                      <span>Verifying...</span>
                    </>
                  ) : (
                    <span>Verify &amp; Continue</span>
                  )}
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => { setOtpStep('entry'); setErrorMessage('') }}
                    className="text-xs text-[#9BAEA2] hover:text-white cursor-pointer"
                  >
                    Change phone number
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
