import React, { useState, useEffect } from 'react';
import { IoSearchSharp, IoArrowUp, IoArrowDown } from "react-icons/io5";
import { RiArrowDropDownLine } from "react-icons/ri";
import { useTheme } from '../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import StudentDetailsModal from '../components/StudentDetailsModal';

const Dashboard = ({ department }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortConfig, setSortConfig] = useState({ key: 'name', direction: 'asc' });
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { isDarkMode } = useTheme();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStudents = async () => {
      try {
        setLoading(true);
        const response = await fetch('http://localhost:8000/students', {
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
        // console.log('Fetched students:', data.students);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching students:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchStudents();
     // Debugging line

  }, []);

  // console.log('students:', students); 

  // Flatten data: students = [{ data: {...} }, ...] → studentList = [{...}, {...}]
  const studentList = students.map((s) => s.data || s);

  // Sort logic (based on name)
  const sortData = (data) => {
    return [...data].sort((a, b) => {
      const aVal = a[sortConfig.key]?.toLowerCase?.() || '';
      const bVal = b[sortConfig.key]?.toLowerCase?.() || '';
      return sortConfig.direction === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
  };

  // Filter students by department, search term, and status
  const filteredStudents = sortData(
    studentList.filter((s) => {
      const matchesSearch = s.name?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesDepartment = department === 'admin' ? true : s.department === department;
      const matchesStatus = statusFilter === 'all' ? true : s.status?.toLowerCase() === statusFilter;
      return matchesSearch && matchesDepartment && matchesStatus;
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
        // const cleanedStudent = {
        //     ...updatedStudent,
        //     // Handle numeric fields with null fallback
        //     tenth_max_marks: updatedStudent.tenth_max_marks ? parseInt(updatedStudent.tenth_max_marks) : null,
        //     twelfth_max_marks: updatedStudent.twelfth_max_marks ? parseInt(updatedStudent.twelfth_max_marks) : null,
        //     tenth_percentage: updatedStudent.tenth_percentage ? parseFloat(updatedStudent.tenth_percentage) : null,
        //     twelfth_percentage: updatedStudent.twelfth_percentage ? parseFloat(updatedStudent.twelfth_percentage) : null,
        //     eamcet_rank: updatedStudent.eamcet_rank ? parseInt(updatedStudent.eamcet_rank) : null,
        //     jee_mains_rank: updatedStudent.jee_mains_rank ? parseInt(updatedStudent.jee_mains_rank) : null,
        //     income: updatedStudent.income ? parseInt(updatedStudent.income) : null,

        //     // Handle boolean fields
        //     reservation: Boolean(updatedStudent.reservation),
        //     ebc_status: Boolean(updatedStudent.ebc_status),
        //     ews_status: Boolean(updatedStudent.ews_status),
        //     minority_status: Boolean(updatedStudent.minority_status),
        //     ph_status: Boolean(updatedStudent.ph_status),
        //     scribe_needed: Boolean(updatedStudent.scribe_needed),

        //     // Handle date_of_birth
        //     date_of_birth: updatedStudent.date_of_birth ? 
        //         new Date(updatedStudent.date_of_birth)
        //             .toLocaleDateString('en-GB', {
        //                 day: '2-digit',
        //                 month: '2-digit',
        //                 year: 'numeric'
        //             }).split('/').join('/') : null,
        // };

        // // Remove empty values
        // Object.keys(cleanedStudent).forEach(key => {
        //     if (cleanedStudent[key] === undefined || cleanedStudent[key] === null || cleanedStudent[key] === '') {
        //         delete cleanedStudent[key];
        //     }
        // });

        console.log('Sending student data hii:', updatedStudent);
        console.log('Scores :',updatedStudent.twelfth_subject_scores);

        const response = await fetch(`http://localhost:8000/student/${updatedStudent.id}`, {
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
            student.id === updatedStudent.id ? { ...student, ...updatedStudent  } : student
        ));
        
        console.log('Student updated successfully:', result);
        handleCloseModal();
    } catch (error) {
        console.error('Error updating student:', error);
        alert(error.message || 'Failed to update student details. Please try again.');
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
            <div className="relative">
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
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Quick Actions */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
              <div className="p-6">
                <h3 className="text-lg font-medium text-indigo-400 mb-4">Quick Actions</h3>
                <div className="space-y-4">
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
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Pending Verifications</span><span className="text-indigo-400 font-semibold">25</span></div>
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Verified Today</span><span className="text-green-400 font-semibold">12</span></div>
                  <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Total Processed</span><span className="text-indigo-400 font-semibold">150</span></div>
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
                        key={s.id}
                        className={`${isDarkMode ? 'hover:bg-gray-600' : 'hover:bg-gray-50'} cursor-pointer`}
                        onClick={() => handleStudentClick(s)}
                      >
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{s.student_id}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{s.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            s.Status === "Verified" ? (isDarkMode ? "bg-green-900 text-green-300" : "bg-green-100 text-green-800") :
                            s.Status === "Pending" ? (isDarkMode ? "bg-yellow-900 text-yellow-300" : "bg-yellow-100 text-yellow-800") :
                            (isDarkMode ? "bg-red-900 text-red-300" : "bg-red-100 text-red-800")
                          }`}>{s.Status}</span>
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
