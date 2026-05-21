#!/usr/bin/env python3
"""Clean BursarBot system architecture PNG — v3."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

W, H = 20, 18
fig = plt.figure(figsize=(W, H), facecolor="white")
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")


# ── Helpers ───────────────────────────────────────────────────────────────────
def rbox(x, y, w, h, fc, ec, tc, title, sub=None, tfs=10.5):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.18",
                        facecolor=fc, edgecolor=ec, linewidth=2.2, zorder=2)
    ax.add_patch(p)
    ty = y + h / 2 + (0.22 if sub else 0)
    ax.text(x + w / 2, ty, title, ha="center", va="center",
            fontsize=tfs, fontweight="bold", color=tc, zorder=3)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.26, sub, ha="center", va="center",
                fontsize=tfs - 2.5, color=tc, alpha=0.8, zorder=3, style="italic")


def arrow(x1, y1, x2, y2, color="#9ca3af", lw=1.8, dash=False, label=None,
          lx=None, ly=None):
    ls = (0, (5, 4)) if dash else "solid"
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw,
                                linestyle=ls, shrinkA=6, shrinkB=6), zorder=1)
    if label:
        tx = lx if lx is not None else (x1 + x2) / 2 + 0.2
        ty = ly if ly is not None else (y1 + y2) / 2
        ax.text(tx, ty, label, fontsize=7.5, color=color, ha="left", va="center",
                zorder=4, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))


def segline(xs, ys, color, lw=1.8, dash=False, label=None, lx=None, ly=None):
    """Polyline with an arrowhead at the last point."""
    ls = (0, (5, 4)) if dash else "solid"
    ax.plot(xs, ys, color=color, lw=lw, linestyle=ls, zorder=1, solid_capstyle="round")
    # draw arrowhead only at endpoint by annotating a tiny segment
    dx, dy = xs[-1] - xs[-2], ys[-1] - ys[-2]
    dist = (dx**2 + dy**2) ** 0.5
    if dist:
        nudge = 0.3 / dist
        ax.annotate("", xy=(xs[-1], ys[-1]),
                    xytext=(xs[-1] - nudge * dx, ys[-1] - nudge * dy),
                    arrowprops=dict(arrowstyle="->", color=color, lw=lw, shrinkA=0, shrinkB=6),
                    zorder=2)
    if label and lx is not None:
        ax.text(lx, ly, label, fontsize=7.5, color=color, ha="left", va="center",
                zorder=4, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.9))


# ── Band backgrounds ──────────────────────────────────────────────────────────
# Title area sits above y=16.2 — bands stay below it
bands = [
    (15.0, 16.0, "#fdf4ff", "#ddd6fe", "User"),
    (12.3, 14.7, "#eff6ff", "#bfdbfe", "Frontend"),
    (5.3,  12.0, "#f5f3ff", "#ddd6fe", "Backend /\nLangGraph"),
    (0.3,  5.0,  "#f0fdf4", "#bbf7d0", "Data · GCP"),
]
for yb, yt, fc, ec, lbl in bands:
    bg = FancyBboxPatch((0.9, yb), 18.8, yt - yb,
                         boxstyle="round,pad=0.1",
                         facecolor=fc, edgecolor=ec, linewidth=1.4, zorder=0)
    ax.add_patch(bg)
    ax.text(0.45, (yb + yt) / 2, lbl, fontsize=8.5, fontweight="bold",
            color="#9ca3af", ha="center", va="center", rotation=90, linespacing=1.5)


# ── USER ─────────────────────────────────────────────────────────────────────
rbox(6.5, 15.1, 7.0, 0.78, "#ede9fe", "#7c3aed", "#4c1d95",
     "Student / Admin / Staff", "Web Browser", tfs=11)


# ── FRONTEND ─────────────────────────────────────────────────────────────────
rbox(1.2, 13.1, 5.2, 1.35, "#dbeafe", "#2563eb", "#1e3a8a",
     "Next.js 15", "Chat UI  ·  Port 3001")
rbox(7.9, 13.1, 4.5, 1.35, "#e0e7ff", "#4f46e5", "#312e81",
     "Proxy Rewrite", "/api/backend/* → :8001")
rbox(14.2, 13.1, 5.1, 1.35, "#fce7f3", "#db2777", "#831843",
     "RBAC Auth", "role lookup · AIGravyty_USERS")


# ── LANGGRAPH zone ────────────────────────────────────────────────────────────
ax.add_patch(FancyBboxPatch((1.1, 5.7), 17.5, 6.0,
                             boxstyle="round,pad=0.12",
                             facecolor="#fafafa", edgecolor="#a78bfa",
                             linewidth=1.6, linestyle=(0, (6, 3)), zorder=1))
ax.text(1.6, 11.55, "LangGraph StateGraph  ·  MemorySaver (per thread_id)",
        fontsize=8.5, color="#7c3aed", fontweight="bold", zorder=3)


# FastAPI
rbox(1.2, 10.15, 5.5, 1.35, "#cffafe", "#0891b2", "#0e7490",
     "FastAPI", "Port 8001  ·  /chat  /reports/*")

# Intent Classifier
rbox(8.3, 10.15, 5.5, 1.35, "#fef3c7", "#d97706", "#78350f",
     "Intent Classifier", "outreach  |  qna  ·  Gemini 2.5 Flash")

# Agents
rbox(1.2, 8.1,  4.8, 1.35, "#d1fae5", "#059669", "#064e3b",
     "QnA Agent", "Gemini 2.5 Flash")
rbox(7.3, 8.1,  4.8, 1.35, "#ccfbf1", "#0d9488", "#0f766e",
     "Outreach Agent", "Gemini 2.5 Flash")
rbox(13.5, 8.1, 5.2, 1.35, "#e0f2fe", "#0284c7", "#0c4a6e",
     "Student Agent", "restricted · role enforcement")

# Tool Node (wide)
rbox(3.8, 6.1, 11.8, 1.35, "#ede9fe", "#7c3aed", "#4c1d95",
     "Tool Node",
     "get_balance  ·  get_bucket  ·  get_finaid  ·  get_comments  ·  send_outreach_email")


# ── DATA / GCP ────────────────────────────────────────────────────────────────
# BigQuery  Gemini  |  Gmail (stacked over Excel)  |  Planned
rbox(1.0,  0.55, 4.8, 4.1, "#dbeafe", "#1d4ed8", "#1e3a8a",
     "Google BigQuery", "6 tables · student_financials")
rbox(6.8,  0.55, 4.8, 4.1, "#fce7f3", "#db2777", "#831843",
     "Gemini 2.5 Flash", "Google AI · temperature=0")
rbox(12.5, 2.6,  4.3, 2.05, "#fef3c7", "#d97706", "#78350f",
     "Gmail SMTP", "CL1 / CL2 / Final Demand")
rbox(12.5, 0.55, 4.3, 1.85, "#d1fae5", "#059669", "#064e3b",
     "Excel Reports", "/reports/*.xlsx")
rbox(17.7, 0.55, 1.9, 4.1, "#f5f3ff", "#7c3aed", "#4c1d95",
     "Planned", "RAG\nOkta SSO", tfs=9)


# ── ARROWS ───────────────────────────────────────────────────────────────────
DARK   = "#6b7280"
BLUE   = "#2563eb"
CYAN   = "#0891b2"
GREEN  = "#059669"
GOLD   = "#d97706"
PINK   = "#db2777"

# User → Next.js
arrow(10.0, 15.1, 3.82, 14.45, color=DARK, label="HTTPS", lx=6.8, ly=14.9)

# Next.js → Proxy
arrow(6.4, 13.78, 7.9, 13.78, color=BLUE)

# Proxy → FastAPI
arrow(10.15, 13.1, 5.5, 11.5, color=BLUE, label="JSON /chat", lx=8.3, ly=12.4)

# FastAPI → Intent
arrow(6.7, 10.82, 8.3, 10.82, color=CYAN)

# Intent → Agents
arrow(9.5,  10.15, 3.6,  9.45, color=GOLD)
arrow(11.05, 10.15, 9.7,  9.45, color=GOLD)
arrow(12.6,  10.15, 16.1, 9.45, color=GOLD)

# Agents → Tool Node
arrow(3.6,  8.1, 6.5,  7.45, color=DARK)
arrow(9.7,  8.1, 9.7,  7.45, color=DARK)
arrow(16.1, 8.1, 14.0, 7.45, color=DARK)

# Tool Node → Data
# → BigQuery
arrow(6.2, 6.1, 3.4, 4.65, color=BLUE, label="queries", lx=4.0, ly=5.6)
# → Gemini
arrow(9.7, 6.1, 9.2, 4.65, color=PINK, label="generate", lx=9.8, ly=5.6)
# → Gmail  (goes right from tool node right area)
arrow(14.2, 6.1, 14.65, 4.65, color=GOLD, label="email", lx=14.75, ly=5.6)
# → Excel  (goes around Gmail's left side)
arrow(11.5, 6.1, 12.5, 2.4, color=GREEN, label=".xlsx", lx=12.0, ly=4.8)

# RBAC → BigQuery: right margin → above Data band → drop into BigQuery
segline([19.3, 19.55, 19.55, 3.4, 3.4], [13.1, 13.1, 5.15, 5.15, 4.65],
        color=PINK, dash=True, label="role lookup", lx=19.6, ly=9.2)


# ── TITLE  (sits above all bands) ─────────────────────────────────────────────
ax.text(10.0, H - 0.25, "BursarBot  —  System Architecture",
        ha="center", va="top", fontsize=18, fontweight="bold", color="#0055A2")
ax.text(10.0, H - 0.92,
        "SJSU Bursar's Office AI Assistant  ·  LangGraph + Gemini 2.5 Flash + Google BigQuery",
        ha="center", va="top", fontsize=10, color="#6b7280")


out = "/Users/spartan/Desktop/Bursar Bot/bursar-bot/architecture.png"
plt.savefig(out, dpi=180, bbox_inches="tight", facecolor="white", edgecolor="none")
print(f"Saved → {out}")
