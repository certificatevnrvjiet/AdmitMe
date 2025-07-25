import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { IoClose } from 'react-icons/io5';
import { FiEdit2, FiSave } from 'react-icons/fi';
import { students } from '../assets/Students.json';
import { getImageUrl } from '../api';
import API from '../api'
import ScrollableTabs from './ScrollableTabs';


const StudentDetailsModal = ({ isOpen, onClose, onSave, student }) => {
    const { isDarkMode } = useTheme();
    const [isEditing, setIsEditing] = useState(false);
    const [editedStudent, setEditedStudent] = useState(student || {}); // Initialize with the passed student
    const [activeTab, setActiveTab] = useState('Personal Information');
    const [activeImageTab, setActiveImageTab] = useState('Aadhaar Card');
    const [isSaving, setIsSaving] = useState(false); // Add this state
    const [imageLoading, setImageLoading] = useState(false);
    const [imageError, setImageError] = useState(false);
    const [zoomLevel, setZoomLevel] = useState(1); // Add zoom state

    // Update `editedStudent` whenever the `student` prop changes
    React.useEffect(() => {
        setEditedStudent(student || {});
        setImageError(false);
        setImageLoading(true); // Set loading to true when student changes
        setZoomLevel(1); // Reset zoom when student changes
    }, [student]);

    const validateStudentId = (id) => {
        if (!id) return true; // Allow empty/null
        if (id.length !== 10) return false;
        const first5 = id.substring(0, 5);
        const rest = id.substring(5);
        return /^\d{5}$/.test(first5) && /^[a-zA-Z0-9]+$/.test(rest);
    };

    const handleInputChange = (field, value) => {
        setEditedStudent((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    const handleSave = async () => {
      if (!validateStudentId(editedStudent.ht_no)) {
              alert('Student ID must be empty or 10 characters long with first 5 digits and remaining alphanumeric');
              return;
          }
        try {
            setIsSaving(true);
            editedStudent.status = 'Verified'; // Set status to Verified
            await onSave(editedStudent);
            setIsEditing(false);
        } catch (error) {
            console.error('Error saving student:', error);
            alert(error.message || 'Failed to save changes. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleDraft = async () => {

          if (!validateStudentId(editedStudent.ht_no)) {
              alert('Student ID must be empty or 10 characters long with first 5 digits and remaining alphanumeric');
              return;
          }

        try {
            setIsSaving(true);
            editedStudent.status = 'Pending'; // Set status to Draft
            await onSave(editedStudent);
            setIsEditing(false);
        } catch (error) {
            console.error('Error saving draft:', error);
            alert(error.message || 'Failed to save draft. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleImageLoad = () => {
        setImageLoading(false);
        setImageError(false);
    };

    const handleImageError = () => {
        setImageLoading(false);
        setImageError(true);
    };

    // Handle zoom functionality
    const handleWheel = (e) => {
        // Only zoom if Ctrl key is held
        if (e.ctrlKey) {
            e.preventDefault();
            const delta = e.deltaY;
            const zoomFactor = 0.1;
            if (delta < 0) {
                // Scroll up - zoom in
                setZoomLevel(prev => Math.min(prev + zoomFactor, 3)); // Max zoom 3x
            } else {
                // Scroll down - zoom out
                setZoomLevel(prev => Math.max(prev - zoomFactor, 0.5)); // Min zoom 0.5x
            }
        }
        // Otherwise, allow default scroll for panning
    };

    // Handle zoom buttons
    const handleZoomIn = () => {
        setZoomLevel(prev => Math.min(prev + 0.2, 3));
    };

    const handleZoomOut = () => {
        setZoomLevel(prev => Math.max(prev - 0.2, 0.5));
    };

    const handleResetZoom = () => {
        setZoomLevel(1);
    };

    const getImageSource = () => {
        let imageField = '';
        switch (activeImageTab) {
            case 'Aadhaar Card':
                imageField = 'aadhaar_link';
                break;
            case 'Transfer Certificate':
                imageField = 'transfer_certificate_link';
                break;
            case '10th Memo':
                imageField = 'tenth_memo_link';
                break;
            case '12th Memo':
                imageField = 'twelfth_memo_link';
                break;
            case 'JEE Rank Card':
                imageField = 'jee_rank_card_link';
                break;
            default:
                imageField = 'aadhaar_link';
                break;
        }
        
        if (editedStudent[imageField]) {
            const linkstr = editedStudent[imageField];
            const match = linkstr.match(/id=([a-zA-Z0-9_-]+)/);
            const fileId = match ? match[1] : null;
            const imageUrl = getImageUrl(fileId);
            return imageUrl;
        }
        return null;
    };

    // Update image loading state when image tab changes
    React.useEffect(() => {
        setImageError(false);
        setImageLoading(true);
        setZoomLevel(1); // Reset zoom when image tab changes
    }, [activeImageTab]);

    // Helper function to format date as DD/MM/YYYY
    function formatDateDMY(dateString) {
      if (!dateString) return '';
      // If already in DD/MM/YYYY or DD-MM-YYYY, return as is
      if (/^\d{2}[\/\-]\d{2}[\/\-]\d{4}$/.test(dateString)) {
        return dateString.replace(/\-/g, '/'); // convert DD-MM-YYYY to DD/MM/YYYY
      }
      // Try to parse ISO or US format
      const date = new Date(dateString);
      if (isNaN(date)) return dateString; // fallback if invalid
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}/${month}/${year}`;
    }

    if (!isOpen) return null;

    const renderField = (label, field, type = 'text', readOnly = false) => {
        return (
            <div className="mb-4">
                <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>{label}:</label>
                <input
                    type="text"
                    value={field === 'date_of_birth' && !isEditing ? formatDateDMY(editedStudent[field]) : (editedStudent[field] || '')}
                    onChange={(e) => handleInputChange(field, e.target.value)}
                    readOnly={!isEditing || readOnly}
                    className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm ${
                        isDarkMode
                            ? 'bg-gray-700 border-gray-600 text-white'
                            : 'bg-white border-gray-300 text-gray-900'
                    } ${!isEditing || readOnly ? 'bg-opacity-50' : ''}`}
                />
            </div>
        );
    };

    // Form tabs
    const formTabs = [
        'Personal Information',
        'Academic Information',
        'Contact Details',
        'Category & Status',
        'Address',
    ];

    // Image tabs
    const imageTabs = [
        'Aadhaar Card',
        'Transfer Certificate',
        '10th Memo',
        '12th Memo',
        'JEE Rank Card',
    ];

    const renderTabContent = () => {
        switch (activeTab) {
            case 'Personal Information':
                return (
                    <div className="space-y-4">
                        {renderField('Student ID', 'ht_no', 'text')}
                        {renderField('Name', 'student_name')}
                        {renderField('Father Name', 'father_name')}
                        {renderField('Mother Name', 'mother_name')}
                        {renderField('Date of Birth', 'date_of_birth')}
                        {renderField('Gender', 'gender')}
                        {renderField('Blood Group', 'blood_group')}
                        {renderField('Mother Tongue', 'mother_tongue')}
                        {renderField('Identification Mark 1', 'identification_mark_1')}
                        {renderField('Aadhaar Number', 'aadhaar_card_number')}
                    </div>
                );
            case 'Academic Information':
                return (
                    <div className="space-y-6">
                        <div>
                            <h5 className="font-medium mb-4">Basic Details</h5>
                            {renderField('College Code', 'college_code')}
                            {renderField('Branch Code', 'branch_code')}
                            {renderField('Admission Category', 'admission_category')}
                            {renderField('UG Code', 'degree_code')}
                        </div>
                        <div>
                            <h5 className="font-medium mb-4">10th Details</h5>
                            {renderField('Board Name', 'tenth_board_name')}
                            {renderField('School Name', 'tenth_school_name')}
                            {renderField('Hall Ticket No', 'tenth_ht_no')}
                            {renderField('Max Marks', 'tenth_maximum_marks')}
                            {renderField('Total Marks', 'tenth_total_marks_cgpa')}
                            {renderField('Percentage', 'tenth_percentage')}
                            {renderField('Month & Year', 'tenth_month_year')}
                        </div>
                        <div>
                            <h5 className="font-medium mb-4">12th Details</h5>
                            {renderField('Board Name', 'twelfth_board_name')}
                            {renderField('College Name', 'twelfth_college_name')}
                            {renderField('Hall Ticket No', 'twelfth_ht_no')}
                            {/* 5x2 grid for subject scores */}
                            <div className="grid grid-cols-2 gap-4 mb-4">
                                <div>
                                    {renderField('M1', 'm1')}
                                </div>
                                <div>
                                    {renderField('M2', 'm2')}
                                </div>
                                <div>
                                    {renderField('M3', 'm3')}
                                </div>
                                <div>
                                    {renderField('M4', 'm4')}
                                </div>
                                <div>
                                    {renderField('P1', 'p1')}
                                </div>
                                <div>
                                    {renderField('P2', 'p2')}
                                </div>
                                <div>
                                    {renderField('C1', 'ch1')}
                                </div>
                                <div>
                                    {renderField('C2', 'ch2')}
                                </div>
                                <div>
                                    {renderField('CLAB', 'chlab')}
                                </div>
                                <div>
                                    {renderField('PLAB', 'plab')}
                                </div>
                            </div>
                            {renderField('Max Marks', 'twelfth_maximum_marks')}
                            {renderField('Total Marks', 'twelfth_total_marks')}
                            {renderField('Percentage', 'twelfth_percentage')}
                            {renderField('Month & Year', 'twelfth_month_year')}
                        </div>
                    </div>
                );
            case 'Contact Details':
                return (
                    <div className="space-y-4">
                        {renderField('Student Phone', 'student_phone')}
                        {renderField('Parent Phone', 'parent_phone')}
                        {renderField('Student Email', 'student_email')}
                        {renderField('Parent Email', 'parent_email')}
                    </div>
                );
            case 'Address':
                return (
                    <div className="space-y-4">
                        {renderField('Street', 'address_street')}
                        {renderField('Village/Town', 'address_village_town')}
                        {renderField('Mandal', 'address_mandal')}
                        {renderField('District', 'address_district')}
                        {renderField('State', 'address_state')}
                        {renderField('Pincode', 'address_pincode')}
                    </div>
                );
            case 'Category & Status':
                return (
                    <div className="space-y-4">
                        {renderField('Nationality', 'nationality')}
                        {renderField('Religion', 'religion')}
                        {renderField('Category', 'category_name')}
                        {renderField('Caste as per TC', 'caste_as_per_tc')}
                        {renderField('Reservation', 'reservation')}
                        {renderField('EBC Status', 'ebc_status')}
                        {renderField('EWS Status', 'ews_status')}
                        {renderField('Income', 'income')}
                        {renderField('Minority Status', 'minority')}
                        {renderField('PH Status', 'ph_status')}
                        {renderField('Scribe Needed', 'scribe')}
                    </div>
                );
            default:
                return null;
        }
    };

    return isOpen ? (
        <div className="fixed top-[64px] bottom-[90px] left-0 right-0 z-50 flex items-center justify-center">
            {/* Blurry Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />
            
            {/* Modal */}
            <div
                className="relative z-10 bg-white rounded-lg shadow-lg max-w-6xl w-full flex flex-col"
                style={{ maxHeight: 'calc(100vh - 128px)' }}
            >
                {/* Top Action Bar */}
                <div className="w-full bg-white rounded-lg border border-gray-200 dark:border-gray-700 p-4 flex justify-between space-x-2">
                    <h3
                        className={`text-xl font-medium ${
                            isDarkMode ? 'text-white' : 'text-gray-900'
                        }`}
                    >
                        Student Details - {editedStudent.student_name}
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
                            <>
                                <button
                                    onClick={handleSave}
                                    disabled={isSaving}
                                    className="p-2 rounded-full hover:bg-green-100 dark:hover:bg-green-700"
                                >
                                    {isSaving ? (
                                        <span className="inline-flex items-center">
                                            <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                                                <circle
                                                    className="opacity-25"
                                                    cx="12"
                                                    cy="12"
                                                    r="10"
                                                    stroke="currentColor"
                                                    strokeWidth="4"
                                                    fill="none"
                                                />
                                                <path
                                                    className="opacity-75"
                                                    fill="currentColor"
                                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                                />
                                            </svg>
                                            Saving...
                                        </span>
                                    ) : <span className={isDarkMode ? 'text-green-300' : 'text-green-600'}>Mark as Verified</span>}
                                </button>
                                <button
                                    onClick={handleDraft}
                                    disabled={isSaving}
                                    className="p-2 rounded-full hover:bg-yellow-100 dark:hover:bg-yellow-700"
                                    title="Save as Draft"
                                >
                                    <span className={isDarkMode ? 'text-yellow-300' : 'text-yellow-600'}>Mark as Pending</span>
                                </button>
                            </>
                        )}
                        <button
                            onClick={onClose}
                            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
                        >
                            <IoClose className={isDarkMode ? 'text-white' : 'text-gray-600'} size={20} />
                        </button>
                    </div>
                </div>

                <div className="flex flex-row">
                    {/* Left: Image Tabs and Image Display */}
                    <div className="w-2/3 p-4 flex flex-col" style={{ maxHeight: 'calc(100vh - 200px)' }}>
                        {/* Image Tabs */}
                        <div className="mb-4">
                            <ScrollableTabs tabs={imageTabs} activeTab={activeImageTab} setActiveTab={setActiveImageTab} />
                        </div>
                        
                        {/* Image Display with Zoom */}
                        <div 
                            className="flex-1 border rounded-lg p-4 relative overflow-hidden" 
                            style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                            onWheel={handleWheel}
                        >
                            {/* Zoom Controls */}
                            <div className="absolute top-2 right-2 z-10 flex items-center space-x-2 bg-white bg-opacity-90 rounded-lg px-3 py-2 shadow-lg">
                                <button
                                    onClick={handleZoomOut}
                                    className="p-1 rounded hover:bg-gray-200 text-gray-600"
                                    title="Zoom Out"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                                    </svg>
                                </button>
                                <span className="text-sm font-medium min-w-[3rem] text-center">
                                    {Math.round(zoomLevel * 100)}%
                                </span>
                                <button
                                    onClick={handleZoomIn}
                                    className="p-1 rounded hover:bg-gray-200 text-gray-600"
                                    title="Zoom In"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                                    </svg>
                                </button>
                                <button
                                    onClick={handleResetZoom}
                                    className="p-1 rounded hover:bg-gray-200 text-gray-600"
                                    title="Reset Zoom"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                                    </svg>
                                </button>
                            </div>
                            
                            {/* Scrollable Image Container */}
                            <div className="w-full h-full overflow-auto">
                                {getImageSource() ? (
                                    <>
                                        {imageLoading && (
                                            <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
                                                <svg className="animate-spin h-8 w-8 text-gray-500" viewBox="0 0 24 24">
                                                    <circle
                                                        className="opacity-25"
                                                        cx="12"
                                                        cy="12"
                                                        r="10"
                                                        stroke="currentColor"
                                                        strokeWidth="4"
                                                        fill="none"
                                                    />
                                                    <path
                                                        className="opacity-75"
                                                        fill="currentColor"
                                                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                                    />
                                                </svg>
                                            </div>
                                        )}
                                        {imageError ? (
                                            <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg text-gray-500">
                                                <div className="text-center">
                                                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                    </svg>
                                                    <p className="mt-2 text-sm">Image not available</p>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="flex justify-center items-center min-h-full p-4">
                                                <img
                                                    src={getImageSource()}
                                                    alt={`${activeImageTab} Document`}
                                                    className="object-contain rounded-lg shadow-lg transition-transform duration-200"
                                                    style={{ 
                                                        transform: `scale(${zoomLevel})`,
                                                        maxWidth: '100%',
                                                        maxHeight: '100%',
                                                        display: imageLoading ? 'none' : 'block'
                                                    }}
                                                    onLoad={handleImageLoad}
                                                    onError={handleImageError}
                                                />
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg text-gray-500">
                                        <div className="text-center">
                                            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                            </svg>
                                            <p className="mt-2 text-sm">No {activeImageTab.toLowerCase()} available</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Right: Form Tabs and Content */}
                    <div className="w-1/3 p-4 flex flex-col border-l" style={{ maxHeight: 'calc(100vh - 200px)' }}>
                        <ScrollableTabs tabs={formTabs} activeTab={activeTab} setActiveTab={setActiveTab} />
                        {/* Tab Content */}
                        <div className="flex-1 overflow-y-auto mt-4" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
                            {renderTabContent()}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    ) : null;
};

export default StudentDetailsModal;