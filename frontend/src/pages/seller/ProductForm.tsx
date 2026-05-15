import { useState } from "react";

import { ApiError } from "../../api";
import ErrorBox from "../../components/ErrorBox";

interface Props {
  initial?: {
    name: string;
    price: string;
    sizes: string;
    description: string;
    stock: string;
    imageUrl: string | null;
  };
  submitLabel: string;
  onSubmit: (form: FormData) => Promise<void>;
  showRemoveImage?: boolean;
}

export default function ProductForm({ initial, submitLabel, onSubmit, showRemoveImage }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [price, setPrice] = useState(initial?.price ?? "");
  const [sizes, setSizes] = useState(initial?.sizes ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [stock, setStock] = useState(initial?.stock ?? "0");
  const [removeImage, setRemoveImage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const form = new FormData(e.currentTarget);
      // Если файл не выбран, убираем пустой файл из FormData (FastAPI ругается на пустые UploadFile).
      const file = form.get("image");
      if (file instanceof File && file.size === 0) {
        form.delete("image");
      }
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

      <label className="form-row">
        <span>Размеры (через запятую, до 20)</span>
        <input
          name="sizes"
          type="text"
          maxLength={200}
          placeholder="S, M, L, XL"
          value={sizes}
          onChange={(e) => setSizes(e.target.value)}
        />
      </label>

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
        <span>Остаток на складе</span>
        <input
          name="stock"
          type="number"
          min={0}
          required
          value={stock}
          onChange={(e) => setStock(e.target.value)}
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
