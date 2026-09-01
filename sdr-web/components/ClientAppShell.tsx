"use client";

import { Suspense } from "react";
import OnboardingModal from "@/components/modals/OnboardingModal";
import TopNav from "@/components/TopNav";
import { CountyProvider } from "@/components/county/CountyProvider";
import { LocaleProvider } from "@/components/i18n/LocaleProvider";

export default function ClientAppShell({ children }: { children: React.ReactNode }) {
  return (
    <LocaleProvider>
      <CountyProvider>
        <Suspense fallback={<header className="h-14 border-b border-border bg-paper/95" />}>
          <TopNav />
        </Suspense>
        <main>{children}</main>
        <OnboardingModal />
      </CountyProvider>
    </LocaleProvider>
  );
}
