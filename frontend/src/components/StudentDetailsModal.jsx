import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { IoClose } from 'react-icons/io5';
import { FiEdit2, FiSave } from 'react-icons/fi';
import { students } from '../assets/Studentsdata.json';

const StudentDetailsModal = ({ isOpen, onClose, onSave }) => {
    const { isDarkMode } = useTheme();
    const [isEditing, setIsEditing] = useState(false);
    const [editedStudent, setEditedStudent] = useState(students);
    const [activeTab, setActiveTab] = useState('personal');

    const handleInputChange = (field, value) => {
        setEditedStudent(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const handleSave = () => {
        onSave(editedStudent);
        setIsEditing(false);
    };

    if (!isOpen) return null;

    const renderField = (label, field, type = "text", readOnly = false) => {
        return (
            <div className="mb-4">
                <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    {label}:
                </label>
                {type === 'boolean' ? (
                    <select
                        value={editedStudent[field] ? 'true' : 'false'}
                        onChange={(e) => handleInputChange(field, e.target.value === 'true')}
                        disabled={!isEditing || readOnly}
                        className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm ${
                            isDarkMode 
                                ? 'bg-gray-700 border-gray-600 text-white' 
                                : 'bg-white border-gray-300 text-gray-900'
                        } ${!isEditing || readOnly ? 'bg-opacity-50' : ''}`}
                    >
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                    </select>
                ) : (
                    <input
                        type={type}
                        value={editedStudent[field] || ''}
                        onChange={(e) => handleInputChange(field, e.target.value)}
                        readOnly={!isEditing || readOnly}
                        className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm ${
                            isDarkMode 
                                ? 'bg-gray-700 border-gray-600 text-white' 
                                : 'bg-white border-gray-300 text-gray-900'
                        } ${!isEditing || readOnly ? 'bg-opacity-50' : ''}`}
                    />
                )}
            </div>
        );
    };

    const tabs = [
        { id: 'personal', label: 'Personal Information' },
        { id: 'academic', label: 'Academic Information' },
        { id: 'contact', label: 'Contact Details' },
        { id: 'address', label: 'Address' },
        { id: 'category', label: 'Category & Status' }
    ];

    const renderTabContent = () => {
        switch (activeTab) {
            case 'personal':
                return (
                    <div className="space-y-4">
                        {renderField('Student ID', 'student_id', 'text', true)}
                        {renderField('Name', 'name')}
                        {renderField('Father Name', 'father_name')}
                        {renderField('Mother Name', 'mother_name')}
                        {renderField('Date of Birth', 'date_of_birth', 'date')}
                        {renderField('Gender', 'gender')}
                        {renderField('Blood Group', 'blood_group')}
                        {renderField('Nationality', 'nationality')}
                        {renderField('Religion', 'religion')}
                        {renderField('Mother Tongue', 'mother_tongue')}
                        {renderField('Identification Mark 1', 'identification_mark_1')}
                        {renderField('Identification Mark 2', 'identification_mark_2')}
                    </div>
                );
            case 'academic':
                return (
                    <div className="space-y-6">
                        <div>
                            <h5 className="font-medium mb-4">Basic Details</h5>
                            {renderField('Degree Code', 'degree_code')}
                            {renderField('Branch Code', 'branch_code')}
                            {renderField('Section', 'section')}
                        </div>
                        <div>
                            <h5 className="font-medium mb-4">10th Details</h5>
                            {renderField('Board Name', 'tenth_board_name')}
                            {renderField('School Name', 'tenth_school_name')}
                            {renderField('Hall Ticket No', 'tenth_hall_ticket_no')}
                            {renderField('Max Marks', 'tenth_max_marks', 'number')}
                            {renderField('Total Marks', 'tenth_total_marks')}
                            {renderField('Percentage', 'tenth_percentage', 'number')}
                            {renderField('Month & Year', 'tenth_month_year')}
                        </div>
                        <div>
                            <h5 className="font-medium mb-4">12th Details</h5>
                            {renderField('Board Name', 'twelfth_board_name')}
                            {renderField('College Name', 'twelfth_college_name')}
                            {renderField('Hall Ticket No', 'twelfth_hall_ticket_no')}
                            {renderField('Max Marks', 'twelfth_max_marks', 'number')}
                            {renderField('Total Marks', 'twelfth_total_marks')}
                            {renderField('Percentage', 'twelfth_percentage', 'number')}
                            {renderField('Month & Year', 'twelfth_month_year')}
                        </div>
                    </div>
                );
            case 'contact':
                return (
                    <div className="space-y-4">
                        {renderField('Student Phone', 'student_phone_no')}
                        {renderField('Parent Phone', 'parent_phone_no')}
                        {renderField('VNR Email', 'vnr_email', 'email')}
                        {renderField('Student Email', 'student_email', 'email')}
                        {renderField('Parent Email', 'parent_email', 'email')}
                    </div>
                );
            case 'address':
                return (
                    <div className="space-y-4">
                        {renderField('Door No', 'address_door_no')}
                        {renderField('Street', 'address_street')}
                        {renderField('Village/Town', 'address_village_town')}
                        {renderField('Mandal', 'address_mandal')}
                        {renderField('District', 'address_district')}
                        {renderField('State', 'address_state')}
                        {renderField('Pincode', 'address_pincode')}
                        {renderField('Rural/Urban', 'rural_urban')}
                    </div>
                );
            case 'category':
                return (
                    <div className="space-y-4">
                        {renderField('Category', 'category_name')}
                        {renderField('Caste as per TC', 'caste_as_per_tc')}
                        {renderField('Reservation', 'reservation', 'boolean')}
                        {renderField('EBC Status', 'ebc_status', 'boolean')}
                        {renderField('EWS Status', 'ews_status', 'boolean')}
                        {renderField('Income', 'income', 'number')}
                        {renderField('Minority Status', 'minority_status', 'boolean')}
                        {renderField('PH Status', 'ph_status', 'boolean')}
                        {renderField('Scribe Needed', 'scribe_needed', 'boolean')}
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="fixed inset-0 z-50" aria-labelledby="modal-title" role="dialog" aria-modal="true">
            <div className="flex items-center justify-center min-h-screen p-4">
                <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>

                <div className={`relative w-[95vw] max-w-7xl mx-auto rounded-lg shadow-xl ${
                    isDarkMode ? 'bg-gray-800' : 'bg-white'
                }`}>
                    {/* Header */}
                    <div className={`flex justify-between items-center px-6 py-4 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                        <h3 className={`text-xl font-medium ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            Student Details - {students.student_name}
                        </h3>
                        <div className="flex items-center space-x-2">
                            {!isEditing && (
                                <button
                                    onClick={() => setIsEditing(true)}
                                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                                >
                                    <FiEdit2 className={isDarkMode ? 'text-white' : 'text-gray-600'} />
                                </button>
                            )}
                            {isEditing && (
                                <button
                                    onClick={handleSave}
                                    className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                                >
                                    <FiSave className={isDarkMode ? 'text-white' : 'text-gray-600'} />
                                </button>
                            )}
                            <button
                                onClick={onClose}
                                className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                            >
                                <IoClose className={isDarkMode ? 'text-white' : 'text-gray-600'} size={20} />
                            </button>
                        </div>
                    </div>

                    {/* Main Content Area */}
                    <div className="flex h-[75vh]">
                        {/* Left Side - Photo */}
                        <div className="w-1/4 p-6 border-r border-gray-200">
                            <img
                                src={students.image_url || 'https://via.placeholder.com/300x400?text=Student+Photo'}
                                alt="Student"
                                className="w-full rounded-lg shadow-lg object-cover aspect-[3/4]"
                            />
                        </div>

                        {/* Right Side - Content */}
                        <div className="w-3/4 flex flex-col">
                            {/* Tabs */}
                            <div className={`flex space-x-1 px-6 py-3 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-200'} bg-inherit`}>
                                {tabs.map(tab => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id)}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
                                            ${activeTab === tab.id
                                                ? isDarkMode
                                                    ? 'bg-gray-700 text-white'
                                                    : 'bg-gray-100 text-gray-900'
                                                : isDarkMode
                                                    ? 'text-gray-400 hover:text-white hover:bg-gray-700'
                                                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                                            }`}
                                    >
                                        {tab.label}
                                    </button>
                                ))}
                            </div>

                            {/* Scrollable Content */}
                            <div className="flex-1 overflow-y-auto">
                                <div className="p-6 pb-20">
                                    {renderTabContent()}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StudentDetailsModal; 