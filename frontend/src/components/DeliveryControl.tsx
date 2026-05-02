import { useState } from "react";

import { api, ApiError } from "../api";
import type { DeliveryStatus, Order } from "../types";
import ErrorBox from "./ErrorBox";

const ORDER: DeliveryStatus[] = ["processing", "shipped", "in_transit", "delivered"];
const LABELS: Record<DeliveryStatus, string> = {
  processing: "Готовится к отправке",
  shipped: "Передан в доставку",
  in_transit: "В пути",
  delivered: "Доставлен",
};

interface Props {
  order: Order;
  onUpdated: (o: Order) => void;
  endpoint: (orderId: number) => string;
}

export default function DeliveryControl({ order, onUpdated, endpoint }: Props) {
  const currentIdx = ORDER.indexOf(order.delivery_status);
  const choices = ORDER.slice(currentIdx + 1);
  const [target, setTarget] = useState<DeliveryStatus | "">(choices[0] ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (choices.length === 0) {
    return <p className="muted small">Доставлен — конечный статус.</p>;
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!target) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api.post<Order>(endpoint(order.id), { delivery_status: target });
      onUpdated(updated);
      const next = ORDER.indexOf(updated.delivery_status) + 1;
      setTarget((ORDER[next] as DeliveryStatus) ?? "");
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Не удалось обновить статус.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="delivery-control" onSubmit={submit}>
      <ErrorBox message={error} />
      <label>
        <span className="muted small">Передвинуть статус</span>
        <select
          value={target}
          onChange={(e) => setTarget(e.target.value as DeliveryStatus)}
          disabled={busy}
        >
          {choices.map((c) => (
            <option key={c} value={c}>
              {LABELS[c]}
            </option>
          ))}
        </select>
      </label>
      <button className="btn btn--primary btn--small" type="submit" disabled={busy || !target}>
        {busy ? "Обновляем…" : "Обновить"}
      </button>
    </form>
  );
}
