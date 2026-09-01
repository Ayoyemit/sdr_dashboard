"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useLocale } from "@/components/i18n/LocaleProvider";
import { aboutHref } from "@/lib/about-nav";
import {
  getInterventionLibrary,
  getMomishLevel,
  getSingleLevel,
  GROUP_ORDER,
  GROUP_LABEL_KEYS,
  hasIntervention,
  InterventionGroup,
  InterventionId,
  LibraryItem,
  setMomishLevel,
  setSingleLevel,
} from "@/lib/interventions";
import { Scenario } from "@/lib/scenarios";

type ColumnTarget = "a" | "b";

interface Props {
  scenarioA: Scenario;
  scenarioB: Scenario;
  onAdd: (target: ColumnTarget, id: InterventionId) => void;
}

function wiredBadge(item: LibraryItem, t: (k: string) => string) {
  if (item.wired === "wired") return null;
  if (item.wired === "ui-only")
    return <span className="text-[9px] text-warning ml-1">● {t("common.uiOnly")}</span>;
  return <span className="text-[9px] text-warning ml-1">● partial</span>;
}

function LibButton({
  active,
  label,
  onClick,
  color,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
  color: "blue" | "green" | "neutral";
}) {
  const styles =
    color === "blue"
      ? { background: "#E0EBF5", color: "#2563A8", border: "1px solid #C0D5E8" }
      : color === "green"
        ? { background: "#DCEEE0", color: "#2B7A3E", border: "1px solid #BFDEC4" }
        : {};

  return (
    <button
      type="button"
      onClick={onClick}
      className="min-h-[44px] px-3 py-2 rounded text-[11px] flex items-center justify-center gap-1 border border-border text-ink-soft hover:bg-paper-deep"
      style={active ? styles : undefined}
    >
      {active ? "✓" : "+"} {label}
    </button>
  );
}

function LibraryContent({
  scenarioA,
  scenarioB,
  onAdd,
  returnPath,
}: {
  scenarioA: Scenario;
  scenarioB: Scenario;
  onAdd: (target: ColumnTarget, id: InterventionId) => void;
  returnPath: string;
}) {
  const { t } = useLocale();
  const library = getInterventionLibrary();

  return (
    <>
      {GROUP_ORDER.map((group) => {
        const items = library.filter((i) => i.group === group);
        return (
          <div key={group} className="mb-5">
            <div className="flex items-center gap-2 mb-2.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  group === "momish" ? "bg-accent" : group === "single" ? "bg-warning" : "bg-intervention"
                }`}
              />
              <span className="text-sm font-medium">{t(GROUP_LABEL_KEYS[group])}</span>
            </div>
            <div className="space-y-3 pl-4">
              {items.map((item) => {
                const inA = hasIntervention(scenarioA, item.id);
                const inB = hasIntervention(scenarioB, item.id);
                return (
                  <div key={item.id}>
                    <div className="text-[12px] mb-1.5">
                      {item.name}
                      {wiredBadge(item, t)}
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      <LibButton
                        active={inA}
                        label="A"
                        color="blue"
                        onClick={() => onAdd("a", item.id)}
                      />
                      <LibButton
                        active={inB}
                        label="B"
                        color="green"
                        onClick={() => onAdd("b", item.id)}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      <Link
        href={aboutHref(returnPath)}
        className="mt-4 block text-xs text-accent hover:underline pl-4"
      >
        {t("interventions.learnMore")} →
      </Link>

      <div className="mt-3 pl-4 pt-2 border-t border-border-soft text-[9px] text-ink-muted leading-relaxed">
        <span className="text-positive">●</span> drives simulation ·{" "}
        <span className="text-warning">●</span> UI controls only (model wiring pending)
      </div>
    </>
  );
}

export default function InterventionLibrary({ scenarioA, scenarioB, onAdd }: Props) {
  const { t } = useLocale();
  const pathname = usePathname();
  const returnPath = pathname || "/compare";
  const [open, setOpen] = useState(false);

  return (
    <aside className="lg:sticky lg:top-24 h-fit">
      <div className="lg:hidden mb-4">
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          className="w-full min-h-[44px] flex items-center justify-between px-4 py-3 bg-card border border-border rounded-xl text-sm font-medium"
          aria-expanded={open}
        >
          <span>{t("compare.libraryTitle")}</span>
          <span className="text-ink-muted">{open ? "−" : "+"}</span>
        </button>
        {open && (
          <div className="mt-3 p-4 bg-card border border-border rounded-xl max-h-[60vh] overflow-y-auto">
            <LibraryContent
              scenarioA={scenarioA}
              scenarioB={scenarioB}
              onAdd={onAdd}
              returnPath={returnPath}
            />
          </div>
        )}
      </div>

      <div className="hidden lg:block">
        <h2 className="font-display text-2xl leading-tight mb-1">{t("compare.libraryTitle")}</h2>
        <p className="text-xs text-ink-muted mb-5">{t("compare.libraryHint")}</p>
        <LibraryContent
          scenarioA={scenarioA}
          scenarioB={scenarioB}
          onAdd={onAdd}
          returnPath={returnPath}
        />
      </div>
    </aside>
  );
}

export { setMomishLevel, setSingleLevel };
