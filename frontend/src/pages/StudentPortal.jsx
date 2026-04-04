import React, { useEffect, useMemo, useState } from "react";
import API from "../api";
import { useAuth } from "../auth/AuthContext";

const tenthBoardOptions = ["TG BSE", "CBSE", "AP BSE", "ACE and A Level", "IBDP", "ICSE", "Other"];
const twelfthBoardOptions = ["TG BIE", "CBSE", "AP BIE", "ACE and A Level", "IBDP", "ICSE", "Other"];
const casteOptions = ["OC", "BC-A", "BC-B", "BC-C", "BC-D", "BC-E", "SC", "ST"];
const incomeOptions = ["Below 1 lakhs", "Below 1.5 lakhs", "Below 2 lakhs", "Below 2.5 lakhs", "Below 8 lakhs", "Above 8 lakhs"];
const bloodGroups = ["A +", "A -", "B +", "B -", "O +", "O -", "AB +", "AB -"];
const programOptions = [
  { value: "BTECH", label: "B.Tech" },
  { value: "MTECH", label: "M.Tech" },
];
const fallbackCatalog = {
  programs: [
    {
      code: "BTECH",
      label: "B.Tech",
      branches: [
        { code: "aids", label: "AIDS" },
        { code: "ae", label: "AE" },
        { code: "ce", label: "CE" },
        { code: "csbs", label: "CSBS" },
        { code: "cse", label: "CSE" },
        { code: "aiml", label: "AIML" },
        { code: "cseds", label: "CSE-DS" },
        { code: "csecys", label: "CSE-CYS" },
        { code: "cseiot", label: "CSE-IOT" },
        { code: "eee", label: "EEE" },
        { code: "ece", label: "ECE" },
        { code: "eie", label: "EIE" },
        { code: "it", label: "IT" },
        { code: "me", label: "ME" },
        { code: "vlsi", label: "VLSI" },
        { code: "biotechnology", label: "Biotechnology" },
        { code: "roboticsandai", label: "Robotics and AI" },
      ],
    },
    {
      code: "MTECH",
      label: "M.Tech",
      branches: [
        { code: "cse", label: "CSE" },
        { code: "ece", label: "ECE" },
        { code: "eee", label: "EEE" },
        { code: "me", label: "ME" },
        { code: "vlsi", label: "VLSI" },
      ],
    },
  ],
};

const initialForm = {
  student_name: "",
  father_name: "",
  mother_name: "",
  date_of_birth: "",
  gender: "Male",
  aadhaar_card_number: "",
  mother_tongue: "",
  student_phone: "",
  father_phone: "",
  mother_phone: "",
  student_email: "",
  father_email: "",
  mother_email: "",
  father_profession_and_designation: "",
  mother_profession_and_designation: "",
  primary_contact_person: "Father",
  address_dno: "",
  address_street: "",
  address_village_town: "",
  address_mandal: "",
  address_district: "",
  address_state: "",
  address_pincode: "",
  rural_urban: "Rural",
  ews_status: "No",
  category_name: "OC",
  caste_as_per_tc: "",
  ebc_status: "No",
  income: "Below 8 lakhs",
  minority: "No",
  blood_group: "O +",
  ph_status: "No",
  scribe: "No",
  tenth_board_name: "TG BSE",
  twelfth_board_name: "TG BIE",
  eapcet_ht_no: "",
  eapcet_rank: "",
  jee_ht_no: "",
  jee_mains_rank: "",
  program_level: "BTECH",
  branch_code: "cse",
  degree_code: "cse",
  admission_category: "Convenor",
};

const initialFiles = {
  tenth_memo: null,
  twelfth_memo: null,
  aadhaar: null,
  transfer_certificate: null,
  eapcet_rank_card: null,
  jee_rank_card: null,
};

const requiredDocTypes = ["tenth_memo", "twelfth_memo", "aadhaar", "transfer_certificate"];

