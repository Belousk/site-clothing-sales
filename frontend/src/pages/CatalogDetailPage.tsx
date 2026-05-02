import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import ErrorBox from "../components/ErrorBox";
import { formatPrice } from "../utils";
import type { Product } from "../types";

export default function CatalogDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    setError(null);
    setProduct(null);
    api
      .get<Product>(`/api/catalog/${id}`)
      .then(setProduct)
      .catch((err) => setError(err instanceof ApiError ? err.detail : "Не удалось загрузить."));
  }, [id]);

  async function addToCart() {
    if (!product) return;
    setBusy(true);
    setError(null);
    try {
      await api.post("/api/cart/add", { product_id: product.id, quantity });
      navigate("/cart");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Не удалось добавить в корзину.");
    } finally {
      setBusy(false);
    }
  }

  if (error && !product) {
    return (
      <section className="section">
        <div className="container">
          <h1>Товар недоступен</h1>
          <ErrorBox message={error} />
          <p>
            <Link to="/catalog" className="btn btn--ghost">
              Вернуться в каталог
            </Link>
          </p>
        </div>
      </section>
    );
  }

  if (!product) {
    return (
      <section className="section">
        <div className="container">
          <p className="muted">Загрузка…</p>
        </div>
      </section>
    );
  }

  const canBuy = user === null || user.role === "buyer";

  return (
    <section className="section">
      <div className="container">
        <div className="product-detail">
          <div className="product-detail__image">
            {product.image_url ? (
              <img src={product.image_url} alt={product.name} />
            ) : (
              <div className="product-card__placeholder large">Без фото</div>
            )}
          </div>
          <div className="product-detail__body">
            <span className="eyebrow">{product.seller_username ?? "Продавец"}</span>
            <h1>{product.name}</h1>
            <div className="product-detail__price">{formatPrice(product.price)} ₽</div>

            {product.sizes.length > 0 && (
              <div className="muted">Размеры: {product.sizes.join(", ")}</div>
            )}

            {product.description && <p>{product.description}</p>}

            <ErrorBox message={error} />

            {canBuy ? (
              <div className="form-actions">
                <label className="qty-input">
                  <span>Количество</span>
                  <input
                    type="number"
                    min={1}
                    max={99}
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, Math.min(99, Number(e.target.value) || 1)))}
                  />
                </label>
                {user ? (
                  <button className="btn btn--primary" type="button" onClick={addToCart} disabled={busy}>
                    {busy ? "Добавляем…" : "В корзину"}
                  </button>
                ) : (
                  <Link to={`/login?next=/catalog/${product.id}`} className="btn btn--primary">
                    Войти, чтобы добавить
                  </Link>
                )}
              </div>
            ) : (
              <p className="muted">
                Покупка доступна только из аккаунта покупателя.
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
