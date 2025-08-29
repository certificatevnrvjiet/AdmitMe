import React, { useState, useContext, useEffect, useRef } from "react";
import { IoSearchSharp, IoArrowUp, IoArrowDown, IoDownload, IoPeople } from "react-icons/io5";
import { RiArrowDropDownLine } from "react-icons/ri";
import { useTheme } from '../context/ThemeContext';
import { useNavigate, Link } from 'react-router-dom';
import StudentDetailsModal from '../components/StudentDetailsModal';
import { AuthContext } from "../auth/AuthContext";
import API from '../api'
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { FaGoogleDrive } from 'react-icons/fa';
import { createWebSocket } from '../websocket';

const Dashboard = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isDarkMode } = useTheme();
  const [user, setUser] = useState({"message":"Loading..." }); 
  const { isAuthenticated, role: userRole } = useContext(AuthContext);
  const navigate = useNavigate();
  const [department, setdepartment] = useState("");
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncLoading, setSyncLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const total_students_processed = students.length;
  const wsRef = useRef(null);
  const not_viewed_students = students.filter(s => s.status === 'Not Viewed').length;
  const verified_students = students.filter(s => s.status === 'Verified').length;
  const pending_students = students.filter(s => s.status === 'Pending').length;
  const [branchFilter, setBranchFilter] = useState('all');
  const [GenderFilter, setGenderFilter] = useState('all');
  const [TenthboardFilter, setTenthBoardFilter] = useState('all');
  const [TwelfthboardFilter, setTwelfthBoardFilter] = useState('all');
  const [SavingtoDrive, setSavingtoDrive] = useState(false);
  const [StudenttypeFilter, setStudentTypeFilter] = useState('regular'); // Default to Regular

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
  

  useEffect(() => {
    if (!isAuthenticated) {
      return <Navigate to="/" replace />;
    }
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
      const matchesStudentType = StudenttypeFilter=== 'all' ? true : s.student_type?.toLowerCase() === StudenttypeFilter;
      // Add LE/Regular filter here if you want to filter students based on LE state
      // Example: const matchesLe = Le ? s.is_le : !s.is_le;
      return matchesSearch && matchesDepartment && matchesStatus && matchesBranch && matchesGender && matchesTenthBoard && matchesTwelfthBoard && matchesStudentType;
    })
  );

  const getDepartmentName = (dept) => {
    const deptNames = {
      admin: 'Administrator',
      cse: 'Computer Science',
      ece: 'Electronics and Communication',
      eee: 'Electrical and Electronics',
      mech: 'Mechanical',
      civil: 'Civil',
    };
    return deptNames[dept] || dept.toUpperCase();
  };

  const handleDepartmentChange = (e) => {
    const selectedDept = e.target.value;
    if (selectedDept !== department) {
      navigate(`/dashboard/${selectedDept}`);
    }
  };

  const handleStatusFilterChange = (e) => {
    setStatusFilter(e.target.value);
  };
  const handleGenderFilterChange = (e) => {
    setGenderFilter(e.target.value);
  };
  const handleBranchFilterChange = (e) => {
    setBranchFilter(e.target.value);
  };
  const handleTenthBoardFilterChange = (e) => {
    setTenthBoardFilter(e.target.value);
  };
  const handleTwelfthBoardFilterChange = (e) => {
    setTwelfthBoardFilter(e.target.value);
  };
  const handleStudentTypeFilterChange = (e) => {
    setStudentTypeFilter(e.target.value);
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
      } catch (driveError) {
      }
  
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
  
      const response = await API.get(`/export-students/${department}`, {
        params,
        responseType: 'blob', // Important for binary file downloads
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
  
      // Create a link and trigger download
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
  

  // Helper function to format date as DD/MM/YYYY
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

  return (
    <div className={`min-h-full ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
      {selectedStudent && (
        <StudentDetailsModal
          student={selectedStudent}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          onSave={handleSaveStudent}
          isLE={StudenttypeFilter === "le"} // Pass LE info to modal
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
            {/* Quick Actions */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-indigo-400">Quick Actions</h3>
                </div>
                <div className="space-y-4">
                  {userRole !== 'admin' &&
                    <button
                      className={`w-full px-4 py-2 rounded-md ${isDarkMode ? 'bg-indigo-600 text-white' : 'bg-indigo-500 text-white'} ${syncLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                      onClick={handleSyncStudents}
                      disabled={syncLoading}
                    >
                      {syncLoading ? 'Syncing...' : 'Extract and Fill 71 fields'}
                    </button>
                  }     
                  {syncStatus && (
                    <div className="text-sm mt-2 text-indigo-400">{syncStatus}</div>
                  )}
                  <button 
                    className={`w-full px-4 py-2 rounded-md flex items-center justify-center space-x-2 ${isDarkMode ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-green-500 text-white hover:bg-green-600'} ${downloadLoading ? 'opacity-50 cursor-not-allowed' : ''}`} 
                    onClick={handleDownloadExcel}
                    disabled={downloadLoading}
                  >
                    <IoDownload className="w-4 h-4" />
                    <span>{downloadLoading ? 'Downloading...' : 'Download Excel'}</span>
                  </button>
                  <button 
                    className={`w-full px-4 py-2 rounded-md flex items-center justify-center space-x-2 ${isDarkMode ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-green-500 text-white hover:bg-green-600'} ${downloadLoading ? 'opacity-50 cursor-not-allowed' : ''}`} 
                    onClick={handleSavetoDrive}
                    disabled={SavingtoDrive}
                  >
                    <FaGoogleDrive className="text-white-600 text-xl" />
                    <span>{SavingtoDrive ? 'Saving...' : 'Save To Drive'}</span>
                  </button>
                  {userRole === 'admin' && (
                    <Link
                      to="/user-management"
                      className={`w-full px-4 py-2 rounded-md flex items-center justify-center space-x-2 ${isDarkMode ? 'bg-purple-600 text-white hover:bg-purple-700' : 'bg-purple-500 text-white hover:bg-purple-600'}`}
                    >
                      <IoPeople className="w-4 h-4" />
                      <span>User Management</span>
                    </Link>
                  )}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
              <div className="p-6">
                <h3 className="text-lg font-medium text-indigo-400 mb-4">Verification Statistics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Not viewed</span><span className="text-indigo-400 font-semibold">{not_viewed_students}</span></div>
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Pending Students</span><span className="text-yellow-400 font-semibold">{pending_students}</span></div>
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Verified Students</span><span className="text-green-400 font-semibold">{verified_students}</span></div>
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Total Students</span><span className="text-indigo-400 font-semibold">{total_students_processed}</span></div>
                </div>
              </div>
            </div>
          </div>

<div className={`mt-8 shadow-sm rounded-lg mb-10 ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
  <div className="p-6">
    <div className="mb-4">
      <h3 className="text-lg font-medium text-indigo-400 mb-4">
        Student Verification Activity
      </h3>

      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        {/* Filter Controls Group */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-4 w-full">
          {/* StudentType Filter */}
          <div className="relative w-full md:w-auto">
            <select
              onChange={handleStudentTypeFilterChange}
              value={StudenttypeFilter}
              className={`appearance-none w-full md:w-auto bg-transparent border ${
                isDarkMode
                  ? 'border-gray-600 text-white bg-gray-700'
                  : 'border-gray-300 text-gray-700 bg-white'
              } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
              <option value="regular">Regular</option>
              <option value="le">LE</option>
            </select>
            <RiArrowDropDownLine
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                isDarkMode ? 'text-white' : 'text-gray-700'
              }`}
              size={20}
            />
          </div>  
          {/* Status Filter */}
          <div className="relative w-full md:w-auto">
            <select
              onChange={handleStatusFilterChange}
              value={statusFilter}
              className={`appearance-none w-full md:w-auto bg-transparent border ${
                isDarkMode
                  ? 'border-gray-600 text-white bg-gray-700'
                  : 'border-gray-300 text-gray-700 bg-white'
              } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
              <option value="all">All Status</option>
              <option value="verified">Verified</option>
              <option value="pending">Pending</option>
              <option value="not viewed">Not Viewed</option>
            </select>
            <RiArrowDropDownLine
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                isDarkMode ? 'text-white' : 'text-gray-700'
              }`}
              size={20}
            />
          </div>

          {/* TenthBoard Filter */}
          <div className="relative w-full md:w-auto">
            <select
              onChange={handleTenthBoardFilterChange}
              value={TenthboardFilter}
              className={`appearance-none w-full md:w-auto bg-transparent border ${
                isDarkMode
                  ? 'border-gray-600 text-white bg-gray-700'
                  : 'border-gray-300 text-gray-700 bg-white'
              } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
              <option value="all">All Tenth Boards</option>
              <option value="tg bse">TG BSE</option>
              <option value="cbse">CBSE</option>
              <option value="icse">ICSE</option>
              <option value="ap bse">AP BSE</option>
              <option value="idbp">IDBP</option>
              <option value="ace and a level">ACE and A Level</option>
              <option value="other">Other</option>
            </select>
            <RiArrowDropDownLine
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                isDarkMode ? 'text-white' : 'text-gray-700'
              }`}
              size={20}
            />
          </div>
          {/* TwelfthBoardFilter */}
              <div className="relative w-full md:w-auto">
            <select
              onChange={handleTwelfthBoardFilterChange}
              value={TwelfthboardFilter}
              className={`appearance-none w-full md:w-auto bg-transparent border ${
                isDarkMode
                  ? 'border-gray-600 text-white bg-gray-700'
                  : 'border-gray-300 text-gray-700 bg-white'
              } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
              <option value="all">All Twelfth Boards</option>
              <option value="tg bie">TG BIE</option>
              <option value="cbse">CBSE</option>
              <option value="icse">ICSE</option>
              <option value="ap bie">AP BIE</option>
              <option value="ibdp">IDBP</option>
              <option value="ace and a level">ACE and A Level</option>
              <option value="other">Other</option>
            </select>
            <RiArrowDropDownLine
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                isDarkMode ? 'text-white' : 'text-gray-700'
              }`}
              size={20}
            />
          </div>

          {/* Branch Filter */}
          {department === 'admin' && (
            <div className="relative w-full md:w-auto">
              <select
                onChange={handleBranchFilterChange}
                value={branchFilter}
                className={`appearance-none w-full md:w-auto bg-transparent border ${
                  isDarkMode
                    ? 'border-gray-600 text-white bg-gray-700'
                    : 'border-gray-300 text-gray-700 bg-white'
                } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
              >
                <option value="all">All Branches</option>
                <option value="aids">AIDS</option>
                <option value="ae">AE</option>
                <option value="ce">CE</option>
                <option value="csbs">CSBS</option>
                <option value="cse">CSE</option>
                <option value="aml">AML</option>
                <option value="cseds">CSE-DS</option>
                <option value="csecys">CSE-CYS</option>
                <option value="cseiot">CSE-IOT</option>
                <option value="eee">EEE</option>
                <option value="ece">ECE</option>
                <option value="eie">EIE</option>
                <option value="it">IT</option>
                <option value="me">ME</option>
                <option value="vlsi">VLSI</option>
                <option value="biotechnology">Biotechnology</option>
                <option value="rai">Robotics and AI</option>
              </select>
              <RiArrowDropDownLine
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                  isDarkMode ? 'text-white' : 'text-gray-700'
                }`}
                size={20}
              />
            </div>
          )}
          {/* Region Filter
          <div className="relative w-full md:w-auto">
            <select
              onChange={handleRegionFilterChange}
              value={regionFilter}
              className={`appearance-none w-full md:w-auto bg-transparent border ${
                isDarkMode
                  ? 'border-gray-600 text-white bg-gray-700'
                  : 'border-gray-300 text-gray-700 bg-white'
              } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
              <option value="all">All Regions</option>
              <option value="within_state">Within State</option>
              <option value="outside_state">Other State</option>
            </select>
            <RiArrowDropDownLine
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                isDarkMode ? 'text-white' : 'text-gray-700'
              }`}
              size={20}
            />
          </div> */}
          {/* Gender Filter */}
          <div className="relative w-full md:w-auto">
            <select
              onChange={handleGenderFilterChange}
              value={GenderFilter}
              className={`appearance-none w-full md:w-auto bg-transparent border ${
                isDarkMode
                  ? 'border-gray-600 text-white bg-gray-700'
                  : 'border-gray-300 text-gray-700 bg-white'
              } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
              <option value="all">All Gender</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
            <RiArrowDropDownLine
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                isDarkMode ? 'text-white' : 'text-gray-700'
              }`}
              size={20}
            />
          </div>
          {/* Search Box */}
          <div className="relative w-full md:w-64">
            <input
              type="text"
              placeholder="Search by Name"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className={`w-full pl-6 pr-10 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 ${
                isDarkMode
                  ? 'bg-gray-600 border-gray-500 text-white placeholder-gray-400'
                  : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
              }`}
            />
            <IoSearchSharp className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          </div>
        </div>
      </div>
    </div>
              <div className="overflow-x-auto">
                <table className={`min-w-full divide-y ${isDarkMode ? 'divide-gray-600' : 'divide-gray-200'}`}>
                  <thead>
                    <tr>
                    <th
                        className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDarkMode ? 'text-gray-300' : 'text-gray-500'
                        } cursor-pointer hover:text-indigo-500`}
                        onClick={() => handleSort('student_id')}
                      >Student ID {getSortIcon('student_id')}</th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        isDarkMode ? 'text-gray-300' : 'text-gray-500'
                      } cursor-pointer hover:text-indigo-500`}
                        onClick={() => handleSort('student_name')}>Student Name{getSortIcon('student_name')}</th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Date Of Birth</th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Status</th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Branch</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${isDarkMode ? 'divide-gray-600' : 'divide-gray-200'}`}>
                    {filteredStudents.map((s) => (
                      <tr
                        key={s.aadhaar_card_number}
                        className={`${isDarkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-50'} cursor-pointer`}
                        onClick={() => handleStudentClick(s)}
                      >
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{s.ht_no}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{s.student_name}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{formatDateDMY(s.date_of_birth)}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            s.status === "Verified" ? (isDarkMode ? "bg-green-900 text-green-300" : "bg-green-100 text-green-800") :
                            s.status === "Pending" ? (isDarkMode ? "bg-yellow-900 text-yellow-300" : "bg-yellow-100 text-yellow-800") :
                            (isDarkMode ? "bg-red-900 text-red-300" : "bg-red-100 text-red-800")
                          }`}>{s.status}</span>
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>{s.branch_code}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </main>
      <ToastContainer />
    </div>
  );
};

export default Dashboard;
