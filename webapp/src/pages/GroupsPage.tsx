import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState } from "components/EmptyState";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Panel } from "components/Panel";
import { api } from "lib/api";
import type { GroupItem } from "types/api";

export function GroupsPage() {
  const [groups, setGroups] = useState<GroupItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<GroupItem[]>("/api/admin/groups")
      .then(setGroups)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(
    () => groups.filter((group) => group.title.toLowerCase().includes(search.toLowerCase())),
    [groups, search]
  );

  if (loading) return <LoadingState label="Guruhlar yuklanmoqda..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <Panel title="Barcha guruhlar" subtitle="Track qilinayotgan management va support chatlar">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Guruh bo'yicha qidirish"
          className="md:max-w-sm"
        />
        <button
          onClick={async () => setGroups(await api.post<GroupItem[]>("/api/admin/groups/sync"))}
          className="rounded-2xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:border-slate-300"
        >
          Sync qilish
        </button>
      </div>
      {filtered.length === 0 ? (
        <EmptyState title="Guruh topilmadi" description="Qidiruvga mos natija yo'q." />
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {filtered.map((group) => (
            <Link key={group.id} to={`/groups/${group.id}`} className="rounded-2xl border border-slate-200 p-4 hover:border-slate-300 hover:bg-slate-50">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-slate-900">{group.title}</h3>
                  <p className="text-sm text-slate-500">{group.group_type === "management" ? "Management group" : "Support group"}</p>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${group.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                  {group.is_active ? "Faol" : "Nofaol"}
                </span>
              </div>
              <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
                <div>
                  <dt className="text-slate-500">Jami</dt>
                  <dd className="mt-1 font-semibold text-slate-900">{group.metrics?.total_requests ?? 0}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Ochiq</dt>
                  <dd className="mt-1 font-semibold text-slate-900">{group.metrics?.open_requests ?? 0}</dd>
                </div>
                <div>
                  <dt className="text-slate-500">Foiz</dt>
                  <dd className="mt-1 font-semibold text-slate-900">{group.metrics?.response_rate ?? 0}%</dd>
                </div>
              </dl>
            </Link>
          ))}
        </div>
      )}
    </Panel>
  );
}
