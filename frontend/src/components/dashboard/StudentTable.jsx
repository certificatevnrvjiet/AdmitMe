import React from 'react';
import { IoArrowUp, IoArrowDown } from "react-icons/io5";

const StudentTable = ({
    filteredStudents,
    isDarkMode,
    handleSort,
    getSortIcon,
    handleStudentClick,
    formatDateDMY
}) => {
    return (
        <div className="overflow-x-auto">
            <table className={`min-w-full divide-y ${isDarkMode ? 'divide-gray-600' : 'divide-gray-200'}`}>
                <thead>
                    <tr>
                        <th
                            className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'
                                } cursor-pointer hover:text-indigo-500`}
                            onClick={() => handleSort('student_id')}
                        >Student ID {getSortIcon('student_id')}</th>
                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'
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
                                <span
                                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                        (s.status || "").toLowerCase() === "approved"
                                            ? (isDarkMode ? "bg-green-900 text-green-300" : "bg-green-100 text-green-800")
                                            : (s.status || "").toLowerCase() === "under_review"
                                                ? (isDarkMode ? "bg-yellow-900 text-yellow-300" : "bg-yellow-100 text-yellow-800")
                                                : (s.status || "").toLowerCase() === "submitted"
                                                    ? (isDarkMode ? "bg-blue-900 text-blue-300" : "bg-blue-100 text-blue-800")
                                                    : (isDarkMode ? "bg-red-900 text-red-300" : "bg-red-100 text-red-800")
                                    }`}
                                >
                                    {s.status}
                                </span>
                            </td>
                            <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>{s.branch_code}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default StudentTable;
