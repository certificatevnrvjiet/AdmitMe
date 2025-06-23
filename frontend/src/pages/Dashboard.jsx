import React, { useState, useContext, useEffect } from "react";
import { IoSearchSharp, IoArrowUp, IoArrowDown } from "react-icons/io5";
import { RiArrowDropDownLine } from "react-icons/ri";
import { useTheme } from '../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import StudentDetailsModal from '../components/StudentDetailsModal';
import { AuthContext } from "../auth/AuthContext";
import API from '../api'





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
  const total_students_processed = students.length; // Assuming this is the total count of students fetched

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/students/${department}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      // console.log('Response:', response); // Debugging line
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      // console.log('Data:', data); // Debugging line
      setStudents(data.students || []);
      console.log('Fetched students:', data.students);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching students:', err);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    if (!isAuthenticated) {
      console.log("User is not authenticated, redirecting to login...");
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

  // Flatten data: students = [{ data: {...} }, ...] → studentList = [{...}, {...}]
  const studentList = students.map((s) => s.data || s);
  console.log('Student List:', studentList); // Debugging line
  // Sort logic (based on name)
  const sortData = (data) => {
    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key]?.toLowerCase?.() || '';
      const bVal = b[sortConfig.key]?.toLowerCase?.() || '';
      return sortConfig.direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
  };
  console.log('Student List 22:', studentList);
  // Filter students by department, search term, and status
  const filteredStudents = sortData(
    studentList.filter((s) => {
      const matchesSearch = s.student_name?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesDepartment = department === 'admin' ? true : s.branch_code?.toLowerCase() === department;
      const matchesStatus = statusFilter === 'all' ? true : s.status?.toLowerCase() === statusFilter;
      return matchesSearch && matchesDepartment && matchesStatus;
    })
  );

  console.log('Student List 33:', filteredStudents);


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
            
        const response = await fetch(`http://localhost:8000/student/${updatedStudent.aadhaar_card_number}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedStudent),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update student');
        }

        const result = await response.json();
        
        // Update local state
        setStudents(students.map(student => 
            student.aadhaar_card_number === updatedStudent.aadhaar_card_number ? { ...student, ...updatedStudent  } : student
        ));
        
        console.log('Student updated successfully:', result);
        handleCloseModal();
    } catch (error) {
        console.error('Error updating student:', error);
        alert(error.message || 'Failed to update student details. Please try again.');
    }
  };

  // Handler for syncing students
  const handleSyncStudents = async () => {
    setSyncStatus(null);
    setSyncLoading(true);
    try {
      // Get token from localStorage or AuthContext
      const token = localStorage.getItem('token');
      if (!token) {
        setSyncStatus('Not authenticated. Please login.');
        setSyncLoading(false);
        return;
      }
      // Use department as branch (skip if admin)
      const branch = department;
      if (!branch || branch === 'admin') {
        setSyncStatus('Please select a department to sync.');
        setSyncLoading(false);
        return;
      }
      const response = await fetch(`http://localhost:8000/sync/${branch}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Sync failed');
      }
      const data = await response.json();
      setSyncStatus(`Sync started! Task ID: ${data.task_id}`);
    } catch (err) {
      setSyncStatus(`Error: ${err.message}`);
    } finally {
      setSyncLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`min-h-full ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <p className={`text-center ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`min-h-full ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <p className={`text-center text-red-500`}>Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-full ${isDarkMode ? 'bg-gray-800' : 'bg-gray-100'}`}>
      {selectedStudent && (
        <StudentDetailsModal
          student={selectedStudent}
          isOpen={isModalOpen}
          onClose={handleCloseModal}
          onSave={handleSaveStudent}
        />
      )}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center mb-6">
            <h2 className={`text-2xl font-semibold ${isDarkMode ? 'text-white' : 'text-gray-800'}`}>
              {getDepartmentName(department)} Department Dashboard
            </h2>
            {/* <div className="relative">
              <select
                onChange={handleDepartmentChange}
                className={`appearance-none bg-transparent border ${
                  isDarkMode ? 'border-gray-600 text-white bg-gray-700' : 'border-gray-300 text-gray-700 bg-white'
                } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
                defaultValue={department}
              >
                <option value="admin">All Departments</option>
                <option value="cse">Computer Science</option>
                <option value="ece">Electronics and Communication</option>
                <option value="eee">Electrical and Electronics</option>
                <option value="mech">Mechanical</option>
                <option value="civil">Civil</option>
              </select>
              <RiArrowDropDownLine
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                  isDarkMode ? 'text-white' : 'text-gray-700'
                }`}
                size={20}
              />
            </div> */}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
              <div className="p-6">
                <h3 className="text-lg font-medium text-indigo-400 mb-4">Quick Actions</h3>
                <div className="space-y-4">
                  <button
                    className={`w-full px-4 py-2 rounded-md ${isDarkMode ? 'bg-indigo-600 text-white' : 'bg-indigo-500 text-white'} ${syncLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={handleSyncStudents}
                    disabled={syncLoading}
                  >
                    {syncLoading ? 'Syncing...' : 'Sync Students'}
                  </button>
                  {syncStatus && (
                    <div className="text-sm mt-2 text-indigo-400">{syncStatus}</div>
                  )}
                  <button className={`w-full px-4 py-2 rounded-md ${isDarkMode ? 'bg-gray-600 text-indigo-300' : 'bg-indigo-50 text-indigo-600'}`}>Verify New Student</button>
                  <button className={`w-full px-4 py-2 rounded-md ${isDarkMode ? 'bg-gray-600 text-indigo-300' : 'bg-indigo-50 text-indigo-600'}`}>View Pending Verifications</button>
                  <button className={`w-full px-4 py-2 rounded-md ${isDarkMode ? 'bg-gray-600 text-indigo-300' : 'bg-indigo-50 text-indigo-600'}`}>Generate Reports</button>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
              <div className="p-6">
                <h3 className="text-lg font-medium text-indigo-400 mb-4">Verification Statistics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Pending Verifications</span><span className="text-indigo-400 font-semibold">{total_students_processed}</span></div>
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Verified Today</span><span className="text-green-400 font-semibold">12</span></div>
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Total Processed</span><span className="text-indigo-400 font-semibold">{total_students_processed}</span></div>
                </div>
              </div>
            </div>
          </div>

          {/* Activity Table */}
          <div className={`mt-8 shadow-sm rounded-lg mb-10 ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
            <div className="p-6">
              <div className="flex justify-between mb-4">
                <h3 className="text-lg font-medium text-indigo-400 mb-4">Student Verification Activity</h3>
                <div className="flex space-x-4">
                  <div className="relative">
                    <select
                      onChange={handleStatusFilterChange}
                      className={`appearance-none bg-transparent border ${
                        isDarkMode ? 'border-gray-600 text-white bg-gray-700' : 'border-gray-300 text-gray-700 bg-white'
                      } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
                      value={statusFilter}
                    >
                      <option value="all">All Status</option>
                      <option value="verified">Verified</option>
                      <option value="pending">Pending</option>
                      <option value="not verified">Not Verified</option>
                    </select>
                    <RiArrowDropDownLine className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${
                    isDarkMode ? 'text-white' : 'text-gray-700'}`}
                    size={20}/>
                  </div>
                  <div className="relative">
                    <input
                      type="text"
                      placeholder="Search by Name"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className={`w-64 pl-6 pr-4 py-2 border rounded-md focus:outline-none focus:ring-1 focus:ring-indigo-500 ${
                        isDarkMode ? 'bg-gray-600 border-gray-500 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                      }`}
                    />
                    <IoSearchSharp className="absolute right-2 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
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
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Student Name</th>
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
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{s.student_id}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{s.student_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            s.status === "Verified" ? (isDarkMode ? "bg-green-900 text-green-300" : "bg-green-100 text-green-800") :
                            s.Status === "Pending" ? (isDarkMode ? "bg-yellow-900 text-yellow-300" : "bg-yellow-100 text-yellow-800") :
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
    </div>
  );
};

export default Dashboard;
