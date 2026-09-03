import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { ErrorBanner } from "../components/States";

export function LoginPage() {
  const { token, login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("admin@peblo.local");
  const [password, setPassword] = useState("admin-password");
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);

  if (token) return <Navigate to="/shows" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      nav("/shows");
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-page">
      <div className="login-brand">
        <span className="brand-mark" aria-hidden="true">
          P
        </span>
        Peblo desk
      </div>
      <form className="login-card-inner" onSubmit={onSubmit} aria-labelledby="login-title">
        <h1 id="login-title">Sign in</h1>
        <p className="hint">
          Seeded accounts: admin@peblo.local / admin-password · editor@peblo.local / editor-password
        </p>
        {error ? <ErrorBanner error={error} /> : null}
        <label>
          <span>Email</span>
          <input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
        </label>
        <label>
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        <p>
          <button type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Open the desk"}
          </button>
        </p>
      </form>
    </main>
  );
}
