import { useContext, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { FiEye, FiEyeOff, FiLogIn, FiUserPlus } from "react-icons/fi";
import API from "../api";
import { AuthContext, useAuth } from "../auth/AuthContext";
import { useTheme } from "../context/ThemeContext";

const StudentLoginPage = ({ initialMode = "login" }) => {
  const [mode, setMode] = useState(initialMode);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [publishedForms, setPublishedForms] = useState([]);
  const [selectedFormSlug, setSelectedFormSlug] = useState("btech-2026");
  const { isAuthenticated, role } = useContext(AuthContext);
  const { login } = useAuth();
  const { isDarkMode } = useTheme();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const requestedForm = searchParams.get("form");
    if (requestedForm) setSelectedFormSlug(requestedForm);
  }, [searchParams]);

  useEffect(() => {
    let mounted = true;
    API.get("/public/forms")
      .then((res) => {
        if (!mounted) return;
        const forms = res.data.forms || [];
        setPublishedForms(forms);
        if (!searchParams.get("form") && forms[0]?.slug) {
          setSelectedFormSlug(forms[0].slug);
        }
      })
      .catch(() => {
        if (!mounted) return;
        setPublishedForms([
          {
            id: "default-admission",
            title: "B.Tech 2026 Admission Form",
            description: "Submit B.Tech 2026 admission details and supporting documents.",
            slug: "btech-2026",
            status: "published",
          },
        ]);
      });
    return () => {
      mounted = false;
    };
  }, [searchParams]);

  useEffect(() => {
    if (isAuthenticated && role === "student") {
      navigate("/student-portal", { replace: true });
    }
  }, [isAuthenticated, role, navigate]);

  const resetMessages = () => {
    setError("");
    setSuccess("");
  };

  const handleLogin = async () => {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    const res = await API.post("/token", form);
    if (res.data.role !== "student") {
      setError("Please use the staff login for admin or department accounts.");
      return;
    }
    login(res.data.access_token, res.data.role);
    navigate("/student-portal");
  };

  const handleRegister = async () => {
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    const res = await API.post("/auth/student/register", {
      email: username,
      password,
      confirm_password: confirmPassword,
    });
    login(res.data.access_token, res.data.role);
    setSuccess("Student account created. Opening your admission forms...");
    navigate("/student-portal");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    resetMessages();

    try {
      if (mode === "register") {
        await handleRegister();
      } else {
        await handleLogin();
      }
    } catch (err) {
      setError(err.response?.data?.detail || (mode === "register" ? "Unable to create student account" : "Invalid student credentials"));
    }
  };

  return (
    <div className="min-h-[calc(100vh-65px)] bg-slate-50 dark:bg-gray-900 px-4 py-10">
      <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-[1fr_420px] md:items-center">
        <div className="hidden md:block">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">Student Admission Login</h1>
          <p className="mt-4 max-w-xl text-lg text-gray-600 dark:text-gray-300">
            Sign in with your student account to view the admission form, upload documents, and submit your application.
          </p>
          <div className="mt-6 max-w-xl space-y-3">
            {(publishedForms.length ? publishedForms : []).map((form) => (
              <button
                key={form.id || form.slug}
                type="button"
                onClick={() => setSelectedFormSlug(form.slug)}
                className={`w-full rounded-md border p-4 text-left transition ${
                  selectedFormSlug === form.slug
                    ? "border-blue-500 bg-blue-50 text-blue-900 dark:bg-blue-950/30 dark:text-blue-200"
                    : "border-gray-200 bg-white text-gray-700 hover:border-blue-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:border-blue-500"
                }`}
              >
                <div className="font-semibold">{form.title}</div>
                <div className="mt-1 text-sm opacity-80">{form.description}</div>
              </button>
            ))}
          </div>
        </div>

        <div className={`rounded-lg border p-8 shadow-sm ${isDarkMode ? "border-gray-700 bg-gray-800" : "border-gray-200 bg-white"}`}>
          <h2 className={`text-2xl font-bold ${isDarkMode ? "text-white" : "text-gray-900"}`}>
            {mode === "register" ? "Create Student Account" : "Student Login"}
          </h2>
          <p className={`mt-1 text-sm ${isDarkMode ? "text-gray-300" : "text-gray-600"}`}>
            {mode === "register" ? "Register before filling the admission form" : "Admission form access"}
          </p>

          <label className="mt-5 block">
            <span className={`mb-1 block text-sm font-medium ${isDarkMode ? "text-gray-200" : "text-gray-700"}`}>Admission Form</span>
            <select
              value={selectedFormSlug}
              onChange={(event) => setSelectedFormSlug(event.target.value)}
              className={`w-full rounded-md border px-3 py-2 focus:border-blue-500 focus:outline-none ${
                isDarkMode ? "border-gray-600 bg-gray-700 text-white" : "border-gray-300 bg-white text-gray-900"
              }`}
            >
              {(publishedForms.length
                ? publishedForms
                : [{ title: "B.Tech 2026 Admission Form", slug: "btech-2026" }]
              ).map((form) => (
                <option key={form.slug} value={form.slug}>{form.title}</option>
              ))}
            </select>
          </label>

          <div className="mt-5 grid grid-cols-2 rounded-md border border-gray-200 bg-gray-100 p-1 text-sm font-semibold dark:border-gray-700 dark:bg-gray-900">
            <button
              type="button"
              onClick={() => {
                setMode("login");
                resetMessages();
              }}
              className={`flex items-center justify-center gap-2 rounded px-3 py-2 ${
                mode === "login" ? "bg-white text-blue-700 shadow-sm dark:bg-gray-800 dark:text-blue-400" : "text-gray-600 dark:text-gray-400"
              }`}
            >
              <FiLogIn /> Login
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("register");
                resetMessages();
              }}
              className={`flex items-center justify-center gap-2 rounded px-3 py-2 ${
                mode === "register" ? "bg-white text-blue-700 shadow-sm dark:bg-gray-800 dark:text-blue-400" : "text-gray-600 dark:text-gray-400"
              }`}
            >
              <FiUserPlus /> Register
            </button>
          </div>

          {error && (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}
          {success && (
            <div className="mt-4 rounded-md border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
              {success}
            </div>
          )}

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className={`mb-1 block text-sm font-medium ${isDarkMode ? "text-gray-200" : "text-gray-700"}`}>Student Email</span>
              <input
                type="email"
                required
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                className={`w-full rounded-md border px-3 py-2 focus:border-blue-500 focus:outline-none ${
                  isDarkMode ? "border-gray-600 bg-gray-700 text-white" : "border-gray-300 bg-white text-gray-900"
                }`}
              />
            </label>

            <label className="block">
              <span className={`mb-1 block text-sm font-medium ${isDarkMode ? "text-gray-200" : "text-gray-700"}`}>Password</span>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className={`w-full rounded-md border px-3 py-2 pr-10 focus:border-blue-500 focus:outline-none ${
                    isDarkMode ? "border-gray-600 bg-gray-700 text-white" : "border-gray-300 bg-white text-gray-900"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 px-3 text-gray-500"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <FiEyeOff /> : <FiEye />}
                </button>
              </div>
            </label>

            {mode === "register" && (
              <label className="block">
                <span className={`mb-1 block text-sm font-medium ${isDarkMode ? "text-gray-200" : "text-gray-700"}`}>Confirm Password</span>
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  minLength={6}
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  className={`w-full rounded-md border px-3 py-2 focus:border-blue-500 focus:outline-none ${
                    isDarkMode ? "border-gray-600 bg-gray-700 text-white" : "border-gray-300 bg-white text-gray-900"
                  }`}
                />
              </label>
            )}

            <button
              type="submit"
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
            >
              {mode === "register" ? "Create Account and Continue" : "Sign in to Admission Form"}
            </button>
          </form>

          <div className="mt-4 flex justify-between text-sm">
            <Link to="/" className="text-blue-600 hover:underline">Back to Home</Link>
            <Link to="/admin-login" className="text-gray-500 hover:underline">Staff Login</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudentLoginPage;
