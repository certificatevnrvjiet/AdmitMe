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
  const [StudenttypeFilter, setStudentTypeFilter] = useState('regular'); // Default to Regular
  const [admissionCategoryFilter, setAdmissionCategoryFilter] = useState('all');

  // Context & Hooks
  const { isDarkMode } = useTheme();
  const { isAuthenticated, role: userRole } = useContext(AuthContext);
  const navigate = useNavigate();
  const wsRef = useRef(null);

  // Derived State
  const total_students_processed = students.length;
  const not_viewed_students = students.filter(s => s.status === 'Not Viewed').length;
  const verified_students = students.filter(s => s.status === 'Verified').length;
  const pending_students = students.filter(s => s.status === 'Pending').length;

  // Effects
  useEffect(() => {
    if (!isAuthenticated) return;

    API.get('/me')
      .then(res => {
        setUser(res.data);
        setdepartment(res.data.role);
      })
      .catch(() => setUser(null));
  }, [isAuthenticated]);

  useEffect(() => {
    if (department) {
      fetchStudents();
    }
  }, [department]);

  // WebSocket Effect
  useEffect(() => {
    const ws = createWebSocket("/ws/notifications");
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
      }
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      ws.close();
    };
  }, []);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const res = await API.get(`/students/${department}`);
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
    if (/^\d{2}[\/\-]\d{2}[\/\-]\d{4}$/.test(dateString)) {
      return dateString.replace(/\-/g, '/');
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
      const matchesDepartment = department === 'admin' ? true : s.branch_code?.toLowerCase() === department;
      const matchesStatus = statusFilter === 'all' ? true : s.status?.toLowerCase() === statusFilter;
      const matchesBranch = branchFilter === 'all' ? true : s.branch_code?.toLowerCase() === branchFilter;
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
      const response = await API.put(
        `/student/${updatedStudent.aadhaar_card_number}`,
        updatedStudent
      );

      setStudents(students.map(student =>
        student.aadhaar_card_number === updatedStudent.aadhaar_card_number
          ? { ...student, ...updatedStudent }
          : student
      ));

      try {
        await handleSavetoDrive();
      } catch (driveError) { }

      handleCloseModal();
    } catch (error) {
      alert(
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
      alert(
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
      alert(
        error.response?.data?.detail ||
        error.message ||
        'Failed to Save To Drive. Please try again.'
      );
    } finally {
      setSavingtoDrive(false);
    }
  };

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className={`min-h-full ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
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
            />

            <StatsCards
              students={students}
              isDarkMode={isDarkMode}
              userRole={userRole}
              not_viewed_students={not_viewed_students}
              verified_students={verified_students}
              pending_students={pending_students}
              total_students_processed={total_students_processed}
            />
          </div>

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
          />
        </div>
      </main>
      <ToastContainer />
    </div>
  );
};

export default Dashboard;
