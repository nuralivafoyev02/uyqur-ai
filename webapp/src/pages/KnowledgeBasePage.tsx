import { FormEvent, useEffect, useMemo, useState } from "react";
import { EmptyState } from "components/EmptyState";
import { ErrorState } from "components/ErrorState";
import { LoadingState } from "components/LoadingState";
import { Modal } from "components/Modal";
import { Panel } from "components/Panel";
import { api } from "lib/api";
import type { KBEntry } from "types/api";

const defaultForm = {
  title: "",
  language: "uz",
  category: "",
  keywords: "",
  synonyms: "",
  patterns: "",
  answer_template: "",
  priority: 10,
  is_active: true,
  confidence_threshold_override: ""
};

function normalizeTerms(entry: KBEntry): KBEntry {
  if (entry.keywords || entry.synonyms || entry.patterns) return entry;
  const terms = entry.kb_terms || [];
  return {
    ...entry,
    keywords: terms.filter((term) => term.term_type === "keyword").map((term) => term.term_value),
    synonyms: terms.filter((term) => term.term_type === "synonym").map((term) => term.term_value),
    patterns: terms.filter((term) => term.term_type === "pattern").map((term) => term.term_value)
  };
}

export function KnowledgeBasePage() {
  const [entries, setEntries] = useState<KBEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(defaultForm);
  const [testInput, setTestInput] = useState("");
  const [preview, setPreview] = useState<Record<string, unknown> | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const result = await api.get<KBEntry[]>("/api/admin/kb");
      setEntries(result.map(normalizeTerms));
      setError("");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const payload = {
      title: form.title,
      language: form.language,
      category: form.category,
      keywords: form.keywords.split(",").map((item) => item.trim()).filter(Boolean),
      synonyms: form.synonyms.split(",").map((item) => item.trim()).filter(Boolean),
      patterns: form.patterns.split(",").map((item) => item.trim()).filter(Boolean),
      answer_template: form.answer_template,
      priority: Number(form.priority),
      is_active: form.is_active,
      confidence_threshold_override: form.confidence_threshold_override ? Number(form.confidence_threshold_override) : null
    };
    if (editingId) {
      await api.patch(`/api/admin/kb/${editingId}`, payload);
    } else {
      await api.post("/api/admin/kb", payload);
    }
    setOpen(false);
    setForm(defaultForm);
    await load();
  };

  const activeCount = useMemo(() => entries.filter((entry) => entry.is_active).length, [entries]);

  if (loading) return <LoadingState label="Knowledge Base yuklanmoqda..." />;
  if (error) return <ErrorState message={error} />;

  return (
    <>
      <div className="space-y-6">
        <Panel
          title="Knowledge Base / Training"
          subtitle={`${entries.length} ta entry, ${activeCount} tasi faol`}
          action={
            <button onClick={() => { setEditingId(null); setForm(defaultForm); setOpen(true); }} className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-medium text-white">
              Entry qo'shish
            </button>
          }
        >
          {entries.length === 0 ? (
            <EmptyState title="KB entry yo'q" description="Bot deterministic auto-reply uchun hali qoidalar qo'shilmagan." />
          ) : (
            <div className="grid gap-4">
              {entries.map((entry) => (
                <article key={entry.id} className="rounded-2xl border border-slate-200 p-4">
                  <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold text-slate-900">{entry.title}</h3>
                        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${entry.is_active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                          {entry.is_active ? "Faol" : "Nofaol"}
                        </span>
                      </div>
                      <p className="mt-2 text-sm text-slate-500">
                        {entry.category} • {entry.language} • priority {entry.priority}
                      </p>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{entry.answer_template}</p>
                      <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
                        {(entry.keywords || []).map((keyword) => (
                          <span key={keyword} className="rounded-full bg-slate-100 px-2.5 py-1">keyword: {keyword}</span>
                        ))}
                        {(entry.synonyms || []).map((item) => (
                          <span key={item} className="rounded-full bg-cyan-50 px-2.5 py-1 text-cyan-700">synonym: {item}</span>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditingId(entry.id);
                          setForm({
                            title: entry.title,
                            language: entry.language,
                            category: entry.category,
                            keywords: (entry.keywords || []).join(", "),
                            synonyms: (entry.synonyms || []).join(", "),
                            patterns: (entry.patterns || []).join(", "),
                            answer_template: entry.answer_template,
                            priority: entry.priority,
                            is_active: entry.is_active,
                            confidence_threshold_override: entry.confidence_threshold_override?.toString() || ""
                          });
                          setOpen(true);
                        }}
                        className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-slate-600"
                      >
                        Tahrirlash
                      </button>
                      <button
                        onClick={async () => {
                          await api.delete(`/api/admin/kb/${entry.id}`);
                          await load();
                        }}
                        className="rounded-xl border border-rose-200 px-3 py-1.5 text-sm text-rose-700"
                      >
                        O'chirish
                      </button>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </Panel>
        <Panel title="Test match" subtitle="Xabar qaysi qoida bilan tushishini oldindan tekshirish">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
            <textarea rows={4} value={testInput} onChange={(event) => setTestInput(event.target.value)} placeholder="Masalan: yetkazib berish qachon bo'ladi?" />
            <button
              onClick={async () => setPreview(await api.post("/api/admin/kb/test-match", { text: testInput, language: "uz" }))}
              className="rounded-2xl bg-accent px-4 py-3 text-sm font-semibold text-white"
            >
              Match ko'rish
            </button>
          </div>
          {preview ? (
            <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-700">
              <pre className="overflow-auto whitespace-pre-wrap">{JSON.stringify(preview, null, 2)}</pre>
            </div>
          ) : null}
        </Panel>
      </div>
      <Modal open={open} onClose={() => setOpen(false)} title={editingId ? "KB entryni tahrirlash" : "Yangi KB entry"}>
        <form onSubmit={submit} className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Title</label>
            <input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Language</label>
            <input value={form.language} onChange={(event) => setForm((prev) => ({ ...prev, language: event.target.value }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Category</label>
            <input value={form.category} onChange={(event) => setForm((prev) => ({ ...prev, category: event.target.value }))} required />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Keywords (comma-separated)</label>
            <input value={form.keywords} onChange={(event) => setForm((prev) => ({ ...prev, keywords: event.target.value }))} />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Synonyms (comma-separated)</label>
            <input value={form.synonyms} onChange={(event) => setForm((prev) => ({ ...prev, synonyms: event.target.value }))} />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Patterns (comma-separated or regex)</label>
            <input value={form.patterns} onChange={(event) => setForm((prev) => ({ ...prev, patterns: event.target.value }))} />
          </div>
          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium text-slate-700">Answer template</label>
            <textarea rows={6} value={form.answer_template} onChange={(event) => setForm((prev) => ({ ...prev, answer_template: event.target.value }))} required />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Priority</label>
            <input type="number" value={form.priority} onChange={(event) => setForm((prev) => ({ ...prev, priority: Number(event.target.value) }))} />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Threshold override</label>
            <input value={form.confidence_threshold_override} onChange={(event) => setForm((prev) => ({ ...prev, confidence_threshold_override: event.target.value }))} />
          </div>
          <div className="md:col-span-2 flex items-center gap-3">
            <input id="kb-active" type="checkbox" checked={form.is_active} onChange={(event) => setForm((prev) => ({ ...prev, is_active: event.target.checked }))} />
            <label htmlFor="kb-active" className="text-sm font-medium text-slate-700">Faol qoida</label>
          </div>
          <div className="md:col-span-2 flex justify-end">
            <button className="rounded-2xl bg-slate-950 px-4 py-2 text-sm font-semibold text-white">Saqlash</button>
          </div>
        </form>
      </Modal>
    </>
  );
}
