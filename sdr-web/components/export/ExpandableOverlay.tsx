"use client";

import { ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";
import { useLocale } from "@/components/i18n/LocaleProvider";

interface Props {
  open: boolean;
  onClose: () => void;
  title: string;
  titleId: string;
  actions?: ReactNode;
  children: ReactNode;
  /** chart = fixed chart height; table = scrollable wide content */
  variant?: "chart" | "table";
}

export function ExpandButton({
  onClick,
  label,
}: {
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1.5 min-h-[44px] px-3 py-1.5 text-xs text-ink-soft border border-border rounded-md hover:bg-paper-deep hover:text-ink transition"
      aria-label={label}
    >
      <svg
        viewBox="0 0 16 16"
        className="w-3.5 h-3.5 shrink-0"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden
      >
        <path
          d="M6 2H2v4M10 2h4v4M10 14h4v-4M6 14H2v-4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span className="hidden sm:inline">{label}</span>
    </button>
  );
}

export default function ExpandableOverlay({
  open,
  onClose,
  title,
  titleId,
  actions,
  children,
  variant = "chart",
}: Props) {
  const { t } = useLocale();

  useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    const resizeTimer = window.setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 60);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKeyDown);
      window.clearTimeout(resizeTimer);
    };
  }, [open, onClose]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[60] flex items-end sm:items-center justify-center p-0 sm:p-4 md:p-8 bg-ink/50 backdrop-blur-sm safe-bottom"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onClick={onClose}
    >
      <div
        className={`w-full bg-card border-0 sm:border border-border rounded-none sm:rounded-xl shadow-2xl p-4 sm:p-5 md:p-8 flex flex-col ${
          variant === "table"
            ? "h-[100dvh] sm:h-auto sm:max-h-[92dvh] max-w-7xl"
            : "h-[100dvh] sm:h-auto sm:max-h-[92dvh] max-w-6xl"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-wrap items-start justify-between gap-4 mb-4 sm:mb-5 shrink-0">
          <div className="min-w-0">
            <h3 id={titleId} className="font-display text-lg sm:text-xl">
              {title}
            </h3>
            <p className="text-xs text-ink-muted mt-1">{t("charts.escHint")}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {actions}
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center gap-1.5 min-h-[44px] px-3 py-1.5 text-xs border border-border rounded-md hover:bg-paper-deep transition"
            >
              {t("charts.close")}
            </button>
          </div>
        </div>
        <div className={variant === "table" ? "flex-1 min-h-0 overflow-auto" : "w-full"}>
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
}
