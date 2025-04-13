import React from 'react';
import { IoSearchSharp } from "react-icons/io5";
import { IoArrowUp, IoArrowDown } from "react-icons/io5";
import { students } from '../assets/Studentsdata.json';
import { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import StudentDetailsModal from '../components/StudentDetailsModal';

const Dashboard = ({ department }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { isDarkMode } = useTheme();
  const navigate = useNavigate();

  // Sort function
  const sortData = (data) => {
    return [...data].sort((a, b) => {
      if (sortConfig.key === 'date') {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return sortConfig.direction === 'asc' ? dateA - dateB : dateB - dateA;
      }
      return 0;
    });
  };

  // Filter students based on department and status
  const filteredStudents = sortData(students.filter((s) => {
    const matchesSearch = s.student_name.trim().toLowerCase().includes(searchTerm.toLowerCase().trim());
    const matchesDepartment = department === 'admin' ? true : s.department === department;
    const matchesStatus = statusFilter === 'all' ? true : s.status.toLowerCase() === statusFilter;
    
    return matchesSearch && matchesDepartment && matchesStatus;
  }));

  const getDepartmentName = (dept) => {
    const deptNames = {
      'admin': 'Administrator',
      'cse': 'Computer Science',
      'ece': 'Electronics and Communication',
      'eee': 'Electrical and Electronics',
      'mech': 'Mechanical',
      'civil': 'Civil'
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
    if (sortConfig.key !== key) {
      return null;
    }
    return sortConfig.direction === 'asc' ? (
      <IoArrowUp className="ml-1 inline-block" />
    ) : (
      <IoArrowDown className="ml-1 inline-block" />
    );
  };

  const handleStudentClick = (student) => {
    setSelectedStudent(student);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedStudent(null);
  };

  const handleSaveStudent = (updatedStudent) => {
    // Here you would typically make an API call to update the student data
    console.log('Saving updated student:', updatedStudent);
    // For now, we'll just close the modal
    handleCloseModal();
  };

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
            {department === 'admin' && (
              <div className="relative">
                <select
                  onChange={handleDepartmentChange}
                  className={`appearance-none bg-transparent border ${
                    isDarkMode ? 'border-gray-600 text-white bg-gray-700' : 'border-gray-300 text-gray-700 bg-white'
                  } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
                  defaultValue={department}
                >
                  <option value="admin" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>All Departments</option>
                  <option value="cse" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Computer Science</option>
                  <option value="ece" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Electronics and Communication</option>
                  <option value="eee" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Electrical and Electronics</option>
                  <option value="mech" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Mechanical</option>
                  <option value="civil" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Civil</option>
                </select>
                <div className={`pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                    <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                  </svg>
                </div>
              </div>
            )}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Verification Status Section */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
              <div className="p-6">
                <h3 className="text-lg font-medium text-indigo-400 mb-4">Quick Actions</h3>
                <div className="space-y-4">
                  <button className={`w-full px-4 py-2 rounded-md transition-colors duration-200 ${isDarkMode ? 'bg-gray-600 text-indigo-300 hover:bg-gray-500' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'}`}>
                    Verify New Student
                  </button>
                  <button className={`w-full px-4 py-2 rounded-md transition-colors duration-200 ${isDarkMode ? 'bg-gray-600 text-indigo-300 hover:bg-gray-500' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'}`}>
                    View Pending Verifications
                  </button>
                  <button className={`w-full px-4 py-2 rounded-md transition-colors duration-200 ${isDarkMode ? 'bg-gray-600 text-indigo-300 hover:bg-gray-500' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'}`}>
                    Generate Reports
                  </button>
                </div>
              </div>
            </div>

            {/* Statistics Section */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
              <div className="p-6">
                <h3 className="text-lg font-medium text-indigo-400 mb-4">Verification Statistics</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Pending Verifications</span>
                    <span className="text-indigo-400 font-semibold">25</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Verified Today</span>
                    <span className="text-green-400 font-semibold">12</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className={`${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>Total Processed</span>
                    <span className="text-indigo-400 font-semibold">150</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity Section */}
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
                      <option value="all" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>All Status</option>
                      <option value="verified" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Verified</option>
                      <option value="pending" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Pending</option>
                      <option value="not verified" className={isDarkMode ? 'bg-gray-700 text-white' : 'bg-white text-gray-700'}>Not Verified</option>
                    </select>
                    <div className={`pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 ${
                      isDarkMode ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                        <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                      </svg>
                    </div>
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
                    <IoSearchSharp className="absolute right-2 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 cursor-pointer hover:bg-gray-500 hover:text-gray-200 rounded transition-colors" />
                  </div>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className={`min-w-full divide-y ${isDarkMode ? 'divide-gray-600' : 'divide-gray-200'}`}>
                  <thead>
                    <tr>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Student Name</th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Status</th>
                      <th 
                        className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                          isDarkMode ? 'text-gray-300' : 'text-gray-500'
                        } cursor-pointer hover:text-indigo-500 transition-colors`}
                        onClick={() => handleSort('date')}
                      >
                        Date {getSortIcon('date')}
                      </th>
                    </tr>
                  </thead>
                  
                  <tbody className={`divide-y ${isDarkMode ? 'divide-gray-600' : 'divide-gray-200'}`}>
                    {filteredStudents.map((s) => (
                      <tr 
                        key={s.aadhaar_card_number} 
                        className={`${isDarkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-50'} cursor-pointer`}
                        onClick={() => handleStudentClick(s)}
                      >
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{s.student_name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            s.status === "Verified" ? (isDarkMode ? "bg-green-900 text-green-300" : "bg-green-100 text-green-800") : ""
                          } ${
                            s.status === "Pending" ? (isDarkMode ? "bg-yellow-900 text-yellow-300" : "bg-yellow-100 text-yellow-800") : ""
                          } ${
                            s.status === "Not Verified" ? (isDarkMode ? "bg-red-900 text-red-300" : "bg-red-100 text-red-800") : ""
                          }`}>{s.status}</span>
                        </td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>{s.date}</td>
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
