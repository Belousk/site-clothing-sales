import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { ApiError } from "../api";
import { homeForRole, useAuth } from "../auth";
import ErrorBox from "../components/ErrorBox";
import type { UserRole } from "../types";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [role, setRole] = useState<UserRole>("buyer");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const u = await register({
        username,
        email,
        password,
        password_confirm: passwordConfirm,
        role,
      });
      navigate(homeForRole(u.role), { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Не удалось зарегистрироваться.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="section">
      <div className="container narrow">
        <div className="section-header">
          <span className="eyebrow">Регистрация</span>
          <h2>Создать аккаунт</h2>
        </div>
        <form className="form" onSubmit={onSubmit}>
          <ErrorBox message={error} />
          <label className="form-row">
            <span>Логин</span>
            <input
              type="text"
              required
              minLength={3}
              maxLength={64}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label className="form-row">
            <span>Email</span>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="form-row">
            <span>Роль</span>
            <select value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
              <option value="buyer">Покупатель</option>
              <option value="seller">Продавец</option>
            </select>
          </label>
          <label className="form-row">
            <span>Пароль</span>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <label className="form-row">
            <span>Повторите пароль</span>
            <input
              type="password"
              required
              minLength={6}
              value={passwordConfirm}
              onChange={(e) => setPasswordConfirm(e.target.value)}
            />
          </label>
          <div className="form-actions">
            <button className="btn btn--primary" type="submit" disabled={submitting}>
              {submitting ? "Создаём…" : "Создать аккаунт"}
            </button>
            <Link to="/login" className="btn btn--ghost">
              У меня уже есть
            </Link>
          </div>
        </form>
      </div>
    </section>
  );
}
