"use client";

import { ReactNode } from "react";

interface Props {
  /** Desktop/tablet view (md+) */
  children: ReactNode;
  /** Phone view (< md) */
  mobileView: ReactNode;
}

export default function ResponsiveDataView({ children, mobileView }: Props) {
  return (
    <>
      <div className="hidden md:block">{children}</div>
      <div className="md:hidden">{mobileView}</div>
    </>
  );
}
