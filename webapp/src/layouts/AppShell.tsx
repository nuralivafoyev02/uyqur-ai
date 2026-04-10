import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "hooks/useAuth";
import { classNames } from "lib/format";

const navigation = [
  { to: "/", label: "Dashboard" },
  { to: "/groups", label: "Guruhlar" },
  { to: "/agents", label: "Agentlar" },
  { to: "/knowledge-base", label: "Knowledge Base" },
  { to: "/bot-control", label: "Bot Control" },
  { to: "/settings", label: "Sozlamalar" },
  { to: "/audit-logs", label: "Audit Logs" }
];

export function AppShell() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside className="border-b border-white/70 bg-slate-950 px-5 py-6 text-white lg:min-h-screen lg:border-b-0 lg:border-r lg:border-r-slate-800">
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-emerald-200/80">Uyqur AI</p>
          <h1 className="mt-2 text-2xl font-semibold">Support Control</h1>
          <p className="mt-2 text-sm text-slate-300">Telegram support guruhlari, agent statistikasi va bot training markazi.</p>
        </div>
        <nav className="mt-6 grid gap-2">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                classNames(
                  "rounded-2xl px-4 py-3 text-sm font-medium transition hover:bg-white/10",
                  isActive ? "bg-white text-slate-950" : "text-slate-200"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="p-4 sm:p-6 lg:p-8">
        <header className="mb-6 flex flex-col gap-4 rounded-3xl border border-white/70 bg-white/75 p-5 shadow-panel backdrop-blur md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Admin session</p>
            <h2 className="mt-2 text-2xl font-semibold text-slate-950">{session?.user?.display_name}</h2>
            <p className="mt-1 text-sm text-slate-500">@{session?.user?.username}</p>
          </div>
          <button
            onClick={async () => {
              await logout();
              navigate("/login");
            }}
            className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:border-slate-300"
          >
            Chiqish
          </button>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
