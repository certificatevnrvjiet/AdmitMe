import React, { useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import API from "../api";
import { useAuth } from "../auth/AuthContext";

const digitOnlyFields = new Set([
  "student_phone",
  "father_phone",
  "mother_phone",
  "parent_phone",
  "aadhaar_card_number",
]);

const defaultValueFor = (field) => {
  if (field.field_key === "consent") return "";
  if (field.field_type === "select" && field.options?.length) return field.options[0];
  if (field.field_key === "branch") return "";
  if (field.field_key === "admission_category") return "Convenor";
  return "";
};

const fallbackAdmissionForm = {
  id: "default-admission",
  title: "B.Tech 2026 Admission Form",
  description: "Submit B.Tech 2026 admission details and supporting documents.",
  slug: "btech-2026",
  status: "published",
  fields: [
    { section: "Personal", field_key: "student_name", label: "Name of the Student", field_type: "text", required: true, sort_order: 10 },
    { section: "Personal", field_key: "father_name", label: "Father's Name", field_type: "text", required: true, sort_order: 20 },
    { section: "Personal", field_key: "mother_name", label: "Mother's Name", field_type: "text", required: true, sort_order: 30 },
    { section: "Personal", field_key: "date_of_birth", label: "Date of Birth", field_type: "date", required: true, sort_order: 40 },
    { section: "Personal", field_key: "gender", label: "Gender", field_type: "select", required: true, options: ["Male", "Female", "Transgender"], sort_order: 50 },
    { section: "Personal", field_key: "aadhaar_card_number", label: "Aadhaar Card Number", field_type: "text", required: true, sort_order: 60 },
    { section: "Contact", field_key: "mother_tongue", label: "Mother Tongue", field_type: "text", required: true, sort_order: 70 },
    { section: "Contact", field_key: "student_phone", label: "Student Phone Number", field_type: "tel", required: true, sort_order: 80 },
    { section: "Contact", field_key: "father_phone", label: "Father Phone Number", field_type: "tel", required: true, sort_order: 90 },
    { section: "Contact", field_key: "mother_phone", label: "Mother Phone Number", field_type: "tel", required: true, sort_order: 100 },
    { section: "Contact", field_key: "student_email", label: "Student Email", field_type: "email", required: true, sort_order: 110 },
    { section: "Address", field_key: "address_dno", label: "Door No", field_type: "text", required: true, sort_order: 120 },
    { section: "Address", field_key: "address_street", label: "Street Name", field_type: "text", required: true, sort_order: 130 },
    { section: "Address", field_key: "address_village_town", label: "Village/Town", field_type: "text", required: true, sort_order: 140 },
    { section: "Address", field_key: "address_mandal", label: "Mandal", field_type: "text", required: true, sort_order: 150 },
    { section: "Address", field_key: "address_district", label: "District", field_type: "text", required: true, sort_order: 160 },
    { section: "Address", field_key: "address_state", label: "State", field_type: "text", required: true, sort_order: 170 },
    { section: "Address", field_key: "address_pincode", label: "Pincode", field_type: "text", required: true, sort_order: 180 },
    { section: "Academic", field_key: "branch", label: "Branch", field_type: "select", required: true, options: [], sort_order: 200 },
    { section: "Category", field_key: "caste_as_per_tc", label: "Caste as per TC", field_type: "text", required: true, sort_order: 205 },
    { section: "Academic", field_key: "tenth_board_name", label: "10th Board", field_type: "select", required: true, options: ["TG BSE", "CBSE", "AP BSE", "ACE and A Level", "IBDP", "ICSE", "Other"], sort_order: 210 },
    { section: "Academic", field_key: "twelfth_board_name", label: "12th Board", field_type: "select", required: true, options: ["TG BIE", "CBSE", "AP BIE", "ACE and A Level", "IBDP", "ICSE", "Other"], sort_order: 220 },
    { section: "Documents", field_key: "tenth_memo", label: "10th Memo", field_type: "file", required: true, maps_to_student_field: false, sort_order: 230 },
    { section: "Documents", field_key: "twelfth_memo", label: "12th Memo", field_type: "file", required: true, maps_to_student_field: false, sort_order: 240 },
    { section: "Documents", field_key: "aadhaar", label: "Aadhaar Card", field_type: "file", required: true, maps_to_student_field: false, sort_order: 250 },
    { section: "Documents", field_key: "transfer_certificate", label: "Transfer Certificate / Bonafide", field_type: "file", required: true, maps_to_student_field: false, sort_order: 260 },
    { section: "Declaration", field_key: "consent", label: "Consent", field_type: "select", required: true, options: ["I Consent"], sort_order: 270 },
  ],
};

const buildInitialForm = (nextForm) => {
  const initial = {};
  (nextForm.fields || []).forEach((field) => {
    if (field.field_type !== "file") initial[field.field_key] = defaultValueFor(field);
  });
  return initial;
};

const normalizeFormDefinition = (nextForm) => ({
  ...nextForm,
  fields: (nextForm.fields || []).map((field) => {
    if (field.field_key === "caste_as_per_tc") {
      return { ...field, required: true };
    }
    return field;
  }),
});

export default function StudentPortal() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [formDefinition, setFormDefinition] = useState(null);
  const [availableForms, setAvailableForms] = useState([]);
  const [formResponses, setFormResponses] = useState({});
  const [formsLoading, setFormsLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({});
  const [files, setFiles] = useState({});
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedResponse, setSubmittedResponse] = useState(null);
  const [submittedLoading, setSubmittedLoading] = useState(false);
  const [showSubmittedView, setShowSubmittedView] = useState(false);
  const [programCatalog, setProgramCatalog] = useState({ programs: [], aliases: {} });
  const { isAuthenticated, role } = useAuth();
  const isFormsHome = !slug;
  const isEditMode = searchParams.get("mode") === "edit";

  useEffect(() => {
    if (isFormsHome) return undefined;
    let mounted = true;
    API.get(`/public/forms/${slug}`)
      .then((res) => {
        if (!mounted) return;
        const nextForm = normalizeFormDefinition(res.data.form);
        setFormDefinition(nextForm);
        setForm(buildInitialForm(nextForm));
      })
      .catch(() => {
        if (!mounted) return;
        const nextForm = normalizeFormDefinition(fallbackAdmissionForm);
        setFormDefinition(nextForm);
        setForm(buildInitialForm(nextForm));
      });
    return () => {
      mounted = false;
    };
  }, [isFormsHome, slug]);

  useEffect(() => {
    let mounted = true;
    API.get("/meta/programs-branches")
      .then(({ data }) => {
        if (mounted) setProgramCatalog(data || { programs: [], aliases: {} });
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!isFormsHome || !isAuthenticated || role !== "student") return undefined;
    let mounted = true;
    setFormsLoading(true);
    setError("");
    API.get("/public/forms")
      .then(async (res) => {
        if (!mounted) return;
        const forms = res.data.forms || [];
        setAvailableForms(forms);
        const settled = await Promise.allSettled(
          forms.map((formItem) => API.get(`/forms/${formItem.id}/responses/me`))
        );
        if (!mounted) return;
        const nextResponses = {};
        settled.forEach((entry, index) => {
          if (entry.status === "fulfilled") {
            nextResponses[forms[index].id] = entry.value.data.response;
          }
        });
        setFormResponses(nextResponses);
      })
      .catch((err) => {
        if (!mounted) return;
        setAvailableForms([fallbackAdmissionForm]);
        setError(err?.response?.data?.detail || "Unable to load admission forms");
      })
      .finally(() => {
        if (mounted) setFormsLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, [isFormsHome, isAuthenticated, role]);

  const sections = useMemo(() => {
    const groups = [];
    const byName = new Map();
    (formDefinition?.fields || []).forEach((field) => {
      const section = field.section || "General";
      if (!byName.has(section)) {
        byName.set(section, []);
        groups.push({ name: section, fields: byName.get(section) });
      }
      byName.get(section).push(field);
    });
    return groups.map((group) => ({
      ...group,
      fields: [...group.fields].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0)),
    }));
  }, [formDefinition]);

  const activeSection = sections[step] || sections[0];
  const branchOptions = useMemo(() => {
    const matchingProgram = (programCatalog.programs || []).find((item) => item.code === "BTECH");
    return matchingProgram?.branches || [];
  }, [programCatalog]);

  const fetchSubmittedResponse = async (formId) => {
    if (!formId || !isAuthenticated || role !== "student") return;
    setSubmittedLoading(true);
    try {
      const { data } = await API.get(`/forms/${formId}/responses/me`);
      const response = data.response;
      setSubmittedResponse(response);
      setShowSubmittedView(!isEditMode);
      if (response?.response_data) {
        const nextValues = { ...buildInitialForm(formDefinition), ...response.response_data };
        delete nextValues._custom;
        setForm(nextValues);
      }
    } catch (err) {
      if (err?.response?.status !== 404) {
        setError(err?.response?.data?.detail || "Unable to load submitted form");
      }
      setSubmittedResponse(null);
      setShowSubmittedView(false);
    } finally {
      setSubmittedLoading(false);
    }
  };

  useEffect(() => {
    if (formDefinition?.id && isAuthenticated && role === "student") {
      fetchSubmittedResponse(formDefinition.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formDefinition?.id, isAuthenticated, role]);

  const updateField = (field, value) => {
    const nextValue = digitOnlyFields.has(field) ? String(value || "").replace(/\D/g, "") : value;
    setForm((prev) => {
      if (field === "branch") {
        return { ...prev, branch: String(nextValue || "").toLowerCase() };
      }
      return { ...prev, [field]: nextValue };
    });
  };

  const validateSection = () => {
    setError("");
    for (const field of activeSection?.fields || []) {
      if (field.required && field.field_type !== "file" && !String(form[field.field_key] || "").trim()) {
        setError(`Please fill ${field.label}`);
        return false;
      }
      if (field.required && field.field_type === "file" && !files[field.field_key]) {
        setError(`Please upload ${field.label}`);
        return false;
      }
    }
    if (activeSection?.fields?.some((field) => field.field_key === "aadhaar_card_number")) {
      const aadhaar = String(form.aadhaar_card_number || "").replace(/\D/g, "");
      if (aadhaar.length !== 12) {
        setError("Aadhaar number must be 12 digits");
        return false;
      }
    }
    for (const field of activeSection?.fields || []) {
      if ((field.field_type === "tel" || digitOnlyFields.has(field.field_key)) && /\D/.test(String(form[field.field_key] || ""))) {
        setError(`${field.label} must contain digits only`);
        return false;
      }
    }
    return true;
  };

  const submit = async () => {
    if (!validateSection()) return;
    if (!isAuthenticated || role !== "student") {
      return;
    }
    setIsSubmitting(true);
    setError("");
    try {
      const responseData = {
        ...form,
        aadhaar_card_number: String(form.aadhaar_card_number || "").replace(/\D/g, ""),
        branch: String(form.branch || "").toLowerCase(),
      };
      const response = await API.post(`/forms/${formDefinition.id}/responses`, {
        response_data: responseData,
      });
      const studentId = response.data.student_id;
      const uploadFields = (formDefinition.fields || []).filter((field) => field.field_type === "file");
      for (const field of uploadFields) {
        const file = files[field.field_key];
        if (!file) continue;
        const formData = new FormData();
        formData.append("file", file);
        await API.post(`/applications/${studentId}/documents/${field.field_key}`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      setResult(response.data);
      await fetchSubmittedResponse(formDefinition.id);
      toast.success("Application submitted successfully");
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || "Failed to submit application");
    } finally {
      setIsSubmitting(false);
    }
  };

  const downloadBlob = async (url, fallbackName) => {
    try {
      const response = await API.get(url, { responseType: "blob" });
      const disposition = response.headers?.["content-disposition"] || "";
      const encodedMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
      const plainMatch = disposition.match(/filename="?([^"]+)"?/i);
      const filename = encodedMatch?.[1]
        ? decodeURIComponent(encodedMatch[1])
        : plainMatch?.[1] || fallbackName;
      const objectUrl = URL.createObjectURL(response.data);
      const anchor = document.createElement("a");
      anchor.href = objectUrl;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setError(err?.response?.data?.detail || "Download failed");
    }
  };

  const documentDownloadName = (field, doc) => {
    const mime = String(doc?.mime_type || "").toLowerCase();
    const extension = mime.includes("png")
      ? "png"
      : mime.includes("jpeg") || mime.includes("jpg")
      ? "jpg"
      : mime.includes("pdf")
      ? "pdf"
      : "bin";
    return `${field.field_key}.${extension}`;
  };

  const renderField = (field) => {
    if (field.field_type === "file") {
      return (
        <label key={field.field_key} className="block rounded-md border border-gray-200 dark:border-gray-700 p-3">
          <span className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
            {field.label}{field.required ? " *" : ""}
          </span>
          <input
            type="file"
            accept=".pdf,image/*"
            onChange={(event) => setFiles((prev) => ({ ...prev, [field.field_key]: event.target.files?.[0] || null }))}
            className="w-full text-sm text-gray-700 dark:text-gray-300"
          />
          {field.help_text && <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">{field.help_text}</p>}
        </label>
      );
    }

    const options = field.field_key === "branch" && !field.options?.length ? branchOptions : field.options || [];
    if (field.field_type === "select" || options.length) {
      return (
        <label key={field.field_key} className="block">
          <span className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
            {field.label}{field.required ? " *" : ""}
          </span>
          <select
            value={form[field.field_key] || ""}
            onChange={(event) => updateField(field.field_key, event.target.value)}
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white px-3 py-2 focus:border-blue-500 focus:outline-none"
          >
            {field.required && <option value="">Select {field.label}</option>}
            {options.map((option) => {
              const value = typeof option === "string" ? option : option.code;
              const label = typeof option === "string" ? option.toUpperCase() : option.label;
              return (
              <option key={value} value={value} className="dark:bg-gray-800">{label}</option>
              );
            })}
          </select>
        </label>
      );
    }

    return (
      <label key={field.field_key} className="block">
        <span className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          {field.label}{field.required ? " *" : ""}
        </span>
        {field.field_type === "textarea" ? (
          <textarea
            value={form[field.field_key] || ""}
            onChange={(event) => updateField(field.field_key, event.target.value)}
            className="min-h-24 w-full rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white px-3 py-2 focus:border-blue-500 focus:outline-none"
          />
        ) : (
          <input
            type={field.field_type === "tel" ? "text" : field.field_type || "text"}
            inputMode={field.field_type === "tel" || digitOnlyFields.has(field.field_key) ? "numeric" : undefined}
            pattern={field.field_type === "tel" || digitOnlyFields.has(field.field_key) ? "[0-9]*" : undefined}
            value={form[field.field_key] || ""}
            onChange={(event) => updateField(field.field_key, event.target.value)}
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white px-3 py-2 focus:border-blue-500 focus:outline-none"
          />
        )}
      </label>
    );
  };

  const renderSubmittedView = () => {
    const responseData = submittedResponse?.response_data || {};
    const documentByType = new Map((submittedResponse?.documents || []).map((doc) => [doc.doc_type, doc]));
    return (
      <div className="mt-6 space-y-5">
        <div className="rounded-md border border-green-200 bg-green-50 dark:border-green-900/50 dark:bg-green-950/20 p-4 text-sm text-green-900 dark:text-green-300">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-semibold">Submitted application</p>
              <p className="mt-1">
                Status: <strong>{submittedResponse?.status || "submitted"}</strong>
                {submittedResponse?.student_id ? <> | Student ID: <strong>{submittedResponse.student_id}</strong></> : null}
              </p>
              {submittedResponse?.application_reference && (
                <p className="mt-1">Reference: <strong>{submittedResponse.application_reference}</strong></p>
              )}
            </div>
            <button
              type="button"
              onClick={() => {
                setShowSubmittedView(false);
                setError("");
              }}
              className="rounded-md bg-white dark:bg-gray-700 px-4 py-2 text-sm font-semibold text-green-800 dark:text-green-200 shadow-sm hover:bg-green-100 dark:hover:bg-gray-600"
            >
              Edit / Resubmit
            </button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => downloadBlob(`/forms/${formDefinition.id}/responses/me/application.pdf`, "application.pdf")}
              className="rounded-md bg-green-700 px-3 py-2 text-sm font-semibold text-white hover:bg-green-800"
            >
              Download Filled Application PDF
            </button>
            <button
              type="button"
              onClick={() => downloadBlob(`/forms/${formDefinition.id}/responses/me/documents.pdf`, "uploaded-documents.pdf")}
              className="rounded-md border border-green-300 dark:border-green-800 bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-green-800 dark:text-green-200 hover:bg-green-100 dark:hover:bg-gray-600"
            >
              Download All Documents PDF
            </button>
          </div>
        </div>

        {sections.map((section) => (
          <section key={section.name} className="rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{section.name}</h2>
            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
              {section.fields.map((field) => {
                const doc = documentByType.get(field.field_key);
                const value = field.field_type === "file"
                  ? (doc ? `${doc.status || "uploaded"} (${doc.mime_type || doc.provider || "document"})` : "Not uploaded")
                  : responseData[field.field_key];
                return (
                  <div key={field.field_key} className="rounded-md bg-gray-50 dark:bg-gray-900/50 px-3 py-2">
                    <p className="text-xs font-medium uppercase text-gray-500 dark:text-gray-400">{field.label}</p>
                    <div className="mt-1 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <p className="break-words text-sm text-gray-900 dark:text-white">{String(value || "-")}</p>
                      {field.field_type === "file" && doc && (
                        <button
                          type="button"
                          onClick={() => downloadBlob(
                            `/forms/${formDefinition.id}/responses/me/documents/${field.field_key}/download`,
                            documentDownloadName(field, doc)
                          )}
                          className="shrink-0 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-2 py-1 text-xs font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600"
                        >
                          Download
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    );
  };

  if (!isAuthenticated || role !== "student") {
    return <Navigate to="/student-login" replace />;
  }

  if (isFormsHome) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-gray-900 px-4 py-8">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Student Admission Forms</h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">
              Select a published form, view submitted applications, or continue editing a form.
            </p>
            {formsLoading && (
              <div className="mt-4 rounded-md border border-blue-100 bg-blue-50 dark:border-blue-900/55 dark:bg-blue-950/20 px-3 py-2 text-sm text-blue-700 dark:text-blue-300">
                Loading your forms...
              </div>
            )}
            {error && (
              <div className="mt-4 rounded-md border border-red-200 bg-red-50 dark:border-red-900/55 dark:bg-red-950/20 px-3 py-2 text-sm text-red-700 dark:text-red-300">
                {error}
              </div>
            )}
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              {(availableForms.length ? availableForms : [fallbackAdmissionForm]).map((formItem) => {
                const response = formResponses[formItem.id];
                return (
                  <article key={formItem.id || formItem.slug} className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{formItem.title}</h2>
                        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{formItem.description}</p>
                      </div>
                      <span className={`shrink-0 rounded-full px-2 py-1 text-xs font-semibold ${
                        response ? "bg-green-100 text-green-700 dark:bg-green-950/30 dark:text-green-300" : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"
                      }`}>
                        {response ? "Submitted" : "Not filled"}
                      </span>
                    </div>
                    {response && (
                      <div className="mt-4 rounded-md bg-gray-50 dark:bg-gray-900/50 p-3 text-sm text-gray-700 dark:text-gray-300">
                        <p>Student ID: <strong>{response.student_id || "-"}</strong></p>
                        <p>Status: <strong>{response.status || "submitted"}</strong></p>
                        {response.application_reference && <p>Reference: <strong>{response.application_reference}</strong></p>}
                      </div>
                    )}
                    <div className="mt-4 flex flex-wrap gap-2">
                      {response && (
                        <button
                          type="button"
                          onClick={() => navigate(`/student-portal/${formItem.slug}?view=submitted`)}
                          className="rounded-md border border-blue-200 dark:border-blue-800 px-3 py-2 text-sm font-semibold text-blue-700 dark:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/30"
                        >
                          View Submitted
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => navigate(`/student-portal/${formItem.slug}${response ? "?mode=edit" : ""}`)}
                        className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                      >
                        {response ? "Edit / Resubmit" : "Fill Form"}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        </div>
        <ToastContainer />
      </div>
    );
  }

  if (!formDefinition && !error) {
    return <div className="min-h-screen px-4 py-8 text-center text-gray-600">Loading admission form...</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-gray-900 px-4 py-8">
      <div className="mx-auto max-w-5xl rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{formDefinition?.title || "Student Admissions Portal"}</h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">{formDefinition?.description}</p>
        {submittedLoading && (
          <div className="mt-4 rounded-md border border-blue-100 bg-blue-50 dark:border-blue-900/55 dark:bg-blue-950/20 px-3 py-2 text-sm text-blue-700 dark:text-blue-300">
            Checking your submitted form...
          </div>
        )}
        {submittedResponse && !showSubmittedView && (
          <div className="mt-4 flex flex-col gap-3 rounded-md border border-blue-100 bg-blue-50 dark:border-blue-900/55 dark:bg-blue-950/20 px-3 py-3 text-sm text-blue-800 dark:text-blue-300 md:flex-row md:items-center md:justify-between">
            <span>You already submitted this form. You can view it any time.</span>
            <button
              type="button"
              onClick={() => setShowSubmittedView(true)}
              className="rounded-md bg-white dark:bg-gray-700 px-3 py-2 font-semibold text-blue-700 dark:text-blue-300 shadow-sm"
            >
              View Submitted Form
            </button>
          </div>
        )}

        {showSubmittedView && submittedResponse ? renderSubmittedView() : (
          <>
        <div className="mt-6 grid gap-2 text-sm" style={{ gridTemplateColumns: `repeat(${Math.max(sections.length, 1)}, minmax(0, 1fr))` }}>
          {sections.map((section, index) => (
            <button
              key={section.name}
              type="button"
              onClick={() => {
                if (index <= step || validateSection()) setStep(index);
              }}
              className={`rounded-md px-3 py-2 text-center font-medium ${step >= index ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300"}`}
            >
              {section.name}
            </button>
          ))}
        </div>

        {error && <div className="mt-4 rounded-md border border-red-200 bg-red-50 dark:border-red-900/55 dark:bg-red-950/20 px-3 py-2 text-sm text-red-700 dark:text-red-300">{error}</div>}
        {result && (
          <div className="mt-4 rounded-md border border-green-200 bg-green-50 dark:border-green-900/55 dark:bg-green-950/20 px-3 py-2 text-sm text-green-800 dark:text-green-300">
            Application submitted successfully. Reference: <strong>{result.application_reference}</strong>, Student ID:{" "}
            <strong>{result.student_id}</strong>
          </div>
        )}

        <h2 className="mt-6 text-lg font-semibold text-gray-900 dark:text-white">{activeSection?.name}</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          {(activeSection?.fields || []).map(renderField)}
          {activeSection?.name === "Documents" && (
            <p className="text-xs text-gray-500 md:col-span-2">Allowed file types: PDF/JPG/JPEG/PNG. Max size per file: 5MB.</p>
          )}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={() => {
              setError("");
              setStep((prev) => Math.max(prev - 1, 0));
            }}
            disabled={step === 0 || isSubmitting}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>
          {step < sections.length - 1 ? (
            <button
              onClick={() => validateSection() && setStep((prev) => Math.min(prev + 1, sections.length - 1))}
              disabled={isSubmitting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next
            </button>
          ) : (
            <button
              onClick={submit}
              disabled={isSubmitting}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isSubmitting ? "Submitting..." : "Submit Application"}
            </button>
          )}
        </div>
          </>
        )}
      </div>
      <ToastContainer />
    </div>
  );
}
