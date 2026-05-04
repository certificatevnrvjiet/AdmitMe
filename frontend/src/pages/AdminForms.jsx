import React, { useEffect, useMemo, useState } from "react";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import API from "../api";

const emptyField = {
  section: "Personal",
  field_key: "",
  label: "",
  field_type: "text",
  required: false,
  options: [],
  help_text: "",
  sort_order: 0,
  maps_to_student_field: true,
};

const defaultForm = {
  title: "B.Tech 2026 Admission Form",
  description: "Student admission details and required document uploads.",
  slug: "btech-2026",
  status: "draft",
  fields: [],
};

export default function AdminForms() {
  const [forms, setForms] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [editor, setEditor] = useState(defaultForm);
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(false);

  const selectedForm = useMemo(() => forms.find((form) => form.id === selectedId), [forms, selectedId]);
  const isDefaultForm = Boolean(selectedForm?.is_default);
  const formSlug = editor.slug || selectedForm?.slug || "btech-2026";
  const studentFormUrl = `${window.location.origin}/student-login?form=${encodeURIComponent(formSlug)}`;
  const portalUrl = `${window.location.origin}/student-portal/${encodeURIComponent(formSlug)}`;
  const publicApiUrl = `${API.defaults.baseURL}/public/forms/${encodeURIComponent(formSlug)}`;

  const fetchForms = async () => {
    setLoading(true);
    try {
      const { data } = await API.get("/forms");
      setForms(data.forms || []);
      if (!selectedId && data.forms?.[0]) setSelectedId(data.forms[0].id);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to load forms");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForms();
  }, []);

  useEffect(() => {
    if (selectedForm) {
      setEditor({
        title: selectedForm.title || "",
        description: selectedForm.description || "",
        slug: selectedForm.slug || "",
        status: selectedForm.status || "draft",
        fields: selectedForm.fields || [],
      });
      API.get(`/forms/${selectedForm.id}/responses`)
        .then((res) => setResponses(res.data.responses || []))
        .catch(() => setResponses([]));
    }
  }, [selectedForm?.id]);

  const updateField = (index, key, value) => {
    setEditor((prev) => ({
      ...prev,
      fields: prev.fields.map((field, i) => (i === index ? { ...field, [key]: value } : field)),
    }));
  };

  const addField = () => {
    setEditor((prev) => ({
      ...prev,
      fields: [...prev.fields, { ...emptyField, sort_order: (prev.fields.length + 1) * 10 }],
    }));
  };

  const saveForm = async () => {
    try {
      if (isDefaultForm) {
        toast.info("The built-in B.Tech 2026 form is managed in code. Create a new form to customize fields.");
        return;
      }
      const payload = {
        ...editor,
        fields: editor.fields.map((field, index) => ({
          ...field,
          options: Array.isArray(field.options)
            ? field.options
            : String(field.options || "").split(",").map((item) => item.trim()).filter(Boolean),
          sort_order: field.sort_order || (index + 1) * 10,
        })),
      };
      if (selectedId) {
        await API.put(`/forms/${selectedId}`, payload);
        toast.success("Form updated");
      } else {
        const { data } = await API.post("/forms", payload);
        setSelectedId(data.form.id);
        toast.success("Form created");
      }
      await fetchForms();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to save form");
    }
  };

  const createNew = () => {
    setSelectedId("");
    setResponses([]);
    setEditor(defaultForm);
  };

  const publishToggle = async () => {
    if (!selectedId) return;
    if (isDefaultForm) {
      toast.info("The built-in B.Tech 2026 form is always published.");
      return;
    }
    const action = editor.status === "published" ? "unpublish" : "publish";
    try {
      await API.post(`/forms/${selectedId}/${action}`);
      toast.success(action === "publish" ? "Form published" : "Form unpublished");
      await fetchForms();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to update status");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 text-gray-900">
      <div className="mx-auto max-w-7xl">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Admission Forms</h1>
            <p className="text-sm text-gray-600">Create, publish, and review student admission form responses.</p>
          </div>
          <button onClick={createNew} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">
            New Form
          </button>
        </div>

        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <aside className="rounded-lg border border-gray-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold uppercase text-gray-500">Forms</h2>
            {loading && <p className="text-sm text-gray-500">Loading...</p>}
            <div className="space-y-2">
              {forms.map((form) => (
                <button
                  key={form.id}
                  onClick={() => setSelectedId(form.id)}
                  className={`w-full rounded-md px-3 py-2 text-left text-sm ${selectedId === form.id ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700"}`}
                >
                  <div className="font-medium">{form.title}</div>
                  <div className="text-xs opacity-80">/{form.slug} - {form.status}</div>
                </button>
              ))}
            </div>
          </aside>

          <main className="space-y-6">
            <section className="rounded-lg border border-gray-200 bg-white p-5">
              {selectedForm && (
                <div className="mb-5 rounded-md border border-blue-100 bg-blue-50 p-4 text-sm text-blue-900">
                  <div className="font-semibold">{selectedForm.title}</div>
                  <div className="mt-2 grid gap-2 md:grid-cols-3">
                    <a className="rounded-md bg-white px-3 py-2 text-blue-700 hover:underline" href={studentFormUrl} target="_blank" rel="noreferrer">
                      Student login link
                    </a>
                    <a className="rounded-md bg-white px-3 py-2 text-blue-700 hover:underline" href={portalUrl} target="_blank" rel="noreferrer">
                      Direct portal link
                    </a>
                    <a className="rounded-md bg-white px-3 py-2 text-blue-700 hover:underline" href={publicApiUrl} target="_blank" rel="noreferrer">
                      Public form API
                    </a>
                  </div>
                  {isDefaultForm && (
                    <p className="mt-2 text-xs">
                      This is the existing B.Tech 2026 form. Students should use the student login link and this form will open after login.
                    </p>
                  )}
                </div>
              )}
              <div className="grid gap-4 md:grid-cols-2">
                <label className="block">
                  <span className="mb-1 block text-sm font-medium">Title</span>
                  <input disabled={isDefaultForm} value={editor.title} onChange={(e) => setEditor((prev) => ({ ...prev, title: e.target.value }))} className="w-full rounded-md border px-3 py-2 disabled:bg-gray-100" />
                </label>
                <label className="block">
                  <span className="mb-1 block text-sm font-medium">Slug</span>
                  <input disabled={isDefaultForm} value={editor.slug} onChange={(e) => setEditor((prev) => ({ ...prev, slug: e.target.value }))} className="w-full rounded-md border px-3 py-2 disabled:bg-gray-100" />
                </label>
                <label className="block md:col-span-2">
                  <span className="mb-1 block text-sm font-medium">Description</span>
                  <textarea disabled={isDefaultForm} value={editor.description} onChange={(e) => setEditor((prev) => ({ ...prev, description: e.target.value }))} className="min-h-20 w-full rounded-md border px-3 py-2 disabled:bg-gray-100" />
                </label>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button onClick={saveForm} disabled={isDefaultForm} className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">Save Form</button>
                {selectedId && !isDefaultForm && (
                  <button onClick={publishToggle} className="rounded-md border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700">
                    {editor.status === "published" ? "Unpublish" : "Publish"}
                  </button>
                )}
              </div>
            </section>

            <section className="rounded-lg border border-gray-200 bg-white p-5">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Fields</h2>
                <button onClick={addField} disabled={isDefaultForm} className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50">Add Field</button>
              </div>
              <div className="space-y-3">
                {editor.fields.map((field, index) => (
                  <div key={`${field.field_key}-${index}`} className="grid gap-3 rounded-md border border-gray-200 p-3 md:grid-cols-6">
                    <input disabled={isDefaultForm} placeholder="Section" value={field.section || ""} onChange={(e) => updateField(index, "section", e.target.value)} className="rounded-md border px-2 py-2 text-sm disabled:bg-gray-100" />
                    <input disabled={isDefaultForm} placeholder="Field key" value={field.field_key || ""} onChange={(e) => updateField(index, "field_key", e.target.value)} className="rounded-md border px-2 py-2 text-sm disabled:bg-gray-100" />
                    <input disabled={isDefaultForm} placeholder="Label" value={field.label || ""} onChange={(e) => updateField(index, "label", e.target.value)} className="rounded-md border px-2 py-2 text-sm md:col-span-2 disabled:bg-gray-100" />
                    <select disabled={isDefaultForm} value={field.field_type || "text"} onChange={(e) => updateField(index, "field_type", e.target.value)} className="rounded-md border px-2 py-2 text-sm disabled:bg-gray-100">
                      {["text", "email", "tel", "date", "number", "select", "textarea", "file"].map((type) => <option key={type}>{type}</option>)}
                    </select>
                    <label className="flex items-center gap-2 text-sm">
                      <input disabled={isDefaultForm} type="checkbox" checked={Boolean(field.required)} onChange={(e) => updateField(index, "required", e.target.checked)} />
                      Required
                    </label>
                    <input
                      placeholder="Options, comma separated"
                      disabled={isDefaultForm}
                      value={Array.isArray(field.options) ? field.options.join(", ") : field.options || ""}
                      onChange={(e) => updateField(index, "options", e.target.value)}
                      className="rounded-md border px-2 py-2 text-sm md:col-span-5 disabled:bg-gray-100"
                    />
                    <button
                      disabled={isDefaultForm}
                      onClick={() => setEditor((prev) => ({ ...prev, fields: prev.fields.filter((_, i) => i !== index) }))}
                      className="rounded-md border border-red-200 px-2 py-2 text-sm text-red-600 disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-lg border border-gray-200 bg-white p-5">
              <h2 className="mb-3 text-lg font-semibold">Responses</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-gray-100 text-left text-gray-600">
                    <tr>
                      <th className="px-3 py-2">Student ID</th>
                      <th className="px-3 py-2">Submitted By</th>
                      <th className="px-3 py-2">Status</th>
                      <th className="px-3 py-2">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {responses.map((response) => (
                      <tr key={response.id} className="border-t">
                        <td className="px-3 py-2">{response.student_id}</td>
                        <td className="px-3 py-2">{response.submitted_by}</td>
                        <td className="px-3 py-2">{response.status}</td>
                        <td className="px-3 py-2">{response.created_at}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </main>
        </div>
      </div>
      <ToastContainer />
    </div>
  );
}
