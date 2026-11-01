import React, { useState, useContext, useEffect, useRef } from "react";
import { IoArrowUp, IoArrowDown } from "react-icons/io5";
import { useTheme } from '../context/ThemeContext';
import { useNavigate, Navigate } from 'react-router-dom';
import StudentDetailsModal from '../components/StudentDetailsModal';
import { AuthContext } from "../auth/AuthContext";
import API from '../api'
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { createWebSocket } from '../websocket';

// Import sub-components
import StatsCards from "../components/dashboard/StatsCards";
import QuickActions from "../components/dashboard/QuickActions";
import FilterBar from "../components/dashboard/FilterBar";
import StudentTable from "../components/dashboard/StudentTable";

const Dashboard = () => {
  const savedExtractAllTask = () => {
    try {
      const raw = localStorage.getItem('extractAllTask');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  };

  // State Declarations
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState({ "message": "Loading..." });
  const [department, setdepartment] = useState("");
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [branchFilter, setBranchFilter] = useState('all');
  const [GenderFilter, setGenderFilter] = useState('all');
  const [TenthboardFilter, setTenthBoardFilter] = useState('all');
  const [TwelfthboardFilter, setTwelfthBoardFilter] = useState('all');
  const [SavingtoDrive, setSavingtoDrive] = useState(false);
  const [extractAllLoading, setExtractAllLoading] = useState(false);
  const [extractAllTask, setExtractAllTask] = useState(savedExtractAllTask);
  const [StudenttypeFilter, setStudentTypeFilter] = useState('regular'); // Default to Regular
  const [admissionCategoryFilter, setAdmissionCategoryFilter] = useState('all');
  const [branchAliases, setBranchAliases] = useState({});

  // Context & Hooks
  const { isDarkMode } = useTheme();
  const { isAuthenticated, role: userRole, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  const wsRef = useRef(null);

  // Derived State
  const total_students_processed = students.length;
  const submitted_students = students.filter(s => (s.status || '').toLowerCase() === 'submitted').length;
  const approved_students = students.filter(s => (s.status || '').toLowerCase() === 'approved').length;
  const under_review_students = students.filter(s => (s.status || '').toLowerCase() === 'under_review').length;

  // Effects
  useEffect(() => {
    if (!isAuthenticated) return;

    API.get('/me')
      .then(res => {
        setUser(res.data);
        setdepartment(res.data.role);
      })
      .catch((err) => {
        setUser(null);
        if (err?.response?.status === 401) {
          logout();
          navigate('/');
        }
      });
  }, [isAuthenticated, logout, navigate]);

  useEffect(() => {
    API.get('/meta/programs-branches')
      .then(({ data }) => setBranchAliases(data?.aliases || {}))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (department) {
      fetchStudents();
    }
  }, [department]);

  // WebSocket Effect
  useEffect(() => {
    const ws = createWebSocket();
    if (!ws) return;

    wsRef.current = ws;

    ws.onmessage = async (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "sync_complete") {
        toast.success(data.message || "Sync completed!");
        setSyncStatus(data.message);
        await fetchStudents();
      } else if (data.type === "sync_failed") {
        toast.error(data.message || "Sync failed!");
        setSyncStatus(data.message);
        await fetchStudents();
      } else if (data.type?.startsWith("extract_all_")) {
        setExtractAllTask((current) => {
          const merged = {
            ...(current || {}),
            id: data.task_id || current?.id,
            task_id: data.task_id || current?.task_id,
            batch_job_id: data.batch_job_id || current?.batch_job_id,
            batch_state: data.batch_state || current?.batch_state,
            progress: data.progress ?? current?.progress ?? 0,
            total_students: data.total_students ?? current?.total_students,
            total_documents: data.total_documents ?? current?.total_documents,
            completed_documents: data.completed_documents ?? current?.completed_documents,
            failed_documents: data.failed_documents ?? current?.failed_documents,
            message: data.message || current?.message,
            status: data.type === "extract_all_complete" ? "completed" : data.type === "extract_all_failed" ? "failed" : current?.status || "processing",
          };
          if (merged.status === "completed" || merged.status === "failed") {
            localStorage.removeItem('extractAllTask');
          } else {
            localStorage.setItem('extractAllTask', JSON.stringify(merged));
          }
          return merged;
        });

        if (data.type === "extract_all_complete") {
          toast.success(data.message || "Bulk extraction completed!");
          await fetchStudents();
        } else if (data.type === "extract_all_failed") {
          toast.error(data.message || "Bulk extraction failed!");
          await fetchStudents();
        }
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      ws.close();
    };
  }, []);

  const normalizeTaskResponse = (payload) => {
    if (Array.isArray(payload)) return payload[0] || null;
    return payload && !payload.error ? payload : null;
  };

  const refreshExtractAllTask = async (taskId) => {
    if (!taskId) return;
    const { data } = await API.get(`/task-status/${taskId}`);
    const row = normalizeTaskResponse(data);
    if (!row) return;

    setExtractAllTask(row);
    if (row.status === "completed" || row.status === "failed") {
      localStorage.removeItem('extractAllTask');
      await fetchStudents();
    } else {
      localStorage.setItem('extractAllTask', JSON.stringify(row));
    }
  };

  useEffect(() => {
    const taskId = extractAllTask?.id || extractAllTask?.task_id;
    if (!taskId || ["completed", "failed"].includes((extractAllTask?.status || "").toLowerCase())) {
      return undefined;
    }

    refreshExtractAllTask(taskId).catch(() => {});
    const timer = window.setInterval(() => {
      refreshExtractAllTask(taskId).catch(() => {});
    }, 12000);
    return () => window.clearInterval(timer);
  }, [extractAllTask?.id, extractAllTask?.task_id, extractAllTask?.status]);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      let res;
      try {
        res = await API.get('/students');
      } catch {
        res = await API.get(`/students/${department}`);
      }
      setStudents(res.data.students || []);
    } catch (err) {
      setError(err.response?.data?.message || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Helper Functions
  // Format date as DD/MM/YYYY
  function formatDateDMY(dateString) {
    if (!dateString) return '';
    if (/^\d{2}[/-]\d{2}[/-]\d{4}$/.test(dateString)) {
      return dateString.replace(/-/g, '/');
    }
    const date = new Date(dateString);
    if (isNaN(date)) return dateString;
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  }

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) return null;
    return sortConfig.direction === 'asc' ? <IoArrowUp className="ml-1 inline-block" /> : <IoArrowDown className="ml-1 inline-block" />;
  };

  // Data Processing (Sorting & Filtering)
  const studentList = students.map((s) => s.data || s);
  const normalizeBranch = (value) => {
    const compact = String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '').replace(/^ug/, '');
    return branchAliases[compact] || compact;
  };
  const sortData = (data) => {
    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key]?.toLowerCase?.() || '';
      const bVal = b[sortConfig.key]?.toLowerCase?.() || '';
      return sortConfig.direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
  };

  const filteredStudents = sortData(
    studentList.filter((s) => {
      const matchesSearch = s.student_name?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesDepartment = department === 'admin' ? true : normalizeBranch(s.branch) === normalizeBranch(department);
      const matchesStatus = statusFilter === 'all' ? true : s.status?.toLowerCase() === statusFilter;
      const matchesBranch = branchFilter === 'all' ? true : normalizeBranch(s.branch) === normalizeBranch(branchFilter);
      const matchesGender = GenderFilter === 'all' ? true : s.gender?.toLowerCase() === GenderFilter;
      const matchesTenthBoard = TenthboardFilter === 'all' ? true : s.tenth_board_name?.toLowerCase() === TenthboardFilter;
      const matchesTwelfthBoard = TwelfthboardFilter === 'all' ? true : s.twelfth_board_name?.toLowerCase() === TwelfthboardFilter;
      const matchesStudentType = StudenttypeFilter === 'all' ? true : s.student_type?.toLowerCase() === StudenttypeFilter;
      const matchesAdmissionCategory = admissionCategoryFilter === 'all' ? true : s.admission_category?.toLowerCase() === admissionCategoryFilter.toLowerCase();
      return matchesSearch && matchesDepartment && matchesStatus && matchesBranch && matchesGender && matchesTenthBoard && matchesTwelfthBoard && matchesStudentType && matchesAdmissionCategory;
    })
  );

  // Handlers
  const handleStudentClick = (student) => {
    setSelectedStudent(student);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedStudent(null);
  };

  const handleSaveStudent = async (updatedStudent) => {
    try {
      await API.put(
        `/student/${updatedStudent.aadhaar_card_number}`,
        updatedStudent
      );

      setStudents(students.map(student =>
        student.aadhaar_card_number === updatedStudent.aadhaar_card_number
          ? { ...student, ...updatedStudent }
          : student
      ));

      await handleSavetoDrive();

      handleCloseModal();
    } catch (error) {
      toast.error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to update student details. Please try again.'
      );
    }
  };

  const handleSyncStudents = async () => {
    setSyncStatus(null);
    setSyncLoading(true);

    try {
      const branch = department;
      if (!branch || branch === 'admin') {
        setSyncStatus('Please select a department to sync.');
        setSyncLoading(false);
        return;
      }
      const { data } = await API.post(`/sync/${branch}`);
      setSyncStatus(`Sync started! Task ID: ${data.task_id}`);
    } catch (err) {
      setSyncStatus(
        `Error: ${err.response?.data?.detail || err.message || 'Sync failed'}`
      );
    } finally {
      setSyncLoading(false);
    }
  };

  const handleDownloadExcel = async () => {
    setDownloadLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search_term', searchTerm);
      if (statusFilter !== 'all') params.append('status_filter', statusFilter);
      if (admissionCategoryFilter !== 'all') params.append('admission_category_filter', admissionCategoryFilter);

      const response = await API.get(`/export-students/${department}`, {
        params,
        responseType: 'blob',
      });

      const contentDisposition = response.headers['content-disposition'];
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      let filename = `${department.toUpperCase()}_students_${timestamp}.xlsx`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }

      toast.success(`File: ${filename} Downloaded Successfully!`);

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      toast.error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to download Excel file. Please try again.'
      );
    } finally {
      setDownloadLoading(false);
    }
  };

  const handleSavetoDrive = async () => {
    setSavingtoDrive(true);
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search_term', searchTerm);
      if (statusFilter !== 'all') params.append('status_filter', statusFilter);
      if (admissionCategoryFilter !== 'all') params.append('admission_category_filter', admissionCategoryFilter);

      await API.post(`/save-to-drive/${department}`, null, { params });
    } catch (error) {
      toast.error(
        error.response?.data?.detail ||
        error.message ||
        'Failed to Save To Drive. Please try again.'
      );
    } finally {
      setSavingtoDrive(false);
    }
  };

  const handleExtractAllPending = async () => {
    setExtractAllLoading(true);
    try {
      const { data } = await API.post('/extract-all');
      toast.success(data.message || 'Bulk extraction started!');
      const task = {
        id: data.task_id,
        task_id: data.task_id,
        batch_job_id: data.batch_job_id,
        status: data.batch_job_id ? 'submitted' : 'completed',
        progress: data.batch_job_id ? 20 : 100,
        total_students: data.total_students,
        total_documents: data.total_documents,
        completed_documents: 0,
        failed_documents: 0,
        batch_state: data.batch_job_id ? 'JOB_STATE_PENDING' : 'completed',
        message: data.message,
      };
      setExtractAllTask(task);
      if (task.status === 'completed') {
        localStorage.removeItem('extractAllTask');
      } else {
        localStorage.setItem('extractAllTask', JSON.stringify(task));
      }
      setSyncStatus(`Extraction submitted! Task ID: ${data.task_id}`);
      refreshExtractAllTask(data.task_id).catch(() => {});
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message || 'Bulk extraction failed');
    } finally {
      setExtractAllLoading(false);
    }
  };

  const handleExtractStudent = async (studentId) => {
    try {
      toast.info('Queuing extraction for student...');
      const { data } = await API.post(`/students/${studentId}/engine-runs`, {
        force: true,
        doc_types: []
      });
      toast.success(`Extraction queued! Task ID: ${data.task_id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message || 'Extraction failed to queue');
    }
  };

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (userRole === 'student') {
    return <Navigate to="/student-portal" replace />;
  }

  if (loading) {
    return <div className={`min-h-[calc(100vh-65px)] p-6 ${isDarkMode ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-800'}`}>Loading students...</div>;
  }

  if (error) {
    return <div className={`min-h-[calc(100vh-65px)] p-6 ${isDarkMode ? 'bg-gray-800 text-red-300' : 'bg-gray-100 text-red-700'}`}>Error: {error}</div>;
  }

  const extractProgress = Math.max(0, Math.min(100, Number(extractAllTask?.progress || 0)));
  const extractStatus = (extractAllTask?.status || '').toLowerCase();
  const showExtractProgress = userRole === 'admin' && extractAllTask;

  return (
    <div className={`min-h-[calc(100vh-65px)] ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
      {selectedStudent && (
        <StudentDetailsModal
          student={selectedStudent}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          onSave={handleSaveStudent}
          isLE={StudenttypeFilter === "le"}
        />
      )}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className={`text-2xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
              {department.toLowerCase() === "admin" ? "Admin Dashboard" : `${department.toUpperCase()} Department Dashboard`}
            </h2>
            {user?.User && (
              <span className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>{user.User}</span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <QuickActions
              userRole={userRole}
              syncLoading={syncLoading}
              handleSyncStudents={handleSyncStudents}
              syncStatus={syncStatus}
              downloadLoading={downloadLoading}
              handleDownloadExcel={handleDownloadExcel}
              SavingtoDrive={SavingtoDrive}
              handleSavetoDrive={handleSavetoDrive}
              isDarkMode={isDarkMode}
              handleExtractAllPending={handleExtractAllPending}
              extractAllLoading={extractAllLoading}
            />

            <StatsCards
              students={students}
              isDarkMode={isDarkMode}
              userRole={userRole}
              submitted_students={submitted_students}
              approved_students={approved_students}
              under_review_students={under_review_students}
              total_students_processed={total_students_processed}
            />
          </div>

          {showExtractProgress && (
            <div className={`mt-6 overflow-hidden rounded-lg shadow-sm border ${isDarkMode ? 'bg-gray-700 border-gray-600 text-gray-100' : 'bg-white border-gray-200 text-gray-800'}`}>
              <div className="p-5">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-medium">Extract All Progress</h3>
                    <p className={`text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>
                      {extractAllTask.message || `State: ${extractAllTask.batch_state || extractAllTask.status || 'queued'}`}
                    </p>
                  </div>
                  <span className={`self-start sm:self-auto px-3 py-1 rounded-full text-xs font-semibold ${
                    extractStatus === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : extractStatus === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-indigo-100 text-indigo-800'
                  }`}>
                    {extractAllTask.batch_state || extractAllTask.status || 'queued'}
                  </span>
                </div>

                <div className={`mt-4 h-3 rounded-full overflow-hidden ${isDarkMode ? 'bg-gray-600' : 'bg-gray-200'}`}>
                  <div className="h-full bg-indigo-500 transition-all duration-500" style={{ width: `${extractProgress}%` }} />
                </div>

                <div className={`mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                  <div>
                    <div className="font-semibold">{extractProgress}%</div>
                    <div className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>Progress</div>
                  </div>
                  <div>
                    <div className="font-semibold">{extractAllTask.total_documents ?? 0}</div>
                    <div className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>Submitted docs</div>
                  </div>
                  <div>
                    <div className="font-semibold">{extractAllTask.completed_documents ?? 0} / {extractAllTask.total_documents ?? 0}</div>
                    <div className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>Processed</div>
                  </div>
                  <div>
                    <div className="font-semibold">{extractAllTask.failed_documents ?? 0}</div>
                    <div className={isDarkMode ? 'text-gray-400' : 'text-gray-500'}>Failed</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <FilterBar
            searchTerm={searchTerm} setSearchTerm={setSearchTerm}
            statusFilter={statusFilter} setStatusFilter={setStatusFilter}
            admissionCategoryFilter={admissionCategoryFilter} setAdmissionCategoryFilter={setAdmissionCategoryFilter}
            StudenttypeFilter={StudenttypeFilter} setStudentTypeFilter={setStudentTypeFilter}
            TenthboardFilter={TenthboardFilter} setTenthBoardFilter={setTenthBoardFilter}
            TwelfthboardFilter={TwelfthboardFilter} setTwelfthBoardFilter={setTwelfthBoardFilter}
            branchFilter={branchFilter} setBranchFilter={setBranchFilter}
            GenderFilter={GenderFilter} setGenderFilter={setGenderFilter}
            department={department}
            isDarkMode={isDarkMode}
          />

          <StudentTable
            filteredStudents={filteredStudents}
            isDarkMode={isDarkMode}
            handleSort={handleSort}
            getSortIcon={getSortIcon}
            handleStudentClick={handleStudentClick}
            formatDateDMY={formatDateDMY}
            handleExtractStudent={handleExtractStudent}
          />
        </div>
      </main>
      <ToastContainer />
    </div>
  );
};

export default Dashboard;
