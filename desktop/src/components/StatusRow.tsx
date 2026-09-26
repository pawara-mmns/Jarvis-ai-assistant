interface StatusRowProps {
  label: string;
  value: string;
  active?: boolean;
}

export function StatusRow({ label, value, active = false }: StatusRowProps) {
  return (
    <div className="flex items-center justify-between border-b border-slate-800 py-3 last:border-0">
      <span className="text-sm text-slate-400">{label}</span>
      <span className={active ? "text-sm text-cyan-300" : "text-sm text-slate-100"}>
        {value}
      </span>
    </div>
  );
}
