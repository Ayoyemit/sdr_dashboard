/** Shared logo mark — maternal care heart (replaces legacy pulse/S icon). */
export default function SdrLogoMark({ className = "w-4 h-4" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden>
      <path
        d="M12 20.5s-6.5-4.2-6.5-9.2C5.5 8.5 8.2 6 12 8c3.8-2 6.5.5 6.5 3.3 0 5-6.5 9.2-6.5 9.2Z"
        fill="#B5471F"
        fillOpacity="0.15"
        stroke="#B5471F"
        strokeWidth="1.6"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="11" r="1.5" fill="#B5471F" />
    </svg>
  );
}
