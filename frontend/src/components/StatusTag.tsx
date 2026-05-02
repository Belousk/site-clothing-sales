import type { DeliveryStatus, OrderStatus, ProductStatus } from "../types";

interface Props {
  status: OrderStatus | DeliveryStatus | ProductStatus;
  label: string;
  kind: "order" | "delivery" | "product";
}

export default function StatusTag({ status, label, kind }: Props) {
  return <span className={`tag tag--${kind}-${status}`}>{label}</span>;
}
