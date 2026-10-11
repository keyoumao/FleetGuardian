import clsx from "clsx";
import { Bot, Code2, LayoutDashboard, Pause, Play, ScrollText, ShieldAlert, ShieldCheck } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useFleet } from "../data/store";

const nav = [
  { to: "/", label: "Representation ASR", icon: LayoutDashboard, end: true },
  { to: "/monitor", label: "Live security monitor", icon: ShieldAlert },
  { to: "/runtime", label: "Runtime demo", icon: ShieldAlert },
  { to: "/agents", label: "Agents", icon: Bot },
  { to: "/incidents", label: "Incidents", icon: ShieldAlert },
  { to: "/policies", label: "Policies & guardrails", icon: ScrollText },
  { to: "/harnesses", label: "Harness source trust", icon: Code2 },
];

export default function Layout() {
  const { incidents, live, setLive, harnesses } = useFleet();
  const openIncidents = incidents.filter((i) => i.status === "open").length;
  const openVulns = harnesses.filter((h) => h.scan).flatMap((h) => h.vulns).filter((v) => v.status === "open").length;

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-200">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-950 p-4 md:flex">
        <div className="mb-8 flex items-center gap-2 px-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600">
            <ShieldCheck className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="font-semibold text-white">FleetGuardian</div>
            <div className="text-xs text-slate-500">Is your security score honest?</div>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition",
                  isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900 hover:text-slate-200",
                )
              }
            >
              <Icon className="h-4 w-4" />
              <span className="flex-1">{label}</span>
              {to === "/incidents" && openIncidents > 0 && (
                <span className="rounded-full bg-rose-500/20 px-2 text-xs text-rose-300">{openIncidents}</span>
              )}
              {to === "/harnesses" && openVulns > 0 && (
                <span className="rounded-full bg-orange-500/20 px-2 text-xs text-orange-300">{openVulns}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={() => setLive(!live)}
          className="mt-4 flex items-center justify-between rounded-lg border border-slate-800 px-3 py-2 text-xs text-slate-400 hover:bg-slate-900"
        >
          <span className="flex items-center gap-2">
            <span className={clsx("h-2 w-2 rounded-full", live ? "animate-pulse bg-emerald-400" : "bg-slate-600")} />
            {live ? "Runtime simulation" : "Simulation paused"}
          </span>
          {live ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
        </button>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* mobile nav */}
        <div className="flex gap-1 overflow-x-auto border-b border-slate-800 p-2 md:hidden">
          {nav.map(({ to, label, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => clsx("whitespace-nowrap rounded-md px-3 py-1.5 text-sm", isActive ? "bg-slate-800 text-white" : "text-slate-400")}>
              {label}
            </NavLink>
          ))}
        </div>
        <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
