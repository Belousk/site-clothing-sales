interface Props {
  message?: string | null;
  errors?: string[];
}

export default function ErrorBox({ message, errors }: Props) {
  const items = errors && errors.length ? errors : message ? [message] : [];
  if (!items.length) return null;
  return (
    <div className="alert alert--danger">
      <ul style={{ margin: 0, paddingLeft: 20 }}>
        {items.map((it, i) => (
          <li key={i}>{it}</li>
        ))}
      </ul>
    </div>
  );
}
