"""Генерация чеков: номер, transaction_id, PDF на диск."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..config import settings
from ..models import Order

_FONT_REGISTERED = False
_FONT_NAME = "DejaVuSans"
_FONT_BOLD_NAME = "DejaVuSans-Bold"


def _register_unicode_font() -> tuple[str, str]:
    """Регистрирует шрифт с поддержкой кириллицы. Один раз за процесс."""
    global _FONT_REGISTERED, _FONT_NAME, _FONT_BOLD_NAME
    if _FONT_REGISTERED:
        return _FONT_NAME, _FONT_BOLD_NAME

    candidates = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        # Windows fallback
        ("C:\\Windows\\Fonts\\DejaVuSans.ttf", "C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf"),
        ("C:\\Windows\\Fonts\\arial.ttf", "C:\\Windows\\Fonts\\arialbd.ttf"),
    ]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont(_FONT_NAME, regular))
            pdfmetrics.registerFont(TTFont(_FONT_BOLD_NAME, bold))
            _FONT_REGISTERED = True
            return _FONT_NAME, _FONT_BOLD_NAME

    # Fallback: встроенный Helvetica (кириллицы не будет, но не упадёт).
    # Обязательно перезаписываем глобалы, иначе на втором вызове ранний return
    # отдаст незарегистрированный 'DejaVuSans' и reportlab упадёт.
    _FONT_NAME = "Helvetica"
    _FONT_BOLD_NAME = "Helvetica-Bold"
    _FONT_REGISTERED = True
    return _FONT_NAME, _FONT_BOLD_NAME


def generate_receipt_number(now: datetime | None = None) -> str:
    """Генерирует читаемый номер чека вида RCP-YYYYMMDD-XXXXXX."""
    now = now or datetime.now(timezone.utc)
    suffix = secrets.token_hex(3).upper()
    return f"RCP-{now.strftime('%Y%m%d')}-{suffix}"


def generate_transaction_id() -> str:
    """ID транзакции (имитация платёжного шлюза)."""
    return f"TXN-{secrets.token_hex(8).upper()}"


def render_receipt_pdf(
    order: Order,
    receipt_number: str,
    transaction_id: str,
    issued_at: datetime,
) -> str:
    """Рендерит PDF в receipts_dir и возвращает имя файла."""
    regular, bold = _register_unicode_font()
    filename = f"{receipt_number}.pdf"
    path: Path = settings.receipts_dir / filename

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "title", parent=styles["Title"], fontName=bold, fontSize=20, leading=24, spaceAfter=8
    )
    eyebrow = ParagraphStyle(
        "eyebrow", parent=styles["Normal"], fontName=regular,
        fontSize=9, leading=11, textColor=colors.HexColor("#9aa1ad"),
        spaceAfter=12,
    )
    body = ParagraphStyle(
        "body", parent=styles["Normal"], fontName=regular, fontSize=11, leading=15,
    )
    body_bold = ParagraphStyle(
        "body_bold", parent=body, fontName=bold,
    )

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Чек {receipt_number}",
    )

    # reportlab Paragraph интерпретирует строку как XML — чтобы пользовательские
    # `<`, `>`, `&` не валили генерацию, экранируем все динамические значения.
    story: list = []
    story.append(Paragraph("ATELIER · ИНТЕРНЕТ-МАГАЗИН ОДЕЖДЫ", eyebrow))
    story.append(Paragraph(f"Чек {xml_escape(receipt_number)}", title))
    story.append(Paragraph(
        f"Дата выдачи: {issued_at.strftime('%d.%m.%Y %H:%M')} (UTC)",
        body,
    ))
    story.append(Paragraph(f"Заказ №{order.id}", body))
    story.append(Paragraph(f"ID транзакции: {xml_escape(transaction_id)}", body))
    story.append(Spacer(1, 10 * mm))

    story.append(Paragraph("Получатель", body_bold))
    story.append(Paragraph(xml_escape(order.recipient_name), body))
    story.append(Paragraph(xml_escape(order.recipient_phone), body))
    story.append(Paragraph(xml_escape(order.delivery_address), body))
    if order.comment:
        story.append(Paragraph(f"Комментарий: {xml_escape(order.comment)}", body))
    story.append(Spacer(1, 8 * mm))

    table_header = ["№", "Товар", "Размер", "Цена, ₽", "Кол-во", "Сумма, ₽"]
    table_rows: list[list[str]] = [table_header]
    for idx, item in enumerate(order.items, start=1):
        size_display = item.selected_size if item.selected_size else (item.sizes or "—")
        table_rows.append([
            str(idx),
            item.product_name,
            size_display,
            f"{item.product_price:.2f}",
            str(item.quantity),
            f"{item.line_total:.2f}",
        ])

    table = Table(
        table_rows,
        colWidths=[10 * mm, 70 * mm, 25 * mm, 25 * mm, 20 * mm, 25 * mm],
        repeatRows=1,
    )
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), bold),
        ("FONTNAME", (0, 1), (-1, -1), regular),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2330")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d8dde6")),
    ]))
    story.append(table)
    story.append(Spacer(1, 6 * mm))

    total_table = Table(
        [["ИТОГО:", f"{order.total:.2f} ₽"]],
        colWidths=[150 * mm, 45 * mm],
    )
    total_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), bold),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 12 * mm))

    footer = ParagraphStyle(
        "footer", parent=body, fontSize=9, textColor=colors.HexColor("#9aa1ad"),
    )
    story.append(Paragraph(
        "Документ сформирован автоматически. Учебный проект Atelier — "
        "оплата имитирована, реальная транзакция не проводилась.",
        footer,
    ))

    doc.build(story)
    return filename
