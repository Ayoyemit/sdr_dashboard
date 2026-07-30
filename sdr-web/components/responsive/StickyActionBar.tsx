"use client";

import { ReactNode } from "react";

interface Props {
  children: ReactNode;
  /** Extra class on the inner bar */
  className?: string;
}

/** Fixed bottom action bar on phone/tablet; hidden on lg+ where inline actions exist. */
export default function StickyActionBar({ children, className = "" }: Props) {
  return (
    <>
      <div className="h-20 lg:hidden" aria-hidden />
      <div
        className="fixed inset-x-0 bottom-0 z-40 lg:hidden border-t border-border bg-paper/95 backdrop-blur safe-bottom"
        role="region"
        aria-label="Primary actions"
      >
        <div className={`max-w-7xl mx-auto px-4 py-3 ${className}`}>{children}</div>
      </div>
    </>
  );
}
