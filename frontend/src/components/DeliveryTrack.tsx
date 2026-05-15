import type { DeliveryStatus, Order } from "../types";
import { formatDateTime } from "../utils";

const STEPS: { code: DeliveryStatus; label: string; getDate: (o: Order) => string | null }[] = [
  { code: "processing", label: "Готовится к отправке", getDate: (o) => o.paid_at },
  { code: "shipped", label: "Передан в доставку", getDate: (o) => o.shipped_at },
  { code: "in_transit", label: "В пути", getDate: (o) => o.delivery_updated_at },
  { code: "delivered", label: "Доставлен", getDate: (o) => o.delivered_at },
];

const ORDER: DeliveryStatus[] = ["processing", "shipped", "in_transit", "delivered"];

export default function DeliveryTrack({ order }: { order: Order }) {
  const currentIdx = ORDER.indexOf(order.delivery_status);
  return (
    <ul className="delivery-track">
      {STEPS.map((step, i) => {
        const done = i <= currentIdx;
        const date = done ? step.getDate(order) : null;
        return (
          <li
            key={step.code}
            className={`delivery-track__step${done ? " delivery-track__step--done" : ""}`}
          >
            <div className="delivery-track__dot" />
            <div className="delivery-track__label">
              <strong>{step.label}</strong>
              <span className="muted small">{date ? formatDateTime(date) : ""}</span>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
