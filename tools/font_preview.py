"""Build a small standalone browser preview of EOA3 Unicode QA samples.

This is NOT the game UI and contains no font files. Only in-memory HTML is built.
"""
import html

from audit_unicode_layout import logical_lines


def display_lines(raw):
    return "\n".join(logical_lines(raw))


def make_html(report, font="Segoe UI"):
    if report.get("status") != "static_language_preflight_not_a_game_patch":
        raise ValueError("Unexpected layout report kind")
    face = html.escape(font, quote=True)
    blocks = []
    for x in report["font_probe_cases"]:
        ident = html.escape(str(x["id"]), quote=True)
        label = html.escape(str(x["call"]), quote=True)
        original = html.escape(display_lines(x.get("source", "")), quote=True)
        translation = html.escape(display_lines(x["vi"]), quote=True)
        blocks.append(
            '<section class="sample"><div class="meta">' + ident + " · " + label +
            '</div><div class="pair"><div><strong>Nguyên văn</strong><pre lang="zh">' +
            original + '</pre></div><div><strong>Bản Việt</strong><pre lang="vi">' +
            translation + "</pre></div></div></section>"
        )
    return """<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EOA3 — Soi chữ Việt ngoại tuyến</title>
<style>
:root{font-family:system-ui,sans-serif;color-scheme:light}
body{max-width:1150px;padding:24px;margin:auto;background:#f8f9fb;color:#1b202a}
h1{font-size:28px;margin-bottom:12px}
aside{padding:12px 18px;background:#fff4da;border:1px solid #e0c587;border-radius:8px}
.sample{background:white;margin:18px 0;padding:18px;border-radius:12px;box-shadow:0 1px 6px #0001}
.meta{color:#525e70;font-size:13px;margin-bottom:12px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}
pre{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #e3e7ec;border-radius:8px;
padding:14px;font-size:17px;line-height:1.55;font-family:""" + '"' + face + '"' + """,system-ui,sans-serif}
strong{font-size:14px} @media(max-width:720px){.pair{grid-template-columns:1fr}}
</style></head><body>
<h1>EOA3 — Soi chữ Việt ngoại tuyến</h1>
<aside><b>Đây không phải giao diện của game.</b> Trình duyệt dùng font và cách
ngắt dòng khác engine AngelSLG. Bản xem trước chỉ để tìm dấu sai, khoảng trắng,
lời thoại dài và so sánh bản gốc. Chưa thể xác nhận font/khung game.</aside>
<p>Font đề xuất: <b>""" + face + """</b>. Không nhúng hay phân phối font.</p>
""" + "\n".join(blocks) + """
</body></html>
"""


if __name__ == "__main__":
    raise SystemExit("Use windows_diagnostic_bundle.py; preview is generated in the ZIP.")
