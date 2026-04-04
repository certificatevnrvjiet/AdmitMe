import React from 'react';

const StatsCards = ({ 
    students, 
    isDarkMode, 
    userRole, 
    submitted_students, 
    approved_students, 
    under_review_students, 
    total_students_processed 
}) => {

    const getDepartmentName = (dept) => {
        const deptNames = {
            admin: 'Administrator',
            cse: 'Computer Science',
            ece: 'Electronics and Communication',
            eee: 'Electrical and Electronics',
            me: 'Mechanical',
            ce: 'Civil',
        };
        return deptNames[dept] || dept.toUpperCase();
    };

    const getDepartmentStats = () => {
        const departments = [
            'cse', 'ece', 'eee', 'me', 'ce', 'aids', 'ae', 'csbs', 'aiml', 'cseds', 'csecys', 'cseiot', 'eie', 'it', 'vlsi', 'biotechnology', 'roboticsandai'
        ];
        return departments.map(dept => {
            const deptStudents = students.filter(s => (s.branch_code || '').toLowerCase() === dept);
            return {
                name: getDepartmentName(dept),
                total: deptStudents.length,
                approved: deptStudents.filter(s => (s.status || '').toLowerCase() === 'approved').length,
                underReview: deptStudents.filter(s => (s.status || '').toLowerCase() === 'under_review').length,
                submitted: deptStudents.filter(s => (s.status || '').toLowerCase() === 'submitted').length,
            };
        }).filter(stat => stat.total > 0);
    };

    return (
        <>
            {/* Stats */}
            <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
                <div className="p-6">
                    <h3 className="text-lg font-medium text-indigo-400 mb-4">Verification Statistics</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Submitted</span><span className="text-indigo-400 font-semibold">{submitted_students}</span></div>
                        <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Under Review</span><span className="text-yellow-400 font-semibold">{under_review_students}</span></div>
                        <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Approved</span><span className="text-green-400 font-semibold">{approved_students}</span></div>
                        <div className="flex justify-between"><span className={isDarkMode ? 'text-gray-300' : 'text-gray-600'}>Total Students</span><span className="text-indigo-400 font-semibold">{total_students_processed}</span></div>
                    </div>
                </div>
            </div>
            
            {userRole === 'admin' && (
                <div
                    className={`shadow-sm rounded-lg h-60 ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}
                    style={{ height: '25rem', display: 'flex', flexDirection: 'column' }}
                >
                    <div className="p-6" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                        <h3 className="text-lg font-medium text-indigo-400 mb-4">Department-wise Statistics</h3>
                        <div className="overflow-y-auto" style={{ flex: 1 }}>
                            <table className={`min-w-full divide-y ${isDarkMode ? 'divide-gray-600' : 'divide-gray-200'}`}>
                                <thead>
                                    <tr>
                                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Department</th>
                                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Total</th>
                                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Approved</th>
                                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Under Review</th>
                                        <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${isDarkMode ? 'text-gray-300' : 'text-gray-500'}`}>Submitted</th>
                                    </tr>
                                </thead>
                                <tbody className={`divide-y ${isDarkMode ? 'divide-gray-600' : 'divide-gray-200'}`}>
                                    {getDepartmentStats().map(stat => (
                                        <tr key={stat.name}>
                                            <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-gray-100' : 'text-gray-900'}`}>{stat.name}</td>
                                            <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-indigo-400' : 'text-indigo-600'}`}>{stat.total}</td>
                                            <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-green-400' : 'text-green-600'}`}>{stat.approved}</td>
                                            <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-yellow-400' : 'text-yellow-600'}`}>{stat.underReview}</td>
                                            <td className={`px-6 py-4 whitespace-nowrap text-sm ${isDarkMode ? 'text-red-400' : 'text-red-600'}`}>{stat.submitted}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default StatsCards;
