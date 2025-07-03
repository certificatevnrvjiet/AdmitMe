import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { IoClose } from 'react-icons/io5';
import { FiEdit2, FiSave } from 'react-icons/fi';
import { students } from '../assets/Students.json';
import { getImageUrl } from '../api';
import API from '../api'


const StudentDetailsModal = ({ isOpen, onClose, onSave, student }) => {
    const { isDarkMode } = useTheme();
    const [isEditing, setIsEditing] = useState(false);
    const [editedStudent, setEditedStudent] = useState(student || {}); // Initialize with the passed student
    const [activeTab, setActiveTab] = useState('personal');
    const [isSaving, setIsSaving] = useState(false); // Add this state
    const [imageLoading, setImageLoading] = useState(false);
    const [imageError, setImageError] = useState(false);
    console.log('Initial student prop:', student);
    // Update `editedStudent` whenever the `student` prop changes
    React.useEffect(() => {
        setEditedStudent(student || {});
        setImageError(false);
        setImageLoading(true); // Set loading to true when student changes
    }, [student]);

    const handleInputChange = (field, value) => {
        setEditedStudent((prev) => ({
            ...prev,
            [field]: value,
        }));
        console.log('Student prop updated:', editedStudent.twelfth_subject_scores);
    };

    const handleSave = async () => {
        try {
            setIsSaving(true);
            console.log('Saving student:', editedStudent.aadhaar_card_number);
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

    const getImageSource = () => {
        // Define image fields based on active tab
        let imageFields = [];
        
        switch (activeTab) {
            case 'personal':
                imageFields = ['tenth_memo_link'];
                break;
            case 'academic':
                imageFields = [ 'twelfth_memo_link'];
                break;
            case 'contact':
                imageFields = ['aadhaar_link'];
                break;
            case 'address':
                imageFields = ['aadhaar_link'];
                break;
            case 'category':
                imageFields = ['transfer_certificate_link'];
                break;
            default:
                imageFields = ['aadhaar_link'];
                break;
        }
        
        for (const field of imageFields) {
            if (editedStudent[field]) {
                const linkstr = editedStudent[field];
                const match = linkstr.match(/id=([a-zA-Z0-9_-]+)/);
                const fileId = match ? match[1] : null;
                const imageUrl = getImageUrl(fileId);
                console.log('Image URL:', imageUrl);
                console.log('Image Source:', activeTab);
                return imageUrl;

            }
        }
        return null;
    };

    // Update image loading state when tab changes
    React.useEffect(() => {
        setImageError(false);
        setImageLoading(true);
    }, [activeTab]);

    if (!isOpen) return null;

    const renderField = (label, field, type = 'text', readOnly = false) => {
        return (
            <div className="mb-4">
                <label className={`block text-sm font-medium ${isDarkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                    {label}:
                </label>
                <input
                    type="text"
                    value={editedStudent[field] || ''}
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

    const tabs = [
        { id: 'personal', label: 'Personal Information' },
        { id: 'academic', label: 'Academic Information' },
        { id: 'contact', label: 'Contact Details' },
        { id: 'category', label: 'Category & Status' },
        { id: 'address', label: 'Address' },
    ];

    const renderTabContent = () => {
        switch (activeTab) {
            case 'personal':
                return (
                    <div className="space-y-4">
                        {renderField('Student ID', 'ht_no', 'text')}
                        {renderField('Name', 'student_name')}
                        {renderField('Father Name', 'father_name')}
                        {renderField('Mother Name', 'mother_name')}
                        {renderField('Date of Birth', 'date_of_birth')}
                        {renderField('Gender', 'gender')}
                        {renderField('Blood Group', 'blood_group')}
                        {renderField('Nationality', 'nationality')}
                        {renderField('Religion', 'religion')}
                        {renderField('Mother Tongue', 'mother_tongue')}
                        {renderField('Identification Mark 1', 'identification_mark_1')}
                        {renderField('Aadhaar Number', 'aadhaar_card_number')}
                        {/* aadhaar_card_number */}
                    </div>
                );
            case 'academic':
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
            case 'contact':
                return (
                    <div className="space-y-4">
                        {renderField('Student Phone', 'student_phone')}
                        {renderField('Parent Phone', 'parent_phone')}
                        {renderField('Student Email', 'student_email')}
                        {renderField('Parent Email', 'parent_email')}
                    </div>
                );
            case 'address':
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
            case 'category':
                return (
                    <div className="space-y-4">
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
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Blurry Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-40 backdrop-blur-sm transition-opacity"
                onClick={onClose}
            />
            {/* Modal */}
            <div className="relative z-10 bg-white dark:bg-gray-800 rounded-lg shadow-lg max-w-4xl w-full mx-4 flex flex-col"
                 style={{ maxHeight: '80vh' }}>
              <div className="flex flex-row h-full">
                {/* Left: Image (scrollable) */}
                <div className="w-1/3 p-4 overflow-y-auto" style={{ maxHeight: '60vh' }}>
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
                            <img
                                src={getImageSource()}
                                alt="Student Document"
                                className="w-full rounded-lg shadow-lg object-cover aspect-[3/4]"
                                onLoad={handleImageLoad}
                                onError={handleImageError}
                                style={{ display: imageLoading ? 'none' : 'block' }}
                            />
                        )}
                      </>
                  ) : (
                      <div className="flex items-center justify-center h-64 bg-gray-100 rounded-lg text-gray-500">
                        <div className="text-center">
                          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <p className="mt-2 text-sm">No document available</p>
                        </div>
                      </div>
                  )}
                </div>

                {/* Right: Tabs and Content */}
                <div className="w-2/3 p-4 flex flex-col">
                  {/* Tabs (horizontal scroll) */}
                  <div className="flex space-x-4 overflow-x-auto pb-2">
                    {tabs.map(tab => (
                      <button
                        key={tab.id}
                        className={`px-4 py-2 whitespace-nowrap rounded-md ${activeTab === tab.id ? 'bg-indigo-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200'}`}
                        onClick={() => setActiveTab(tab.id)}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>
                  {/* Tab Content */}
                  <div className="flex-1 overflow-y-auto mt-4">
                    {renderTabContent()}
                  </div>
                </div>
              </div>
              {/* Fixed Footer */}
              <div className="sticky bottom-0 left-0 w-full bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 p-4 flex justify-end space-x-2">
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
                            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
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
                          ) : (
                              <FiSave className={isDarkMode ? 'text-white' : 'text-gray-600'} />
                          )}
                        </button>
                        <button
                            onClick={handleDraft}
                            disabled={isSaving}
                            className="p-2 rounded-full hover:bg-yellow-100 dark:hover:bg-yellow-700"
                            title="Save as Draft"
                        >
                          <span className={isDarkMode ? 'text-yellow-300' : 'text-yellow-600'}>
                            Draft
                          </span>
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
            </div>
        </div>
    ) : null;
};

export default StudentDetailsModal;