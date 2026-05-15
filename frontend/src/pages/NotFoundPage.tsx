import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section className="section">
      <div className="container">
        <h1>Страница не найдена</h1>
        <p className="muted">
          <Link to="/">Вернуться на главную</Link>
        </p>
      </div>
    </section>
  );
}
