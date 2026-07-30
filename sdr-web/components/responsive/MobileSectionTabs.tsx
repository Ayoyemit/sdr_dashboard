"use client";

interface Tab {
  id: string;
  label: string;
}

interface Props {
  tabs: Tab[];
  activeId: string;
  onChange: (id: string) => void;
  /** Accent color for active tab border */
  accent?: "a" | "b" | "neutral";
}

const ACCENT_STYLES = {
  a: "border-[#2563A8] bg-[#E0EBF5] text-[#2563A8]",
  b: "border-[#2B7A3E] bg-[#DCEEE0] text-[#2B7A3E]",
  neutral: "border-ink bg-card text-ink",
};

export default function MobileSectionTabs({ tabs, activeId, onChange, accent = "neutral" }: Props) {
  return (
    <div
      className="flex gap-2 p-1 bg-paper-deep rounded-lg border border-border md:hidden"
      role="tablist"
    >
      {tabs.map((tab) => {
        const active = tab.id === activeId;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab.id)}
            className={`flex-1 min-h-[44px] px-3 py-2 rounded-md text-sm font-medium transition border ${
              active
                ? ACCENT_STYLES[accent]
                : "border-transparent text-ink-muted hover:text-ink-soft"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