const StudentPortal = () => {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(initialForm);
  const [files, setFiles] = useState(initialFiles);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [catalog, setCatalog] = useState(fallbackCatalog);
  const { isAuthenticated, role } = useAuth();

  const availableBranches = useMemo(() => {
    const selectedProgram = catalog.programs.find(
      (p) => p.code === String(form.program_level || "").toUpperCase()
    );
    return selectedProgram?.branches || [];
  }, [catalog, form.program_level]);

  useEffect(() => {
    let mounted = true;
    API.get("/meta/programs-branches")
      .then((res) => {
        if (!mounted) return;
        if (res?.data?.programs?.length) {
          setCatalog(res.data);
        }
      })
      .catch(() => setCatalog(fallbackCatalog));
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    const currentBranch = String(form.branch_code || "").toLowerCase();
    const validBranches = availableBranches.map((b) => String(b.code || "").toLowerCase());
    if (validBranches.length && !validBranches.includes(currentBranch)) {
      const nextBranch = validBranches[0];
      setForm((prev) => ({ ...prev, branch_code: nextBranch, degree_code: nextBranch }));
    }
  }, [availableBranches, form.branch_code]);

  const stepTitle = useMemo(() => {
    if (step === 1) return "Personal and Contact Details";
    if (step === 2) return "Address, Category and Academic Details";
    return "Document Uploads";
  }, [step]);

  const updateField = (field, value) => {
    setForm((prev) => {
      if (field === "branch_code") {
        const normalized = String(value || "").toLowerCase();
        return { ...prev, branch_code: normalized, degree_code: normalized };
      }
      if (field === "program_level") {
        return { ...prev, program_level: String(value || "").toUpperCase() };
      }
      return { ...prev, [field]: value };
    });
  };

  const validateStep = () => {
    setError("");

    if (step === 1) {
      const required = [
        "student_name",
        "father_name",
        "mother_name",
        "date_of_birth",
        "aadhaar_card_number",
        "mother_tongue",
        "student_phone",
        "father_phone",
        "mother_phone",
        "student_email",
        "father_profession_and_designation",
        "mother_profession_and_designation",
      ];
      for (const field of required) {
        if (!String(form[field] || "").trim()) {
          setError(`Please fill ${field.replace(/_/g, " ")}`);
          return false;
        }
      }
      const aadhaar = String(form.aadhaar_card_number || "").replace(/\D/g, "");
      if (aadhaar.length !== 12) {
        setError("Aadhaar number must be 12 digits");
        return false;
      }
      if (!/^\d{10}$/.test(String(form.student_phone || ""))) {
        setError("Student phone number must be 10 digits");
        return false;
      }
    }

    if (step === 2) {
      const required = [
        "address_dno",
        "address_street",
        "address_village_town",
        "address_mandal",
        "address_district",
        "address_state",
        "address_pincode",
        "tenth_board_name",
        "twelfth_board_name",
        "program_level",
        "branch_code",
      ];
      for (const field of required) {
        if (!String(form[field] || "").trim()) {
          setError(`Please fill ${field.replace(/_/g, " ")}`);
          return false;
        }
      }
    }

    if (step === 3) {
      for (const docType of requiredDocTypes) {
        if (!files[docType]) {
          setError(`Please upload required document: ${docType.replace(/_/g, " ")}`);
          return false;
        }
      }
    }

    return true;
  };

  const nextStep = () => {
    if (!validateStep()) return;
    setStep((prev) => Math.min(prev + 1, 3));
  };

  const prevStep = () => {
    setError("");
    setStep((prev) => Math.max(prev - 1, 1));
  };

  const handleFileChange = (docType, file) => {
    setFiles((prev) => ({ ...prev, [docType]: file || null }));
  };

  const submitApplication = async () => {
    if (!validateStep()) return;

    setIsSubmitting(true);
    setError("");

    try {
      const payload = {
        ...form,
        aadhaar_card_number: String(form.aadhaar_card_number || "").replace(/\D/g, ""),
        branch_code: String(form.branch_code || "").toLowerCase(),
        degree_code: String(form.degree_code || form.branch_code || "").toLowerCase(),
        program_level: String(form.program_level || "BTECH").toUpperCase(),
      };

      const response = await API.post("/applications", payload);
      const studentId = response?.data?.student_id;
      const applicationReference = response?.data?.application_reference;

      if (!studentId) {
        throw new Error("Application submitted but no student ID returned");
      }

      const docUploadOrder = [
        "tenth_memo",
        "twelfth_memo",
        "aadhaar",
        "transfer_certificate",
        "eapcet_rank_card",
        "jee_rank_card",
      ];

      for (const docType of docUploadOrder) {
        const file = files[docType];
        if (!file) continue;

        const formData = new FormData();
        formData.append("file", file);
        await API.post(`/applications/${studentId}/documents/${docType}`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }

      setResult({ studentId, applicationReference });
      setStep(1);
      setForm(initialForm);
      setFiles(initialFiles);
    } catch (err) {
      if ([401, 403].includes(err?.response?.status)) {
        setError("Please sign in with your student account to submit applications.");
      } else {
        setError(err?.response?.data?.detail || err?.message || "Failed to submit application");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderInput = (label, field, type = "text") => (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <input
        type={type}
        value={form[field] || ""}
        onChange={(e) => updateField(field, e.target.value)}
        className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
      />
    </label>
  );

  const renderSelect = (label, field, options) => (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-gray-700">{label}</span>
      <select
        value={form[field] || ""}
        onChange={(e) => updateField(field, e.target.value)}
        className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
      >
        {options.map((opt) => {
          const option = typeof opt === "string" ? { value: opt, label: opt } : opt;
          return (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
          );
        })}
      </select>
    </label>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white px-4 py-8">
      <div className="mx-auto max-w-5xl rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900">Student Admissions Portal</h1>
        <p className="mt-1 text-sm text-gray-600">
          Multi-step admissions form for all programs (local-first storage).
        </p>
        {(!isAuthenticated || role !== "student") && (
          <p className="mt-2 text-sm text-amber-700">
            Sign in with a student account before final submission.
          </p>
        )}

        <div className="mt-6 grid grid-cols-3 gap-2 text-sm">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className={`rounded-md px-3 py-2 text-center font-medium ${
                step >= n ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600"
              }`}
            >
              Step {n}
            </div>
          ))}
        </div>

        <h2 className="mt-6 text-lg font-semibold text-gray-900">{stepTitle}</h2>

        {error && (
          <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-4 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-800">
            Application submitted successfully. Reference: <strong>{result.applicationReference}</strong>, Student ID:{" "}
            <strong>{result.studentId}</strong>
          </div>
        )}

        {step === 1 && (
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            {renderInput("Name of the Student *", "student_name")}
            {renderInput("Father's Name *", "father_name")}
            {renderInput("Mother's Name *", "mother_name")}
            {renderInput("Date of Birth *", "date_of_birth", "date")}
            {renderSelect("Gender *", "gender", ["Male", "Female", "Transgender"])}
            {renderInput("Aadhaar Card Number *", "aadhaar_card_number")}
            {renderInput("Mother Tongue *", "mother_tongue")}
            {renderInput("Student Phone Number *", "student_phone")}
            {renderInput("Father Phone Number *", "father_phone")}
            {renderInput("Mother Phone Number *", "mother_phone")}
            {renderInput("Student Email *", "student_email", "email")}
            {renderInput("Father Email", "father_email", "email")}
            {renderInput("Mother Email", "mother_email", "email")}
            {renderInput("Father Profession and Designation *", "father_profession_and_designation")}
            {renderInput("Mother Profession and Designation *", "mother_profession_and_designation")}
            {renderSelect("Primary Contact Person *", "primary_contact_person", ["Father", "Mother"])}
          </div>
        )}

        {step === 2 && (
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            {renderInput("Door No *", "address_dno")}
            {renderInput("Street Name *", "address_street")}
            {renderInput("Village Name *", "address_village_town")}
            {renderInput("Mandal Name *", "address_mandal")}
            {renderInput("District Name *", "address_district")}
            {renderInput("State Name *", "address_state")}
            {renderInput("Pincode *", "address_pincode")}
            {renderSelect("Rural / Urban *", "rural_urban", ["Rural", "Urban"])}
            {renderSelect("EWS Status *", "ews_status", ["Yes", "No"])}
            {renderSelect("Caste Category *", "category_name", casteOptions)}
            {renderInput("Caste as per TC", "caste_as_per_tc")}
            {renderSelect("EBC Status *", "ebc_status", ["Yes", "No"])}
            {renderSelect("Annual Income of Parent *", "income", incomeOptions)}
            {renderSelect("Minority *", "minority", ["Yes", "No"])}
            {renderSelect("Blood Group *", "blood_group", bloodGroups)}
            {renderSelect("PH Status *", "ph_status", ["Yes", "No"])}
            {renderSelect("PH Scribe *", "scribe", ["Yes", "No"])}
            {renderSelect("Program *", "program_level", programOptions)}
            {renderSelect("Branch *", "branch_code", availableBranches)}
            {renderSelect("10th Board *", "tenth_board_name", tenthBoardOptions)}
            {renderSelect("12th Board Name *", "twelfth_board_name", twelfthBoardOptions)}
            {renderInput("EAPCET Hall Ticket No", "eapcet_ht_no")}
            {renderInput("EAPCET Rank", "eapcet_rank")}
            {renderInput("JEE Hall Ticket No", "jee_ht_no")}
            {renderInput("JEE CRL Rank", "jee_mains_rank")}
          </div>
        )}

        {step === 3 && (
          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
            {[
              ["10th MEMO *", "tenth_memo"],
              ["12th MEMO *", "twelfth_memo"],
              ["Aadhaar Card *", "aadhaar"],
              ["Transfer Certificate / Bonafide *", "transfer_certificate"],
              ["EAPCET Rank Card", "eapcet_rank_card"],
              ["JEE Rank Card", "jee_rank_card"],
            ].map(([label, docType]) => (
              <label key={docType} className="block rounded-md border border-gray-200 p-3">
                <span className="mb-2 block text-sm font-medium text-gray-700">{label}</span>
                <input
                  type="file"
                  accept=".pdf,image/*"
                  onChange={(e) => handleFileChange(docType, e.target.files?.[0] || null)}
                  className="w-full text-sm"
                />
              </label>
            ))}
            <p className="text-xs text-gray-500 md:col-span-2">
              Allowed file types: PDF/JPG/JPEG/PNG. Max size per file: 5MB.
            </p>
          </div>
        )}

        <div className="mt-6 flex items-center justify-between">
          <button
            onClick={prevStep}
            disabled={step === 1 || isSubmitting}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>

          {step < 3 ? (
            <button
              onClick={nextStep}
              disabled={isSubmitting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Next
            </button>
          ) : (
            <button
              onClick={submitApplication}
              disabled={isSubmitting}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isSubmitting ? "Submitting..." : "Submit Application"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default StudentPortal;
