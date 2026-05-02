import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../auth";
import type { UserRole } from "../types";

interface Props {
  roles: UserRole[];
}

export default function RequireRole({ roles }: Props) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="container" style={{ padding: "60px 0" }}>
        <p className="muted">Загрузка…</p>
      </div>
    );
  }
  if (user === null) {
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  }
  if (!roles.includes(user.role)) {
    return (
      <div className="container" style={{ padding: "60px 0" }}>
        <h1>Доступ запрещён</h1>
        <p className="muted">Эта страница доступна только для роли: {roles.join(", ")}.</p>
      </div>
    );
  }
  return <Outlet />;
}
