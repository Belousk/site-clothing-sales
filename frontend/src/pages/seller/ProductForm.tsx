import { useState } from "react";

import { ApiError } from "../../api";
import ErrorBox from "../../components/ErrorBox";

interface SizeStockEntry {
  size: string;
  stock: string;
}

interface Props {
  initial?: {
    name: string;
    price: string;
    description: string;
    sizeStocks: SizeStockEntry[];
    imageUrl: string | null;
  };
  submitLabel: string;
  onSubmit: (form: FormData) => Promise<void>;
  showRemoveImage?: boolean;
}

export default function ProductForm({ initial, submitLabel, onSubmit, showRemoveImage }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [price, setPrice] = useState(initial?.price ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [sizeStocks, setSizeStocks] = useState<SizeStockEntry[]>(
    initial?.sizeStocks?.length ? initial.sizeStocks : [{ size: "", stock: "0" }],
  );
  const [removeImage, setRemoveImage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function addRow() {
    setSizeStocks([...sizeStocks, { size: "", stock: "0" }]);
  }

  function removeRow(idx: number) {
    setSizeStocks(sizeStocks.filter((_, i) => i !== idx));
  }

  function updateRow(idx: number, field: "size" | "stock", value: string) {
    setSizeStocks(sizeStocks.map((entry, i) => (i === idx ? { ...entry, [field]: value } : entry)));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const form = new FormData(e.currentTarget);
      const file = form.get("image");
      if (file instanceof File && file.size === 0) {
        form.delete("image");
      }
      // Build size_stocks JSON from the rows
      const sizeStocksMap: Record<string, number> = {};
      for (const entry of sizeStocks) {
        const s = entry.size.trim();
        if (s) {
          sizeStocksMap[s] = Math.max(0, parseInt(entry.stock, 10) || 0);
        }
      }
      form.set("size_stocks", JSON.stringify(sizeStocksMap));
      // Remove individual form fields that were replaced
      form.delete("sizes");
      form.delete("stock");
      await onSubmit(form);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Не удалось сохранить.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit} encType="multipart/form-data">
      <ErrorBox message={error} />

      <label className="form-row">
        <span>Название</span>
        <input
          name="name"
          type="text"
          required
          maxLength={160}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>

      <label className="form-row">
        <span>Цена, ₽</span>
        <input
          name="price"
          type="text"
          required
          inputMode="decimal"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
      </label>

      <div className="form-row">
        <span>Размеры и остатки</span>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {sizeStocks.map((entry, idx) => (
            <div key={idx} style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="text"
                placeholder="Размер (S, M, L...)"
                maxLength={8}
                value={entry.size}
                onChange={(e) => updateRow(idx, "size", e.target.value)}
                style={{ flex: 1 }}
              />
              <input
                type="number"
                placeholder="Остаток"
                min={0}
                value={entry.stock}
                onChange={(e) => updateRow(idx, "stock", e.target.value)}
                style={{ width: 90 }}
              />
              {sizeStocks.length > 1 && (
                <button
                  type="button"
                  className="btn btn--ghost btn--small btn--danger"
                  onClick={() => removeRow(idx)}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          <button type="button" className="btn btn--ghost btn--small" onClick={addRow}>
            + Добавить размер
          </button>
        </div>
      </div>

      <label className="form-row">
        <span>Описание</span>
        <textarea
          name="description"
          maxLength={4000}
          rows={5}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>

      <label className="form-row">
        <span>Фото (jpg, png, webp, gif — до 5 МБ)</span>
        <input name="image" type="file" accept="image/*" />
      </label>

      {showRemoveImage && initial?.imageUrl && (
        <label className="form-row form-row--inline">
          <input
            type="checkbox"
            name="remove_image"
            value="1"
            checked={removeImage}
            onChange={(e) => setRemoveImage(e.target.checked)}
          />
          <span>Удалить текущее фото</span>
        </label>
      )}

      {initial?.imageUrl && (
        <div className="muted small">
          Текущее фото:
          <br />
          <img
            src={initial.imageUrl}
            alt=""
            style={{ maxWidth: 200, marginTop: 8, borderRadius: 8 }}
          />
        </div>
      )}

      <div className="form-actions">
        <button className="btn btn--primary" type="submit" disabled={submitting}>
          {submitting ? "Сохраняем…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
