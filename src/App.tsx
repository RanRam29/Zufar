
import React from 'react'
import { API_BASE, health, registerUser } from './lib/api'

export default function App() {
  const [ok, setOk] = React.useState<boolean | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [msg, setMsg] = React.useState<string>('')
  const [email, setEmail] = React.useState('')
  const [fullName, setFullName] = React.useState('')
  const [password, setPassword] = React.useState('')

  React.useEffect(() => { health().then(setOk) }, [])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMsg('שולח...')
    const { ok, status, data } = await registerUser({ email, full_name: fullName || null, password })
    setLoading(false)
    setMsg(JSON.stringify({ status, ...data }, null, 2))
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src="/favicon.svg" className="w-7 h-7" alt="Z" />
            <h1 className="text-lg font-semibold">Zufar</h1>
            <span className={`pill ${ok ? 'badge-ok' : ok === false ? 'badge-err' : ''}`}>
              {ok === null ? 'בודק בריאות…' : ok ? 'בריא' : 'בעיית בריאות'}
            </span>
          </div>
          <div className="text-xs text-muted">API: {API_BASE}</div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-10">
        <section className="card">
          <h2 className="text-2xl font-bold mb-2">Onboarding / הרשמת משתמש</h2>
          <p className="text-muted mb-6">צור חשבון חדש ומחובר ל־API.</p>

          <form onSubmit={onSubmit} className="grid gap-4">
            <label className="grid gap-1">
              <span className="text-sm text-muted">אימייל</span>
              <input className="input" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@example.com" />
            </label>
            <label className="grid gap-1">
              <span className="text-sm text-muted">שם מלא</span>
              <input className="input" value={fullName} onChange={e => setFullName(e.target.value)} placeholder="שם מלא (אופציונלי)" />
            </label>
            <label className="grid gap-1">
              <span className="text-sm text-muted">סיסמה</span>
              <input className="input" type="password" required minLength={6} value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
            </label>

            <div className="flex items-center justify-between gap-3 pt-2">
              <button className="btn" type="submit" disabled={loading}>
                {loading ? 'שולח…' : 'הירשם'}
              </button>
              <span className="text-xs text-muted">* הנתונים נשלחים ל־API דרך HTTPS</span>
            </div>
          </form>

          <pre className="mt-6 bg-black/30 border border-white/10 rounded-xl p-4 text-xs whitespace-pre-wrap">{msg}</pre>
        </section>
      </main>

      <footer className="text-center text-muted py-8 text-sm">
        © {new Date().getFullYear()} Zufar · Built with React + Vite · Tailwind
      </footer>
    </div>
  )
}
