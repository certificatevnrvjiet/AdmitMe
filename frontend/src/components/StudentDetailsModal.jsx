import React, { useState } from 'react';
import { useTheme } from '../context/ThemeContext';
import { IoClose } from 'react-icons/io5';
import { FiEdit2, FiSave } from 'react-icons/fi';
import { getImageUrl, getStudentDocumentUrl } from '../api';
import API from '../api'
import ScrollableTabs from './ScrollableTabs';
import useDisableBrowserZoom from './useDisableBrowserZoom';

const StudentDetailsModal = ({ isOpen, onClose, onSave, student, headerHeightVh = 10, footerHeightVh = 12 }) => {
    const { isDarkMode } = useTheme();
    const [isEditing, setIsEditing] = useState(false);
    const [editedStudent, setEditedStudent] = useState(student || {}); // Initialize with the passed student
    const [activeTab, setActiveTab] = useState('Personal Information');
    const [activeImageTab, setActiveImageTab] = useState('Aadhaar Card');
    // Check if student type is LE (must be before any use)
    const isLE = student?.student_type?.toLowerCase() === 'le';
    // Track the active academic sub-section (10th, 12th, Diploma)
    const [activeAcademicSection, setActiveAcademicSection] = useState(isLE ? 'Diploma' : '10th');

    // Branch codes for dropdown (using uppercase values to match database format)
    const branchCodes = [
        { value: 'AIDS', label: 'AIDS' },
        { value: 'AE', label: 'AE' },
        { value: 'CE', label: 'CE' },
        { value: 'CSBS', label: 'CSBS' },
        { value: 'CSE', label: 'CSE' },
        { value: 'AIML', label: 'AIML' },
        { value: 'CSEDS', label: 'CSE-DS' },
        { value: 'CSECYS', label: 'CSE-CYS' },
        { value: 'CSEIOT', label: 'CSE-IOT' },
        { value: 'EEE', label: 'EEE' },
        { value: 'ECE', label: 'ECE' },
        { value: 'EIE', label: 'EIE' },
        { value: 'IT', label: 'IT' },
        { value: 'ME', label: 'ME' },
        { value: 'VLSI', label: 'VLSI' },
        { value: 'BIOTECHNOLOGY', label: 'Biotechnology' },
        { value: 'ROBOTICSANDAI', label: 'Robotics and AI' },
    ];

    // Mapping from form tab to default image tab
    const tabToImageTab = {
        'Personal Information': 'Aadhaar Card',
        'Academic Information': isLE ? 'Diploma Certificate' : '10th Memo',
        'Contact Details': 'Aadhaar Card',
        'Category & Status': 'Transfer Certificate',
        'Address': 'Aadhaar Card',
    };

    // Academic sub-sections and mapping to image tabs
    const academicSections = isLE
        ? [
            { label: '10th Details', value: '10th', imageTab: '10th Memo' },
            { label: 'Diploma Details', value: 'Diploma', imageTab: 'Diploma Certificate' },
            { label: 'ECET Details', value: 'ECET', imageTab: 'ECET Rank Card' },
        ]
        : [
            { label: '10th Details', value: '10th', imageTab: '10th Memo' },
            { label: '12th Details', value: '12th', imageTab: '12th Memo' },
            { label: 'JEE Mains', value: 'JEE', imageTab: 'JEE Rank Card' },
                        { label: 'EAPCET', value: 'EAPCET', imageTab: 'EAPCET Rank Card' },
                    ];

        // Helper to get image tab for current academic section
        const getAcademicImageTab = (sectionValue) => {
                const found = academicSections.find(s => s.value === sectionValue);
                return found ? found.imageTab : academicSections[0].imageTab;
        };

    // When the right-side tab changes, update the left-side image tab accordingly
    React.useEffect(() => {
        if (activeTab === 'Academic Information') {
            setActiveImageTab(getAcademicImageTab(activeAcademicSection));
        } else {
            const mappedImageTab = tabToImageTab[activeTab];
            if (mappedImageTab && mappedImageTab !== activeImageTab) {
                setActiveImageTab(mappedImageTab);
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, isLE, activeAcademicSection]);
    const [isSaving, setIsSaving] = useState(false); // Add this state
    const [imageLoading, setImageLoading] = useState(false);
    const [imageError, setImageError] = useState(false);
    const [documentObjectUrl, setDocumentObjectUrl] = useState(null);
    const [zoomLevel, setZoomLevel] = useState(1); // Add zoom state
    const [rotationAngle, setRotationAngle] = useState(0); // Add rotation state
    const [comparisonResults, setComparisonResults] = useState([]);
    const [engineStatus, setEngineStatus] = useState("");
    const [engineRunning, setEngineRunning] = useState(false);
    const enginePollRef = React.useRef(null);

    // Use custom hook to disable browser zoom when modal is open
    useDisableBrowserZoom(isOpen);

    // Update `editedStudent` whenever the `student` prop changes
    React.useEffect(() => {
        setEditedStudent(student || {});
        setImageError(false);
        setImageLoading(true); // Set loading to true when student changes
        setZoomLevel(1); // Reset zoom when student changes
        setRotationAngle(0); // Reset rotation when student changes
    }, [student]);

    const fetchComparisonResults = React.useCallback(async () => {
        const studentId = student?.aadhaar_card_number;
        if (!studentId || !isOpen) return;
        try {
            const { data } = await API.get(`/students/${studentId}/comparison-results`);
            setComparisonResults(data.comparison_results || []);
        } catch {
            setComparisonResults([]);
        }
    }, [student?.aadhaar_card_number, isOpen]);

    React.useEffect(() => {
        fetchComparisonResults();
    }, [fetchComparisonResults]);

    const validateStudentId = (id) => {
        if (!id) return true; // Allow empty/null
        if (id.length !== 10) return false;
        const first5 = id.substring(0, 5);
        const rest = id.substring(5);
        return /^\d{5}$/.test(first5) && /^[a-zA-Z0-9]+$/.test(rest);
    };


    // Helper to calculate percentage (no negatives allowed)
    const calculatePercentage = (total, max) => {
        if (
            !total || !max ||
            isNaN(total) || isNaN(max) ||
            Number(max) <= 0 || Number(total) < 0 || Number(max) < 0
        ) return '';
        return ((Number(total) / Number(max)) * 100).toFixed(2);
    };

    // Always recalculate percentage when marks fields change
    React.useEffect(() => {
        setEditedStudent(prev => {
            const tenth_percentage = calculatePercentage(prev.tenth_total_marks_cgpa, prev.tenth_maximum_marks);
            const twelfth_percentage = calculatePercentage(prev.twelfth_total_marks, prev.twelfth_maximum_marks);
            // Only update if changed, to avoid unnecessary rerenders
            if (prev.tenth_percentage !== tenth_percentage || prev.twelfth_percentage !== twelfth_percentage) {
                return {
                    ...prev,
                    tenth_percentage,
                    twelfth_percentage
                };
            }
            return prev;
        });
    }, [editedStudent.tenth_total_marks_cgpa, editedStudent.tenth_maximum_marks, editedStudent.twelfth_total_marks, editedStudent.twelfth_maximum_marks]);

    // Prevent negative numbers for marks fields
    const handleInputChange = (field, value) => {
        // List of marks fields that should not allow negatives
        const marksFields = [
            'tenth_maximum_marks', 'tenth_total_marks_cgpa',
            'twelfth_maximum_marks', 'twelfth_total_marks',
        ];
        let newValue = value;
        if (marksFields.includes(field)) {
            // Remove negative sign if present
            if (String(newValue).startsWith('-')) newValue = String(newValue).replace(/^-+/, '');
            // Remove any non-digit except dot
            newValue = newValue.replace(/[^\d.]/g, '');
        }
        setEditedStudent((prev) => ({
            ...prev,
            [field]: newValue,
        }));
    };

    const handleSave = async () => {
      if (!validateStudentId(editedStudent.ht_no)) {
              setEngineStatus('Student ID must be empty or 10 characters long with first 5 digits and remaining alphanumeric');
              return;
          }
        try {
            setIsSaving(true);
            editedStudent.status = 'approved';
            await onSave(editedStudent);
            setIsEditing(false);
        } catch (error) {
            setEngineStatus(error.message || 'Failed to save changes. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleDraft = async () => {

          if (!validateStudentId(editedStudent.ht_no)) {
              setEngineStatus('Student ID must be empty or 10 characters long with first 5 digits and remaining alphanumeric');
              return;
          }

        try {
            setIsSaving(true);
            editedStudent.status = 'under_review';
            editedStudent.Time_updated = new Date().toISOString(); // Mark as draft
            await onSave(editedStudent);
            setIsEditing(false);
        } catch (error) {
            setEngineStatus(error.message || 'Failed to save draft. Please try again.');
        } finally {
            setIsSaving(false);
        }
    };

    // Cleanup polling on unmount
    React.useEffect(() => {
        return () => {
            if (enginePollRef.current) clearInterval(enginePollRef.current);
        };
    }, []);

    const pollTaskUntilDone = React.useCallback((taskId) => {
        if (enginePollRef.current) clearInterval(enginePollRef.current);
        setEngineRunning(true);
        enginePollRef.current = setInterval(async () => {
            try {
                const { data } = await API.get(`/task-status/${taskId}`);
                const taskRow = Array.isArray(data) ? data[0] : data;
                const taskStatus = taskRow?.status || 'unknown';
                if (taskStatus === 'completed') {
                    clearInterval(enginePollRef.current);
                    enginePollRef.current = null;
                    setEngineRunning(false);
                    setEngineStatus('Extraction complete. Results refreshed.');
                    await fetchComparisonResults();
                } else if (taskStatus === 'failed') {
                    clearInterval(enginePollRef.current);
                    enginePollRef.current = null;
                    setEngineRunning(false);
                    setEngineStatus(`Extraction failed: ${taskRow?.error || 'Unknown error'}`);
                } else {
                    const pct = taskRow?.progress ?? '';
                    setEngineStatus(`Extracting from documents… ${pct ? pct + '%' : ''}`);
                }
            } catch {
                // keep polling
            }
        }, 3000);
    }, [fetchComparisonResults]);

    const handleRunEngines = async () => {
        const studentId = editedStudent?.aadhaar_card_number;
        if (!studentId) return;
        try {
            setEngineStatus('Queuing extraction engine…');
            setEngineRunning(true);
            const { data } = await API.post(`/students/${studentId}/engine-runs`, { force: true });
            const taskId = data.task_id;
            setEngineStatus(`Engine queued (task ${taskId}). Extracting…`);
            pollTaskUntilDone(taskId);
        } catch (error) {
            setEngineRunning(false);
            setEngineStatus(error.response?.data?.detail || error.message || 'Failed to start engine run');
        }
    };

    const handleOverrideComparison = async (fieldName, currentValue) => {
        const studentId = editedStudent?.aadhaar_card_number;
        if (!studentId) return;
        try {
            await API.patch(`/students/${studentId}/comparison-results/${fieldName}`, {
                field_name: fieldName,
                reviewer_override: !currentValue,
                reviewer_notes: !currentValue ? "Reviewer accepted this mismatch." : "",
            });
            await fetchComparisonResults();
        } catch (error) {
            setEngineStatus(error.response?.data?.detail || error.message || "Failed to update comparison");
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

    // Handle rotation functionality
    const handleRotate = () => {
        setRotationAngle(prev => (prev + 90) % 360);
    };

    const getImageSource = () => {
        let imageField = '';
        let docType = '';
        switch (activeImageTab) {
            case 'Aadhaar Card':
                imageField = 'aadhaar_link';
                docType = 'aadhaar';
                break;
            case 'Transfer Certificate':
                imageField = 'transfer_certificate_link';
                docType = 'transfer_certificate';
                break;
            case '10th Memo':
                imageField = 'tenth_memo_link';
                docType = 'tenth_memo';
                break;
            case '12th Memo':
                imageField = 'twelfth_memo_link';
                docType = 'twelfth_memo';
                break;
            case 'JEE Rank Card':
                imageField = 'jee_rank_card_link';
                docType = 'jee_rank_card';
                break;
            case 'EAPCET Rank Card':
                imageField = 'eapcet_rank_card_link';
                docType = 'eapcet_rank_card';
                break;
            case 'Diploma Certificate':
                imageField = 'twelfth_memo_link'; // Assuming diploma is same as 12th memo
                docType = 'twelfth_memo';
                break;
            case 'ECET Rank Card':
                imageField = 'eapcet_rank_card_link';
                docType = 'eapcet_rank_card';
                break;
            default:
                imageField = 'aadhaar_link';
                docType = 'aadhaar';
                break;
        }

        const studentId = editedStudent?.aadhaar_card_number;
        if (studentId && docType) {
            return getStudentDocumentUrl(studentId, docType);
        }

        if (editedStudent[imageField]) {
            // Legacy fallback to existing image endpoint when student id is unavailable
            const linkstr = editedStudent[imageField];
            const match = linkstr.match(/id=([a-zA-Z0-9_-]+)/);
            const fileId = match ? match[1] : null;
            return getImageUrl(fileId);
        }
        return null;
    };

    const imageSource = React.useMemo(
        () => getImageSource(),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [activeImageTab, editedStudent?.aadhaar_card_number, editedStudent?.aadhaar_link, editedStudent?.transfer_certificate_link, editedStudent?.tenth_memo_link, editedStudent?.twelfth_memo_link, editedStudent?.jee_rank_card_link, editedStudent?.eapcet_rank_card_link]
    );

    React.useEffect(() => {
        let objectUrl = null;
        let cancelled = false;

        if (!isOpen || !imageSource) {
            setDocumentObjectUrl(null);
            setImageLoading(false);
            return undefined;
        }

        setImageLoading(true);
        setImageError(false);
        API.get(imageSource, { responseType: 'blob' })
            .then((response) => {
                if (cancelled) return;
                objectUrl = URL.createObjectURL(response.data);
                setDocumentObjectUrl(objectUrl);
            })
            .catch(() => {
                if (cancelled) return;
                setDocumentObjectUrl(null);
                setImageLoading(false);
                setImageError(true);
            });

        return () => {
            cancelled = true;
            if (objectUrl) URL.revokeObjectURL(objectUrl);
        };
    }, [imageSource, isOpen]);

    // Update image loading state whtime_updaen image tab changes
    React.useEffect(() => {
        setImageError(false);
        setImageLoading(true);
        setZoomLevel(1); // Reset zoom when image tab changes
    }, [activeImageTab]);

    // Helper function to format date as DD/MM/YYYY
    function formatDateDMY(dateString) {
      if (!dateString) return '';
      // If already in DD/MM/YYYY or DD-MM-YYYY, return as is
      if (/^\d{2}[/-]\d{2}[/-]\d{4}$/.test(dateString)) {
        return dateString.replace(/-/g, '/'); // convert DD-MM-YYYY to DD/MM/YYYY
      }
      // Try to parse ISO or US format
      const date = new Date(dateString);
      if (isNaN(date)) return dateString; // fallback if invalid
      const day = String(date.getDate()).padStart(2, '0');
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const year = date.getFullYear();
      return `${day}/${month}/${year}`;
    }

    const renderField = (label, field, type = 'text', readOnly = false, options = null) => {
    const isDOB = field === 'date_of_birth';
    const isMarksField = [
        'tenth_maximum_marks', 'tenth_total_marks_cgpa',
        'twelfth_maximum_marks', 'twelfth_total_marks'
    ].includes(field);
    const isDropdown = options && isEditing && !readOnly;
    
    return (
        <div className="mb-4 relative">
            <label className={`block text-sm font-medium text-gray-700`}>{label}:</label>
            {isDropdown ? (
                <select
                    value={editedStudent[field] || ''}
                    onChange={(e) => handleInputChange(field, e.target.value)}
                    className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm ${
                        isDarkMode
                            ? 'bg-gray-700 border-gray-600 text-white'
                            : 'bg-white border-gray-300 text-gray-900'
                    }`}
                >
                    {!editedStudent[field] && <option value="">Select {label}</option>}
                    {options.map((option) => (
                        <option key={option.value} value={option.value}>
                            {option.label}
                        </option>
                    ))}
                    {/* Add current value as option if it doesn't exist in the list */}
                    {editedStudent[field] && !options.find(opt => opt.value === editedStudent[field]) && (
                        <option value={editedStudent[field]}>
                            {editedStudent[field]} (Current)
                        </option>
                    )}
                </select>
            ) : (
                <input
                    type={type}
                    value={isDOB ? formatDateDMY(editedStudent[field]) : (editedStudent[field] || '')}
                    onChange={(e) => handleInputChange(field, e.target.value)}
                    readOnly={!isEditing || readOnly}
                    min={isMarksField && type === 'number' ? 0 : undefined}
                    className={`mt-1 block w-full px-3 py-2 border rounded-md shadow-sm ${
                        isDarkMode
                            ? 'bg-gray-700 border-gray-600 text-white'
                            : 'bg-white border-gray-300 text-gray-900'
                    } ${!isEditing || readOnly ? 'bg-opacity-50' : ''}`}
                />
            )}
            {/* Calendar Picker for DOB in Edit Mode */}
            {isDOB && isEditing && !readOnly && !isDropdown && (
                <div className="absolute top-[33px] right-2">
                    <input
                        type="date"
                        value={(() => {
                            const d = new Date(editedStudent[field]);
                            return isNaN(d) ? '' : d.toISOString().split('T')[0];
                        })()}
                        onChange={(e) => {
                            const isoDate = e.target.value; // yyyy-mm-dd
                            const [year, month, day] = isoDate.split('-');
                            const formatted = `${day}/${month}/${year}`;
                            handleInputChange(field, formatted);
                        }}
                        className="opacity-0 absolute inset-0 w-full h-full cursor-pointer"
                    />
                    <svg
                        className="w-5 h-5 text-gray-500 pointer-events-none"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 
                            00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                    </svg>
                </div>
            )}
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
        'Comparison',
    ];

    // Image tabs
    const imageTabs = React.useMemo(() =>{
        if (isLE) {
            return [
                'Aadhaar Card',
                'Transfer Certificate',
                '10th Memo',
                'Diploma Certificate',
                'ECET Rank Card',
            ];
        }
        return [
            'Aadhaar Card', 
            'Transfer Certificate',
            '10th Memo',
            '12th Memo',
            'JEE Rank Card',
            'EAPCET Rank Card',
        ];
    }, [isLE]);

    if (!isOpen) return null;

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
                            {renderField('Branch Code', 'branch', 'text', false, branchCodes)}
                            {renderField('Admission Category', 'admission_category')}
                        </div>
                        {/* Academic sub-section selector */}
                        <div className="flex space-x-2 mb-2">
                            {academicSections.map(section => (
                                <button
                                    key={section.value}
                                    className={`px-3 py-1 rounded ${activeAcademicSection === section.value ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700'}`}
                                    onClick={() => setActiveAcademicSection(section.value)}
                                >
                                    {section.label}
                                </button>
                            ))}
                        </div>
                        {/* Render academic section details */}
                        {activeAcademicSection === '10th' && (
                            <div>
                                <h5 className="font-medium mb-4">10th Details</h5>
                                {renderField('Board Name', 'tenth_board_name')}
                                {renderField('School Name', 'tenth_school_name')}
                                {renderField('Hall Ticket No', 'tenth_ht_no')}
                                {renderField('Max Marks', 'tenth_maximum_marks', 'number', false)}
                                {renderField('Total Marks', 'tenth_total_marks_cgpa', 'number', false)}
                                {renderField('Percentage', 'tenth_percentage', 'text', true)}
                                {renderField('Month & Year', 'tenth_month_year')}
                            </div>
                        )}
                        {activeAcademicSection === '12th' && !isLE && (
                            <div>
                                <h5 className="font-medium mb-4">12th Details</h5>
                                {renderField('Board Name', 'twelfth_board_name')}
                                {renderField('College Name', 'twelfth_college_name')}
                                {renderField('Hall Ticket No', 'twelfth_ht_no')}
                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div>{renderField('M1', 'm1')}</div>
                                    <div>{renderField('M2', 'm2')}</div>
                                    <div>{renderField('M3', 'm3')}</div>
                                    <div>{renderField('M4', 'm4')}</div>
                                    <div>{renderField('P1', 'p1')}</div>
                                    <div>{renderField('P2', 'p2')}</div>
                                    <div>{renderField('C1', 'ch1')}</div>
                                    <div>{renderField('C2', 'ch2')}</div>
                                    <div>{renderField('CLAB', 'chlab')}</div>
                                    <div>{renderField('PLAB', 'plab')}</div>
                                </div>
                                {renderField('Max Marks', 'twelfth_maximum_marks', 'number', false)}
                                {renderField('Total Marks', 'twelfth_total_marks', 'number', false)}
                                {renderField('Percentage', 'twelfth_percentage', 'text', true)}
                                {renderField('Month & Year', 'twelfth_month_year')}
                            </div>
                        )}
                        {activeAcademicSection === 'Diploma' && isLE && (
                            <div>
                                <h5 className="font-medium mb-4">Diploma Details</h5>
                                {renderField('Board Name', 'twelfth_board_name')}
                                {renderField('College Name', 'twelfth_college_name')}
                                {renderField('Hall Ticket No', 'twelfth_ht_no')}
                                {renderField('Max Marks', 'twelfth_maximum_marks', 'number', false)}
                                {renderField('Total Marks', 'twelfth_total_marks', 'number', false)}
                                {renderField('Percentage', 'twelfth_percentage', 'text', true)}
                                {renderField('Month & Year', 'twelfth_month_year')}
                            </div>
                        )}
                        {activeAcademicSection === 'ECET' && isLE && (
                            <div>
                                <h5 className="font-medium mb-4">ECET Details</h5>
                                {renderField('ECET Hall Ticket No', 'eapcet_ht_no')}
                                {renderField('ECET Rank', 'eapcet_rank')}
                            </div>
                        )}
                        {activeAcademicSection === 'JEE' && !isLE && (
                            <div>
                                <h5 className="font-medium mb-4">JEE Mains</h5>
                                {renderField('JEE Roll No', 'jee_roll_no')}
                                {renderField('JEE Rank', 'jee_rank')}
                            </div>
                        )}
                        {activeAcademicSection === 'EAPCET' && !isLE && (
                            <div>
                                <h5 className="font-medium mb-4">EAPCET Details</h5>
                                {renderField('EAPCET Hall Ticket No', 'eapcet_ht_no')}
                                {renderField('EAPCET Rank', 'eapcet_rank')}
                            </div>
                        )}
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
                        {renderField('Door Number', 'address_dno')}
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
            case 'Comparison': {
                const mismatches = comparisonResults.filter((row) => row.match_status !== 'match' && !row.reviewer_override);
                return (
                    <div className="space-y-4">
                        <div className="rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-3">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <p className="text-sm font-semibold text-gray-800 dark:text-white">Document Extraction</p>
                                    <p className="text-xs text-gray-600 dark:text-gray-400">
                                        {comparisonResults.length
                                            ? `${mismatches.length} field${mismatches.length !== 1 ? 's' : ''} need attention out of ${comparisonResults.length} checked.`
                                            : 'No extraction results yet. Click "Run Extraction" to extract data from uploaded documents.'}
                                    </p>
                                </div>
                                <div className="flex gap-2">
                                    {comparisonResults.length > 0 && (
                                        <button
                                            onClick={fetchComparisonResults}
                                            disabled={engineRunning}
                                            className="rounded-md border border-gray-300 dark:border-gray-600 px-3 py-2 text-xs font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50"
                                        >
                                            ↻ Refresh
                                        </button>
                                    )}
                                    <button
                                        onClick={handleRunEngines}
                                        disabled={engineRunning}
                                        className="rounded-md bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60 flex items-center gap-1"
                                    >
                                        {engineRunning ? (
                                            <><svg className="animate-spin h-3 w-3" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg> Extracting…</>
                                        ) : 'Run Extraction'}
                                    </button>
                                </div>
                            </div>
                            {engineStatus && (
                                <p className={`mt-2 text-xs ${engineRunning ? 'text-blue-600 dark:text-blue-400' : engineStatus.includes('failed') || engineStatus.includes('Failed') ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                                    {engineStatus}
                                </p>
                            )}
                        </div>
                        <div className="space-y-2">
                            {comparisonResults.map((row) => {
                                const isMismatch = row.match_status !== 'match' && !row.reviewer_override;
                                return (
                                    <div
                                        key={`${row.field_name}-${row.id}`}
                                        className={`rounded-md border p-3 text-sm ${
                                            isMismatch
                                                ? row.severity === 'high'
                                                    ? 'border-red-200 bg-red-50'
                                                    : 'border-amber-200 bg-amber-50'
                                                : 'border-green-100 bg-green-50'
                                        }`}
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="font-semibold text-gray-800">{row.field_name?.replace(/_/g, ' ')}</span>
                                            <span className="rounded-full bg-white px-2 py-0.5 text-xs uppercase text-gray-600">
                                                {row.reviewer_override ? 'override' : row.match_status}
                                            </span>
                                        </div>
                                        <div className="mt-2 grid gap-2">
                                            <div>
                                                <span className="text-xs text-gray-500">Filled</span>
                                                <p className="break-words text-gray-800">{row.filled_value || '-'}</p>
                                            </div>
                                            <div>
                                                <span className="text-xs text-gray-500">Extracted</span>
                                                <p className="break-words text-gray-800">{row.extracted_value || '-'}</p>
                                            </div>
                                        </div>
                                        {row.match_status === 'mismatch' && (
                                            <button
                                                onClick={() => handleOverrideComparison(row.field_name, row.reviewer_override)}
                                                className="mt-2 rounded-md border border-gray-300 px-2 py-1 text-xs text-gray-700"
                                            >
                                                {row.reviewer_override ? 'Remove Override' : 'Accept Mismatch'}
                                            </button>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                );
            }
            default:
                return null;
        }
    };

    // Prefer DOM-measured header/footer if available for perfect alignment
    const headerEl = typeof document !== 'undefined' ? document.getElementById('app-header') : null;
    const footerEl = typeof document !== 'undefined' ? document.getElementById('app-footer') : null;
    const headerPx = headerEl?.offsetHeight ?? 0;
    const footerPx = footerEl?.offsetHeight ?? 0;
    const safeAreaStyle = headerPx && footerPx
        ? { top: headerPx + 1, bottom: footerPx + 2, left: 0, right: 0 }
        : { top: `${headerHeightVh}vh`, bottom: `${footerHeightVh}vh`, left: 0, right: 0 };
    const modalMaxHeight = headerPx && footerPx
        ? `calc(100vh - ${headerPx + footerPx + 4}px)`
        : `calc(100vh - ${headerHeightVh + footerHeightVh}vh - 4px)`;

    return isOpen ? (
        <div className="fixed z-[150] flex items-start justify-center pt-1 md:pt-2 pb-2 px-4 md:px-6" style={safeAreaStyle}>
            {/* Blurry Backdrop */}
            <div
                className="fixed z-[140] bg-black bg-opacity-50 backdrop-blur-sm transition-opacity"
                style={safeAreaStyle}
                onClick={onClose}
            />
            
            {/* Modal */}
            <div
                className="relative z-[150] bg-white rounded-lg shadow-lg max-w-6xl w-full h-full flex flex-col overflow-hidden"
                style={{ maxHeight: modalMaxHeight }}
            >
                {/* Top Action Bar */}
                <div className="w-full bg-white rounded-lg border border-gray-200 dark:border-gray-700 p-1 md:p-2 flex justify-between space-x-2">
                    <h3
                        className={`text-lg md:text-xl font-medium `}
                    >
                        Student Details - {editedStudent.student_name}
                    </h3>
                    <div className="flex items-center space-x-2">
                        {!isEditing && (
                            <button
                                onClick={() => setIsEditing(true)}
                                className={`p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-white`}
                            >
                                <FiEdit2 />
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
                                    ) : <span className={isDarkMode ? 'text-green-300' : 'text-green-600'}>Mark as Approved</span>}
                                </button>
                                <button
                                    onClick={handleDraft}
                                    disabled={isSaving}
                                    className="p-2 rounded-full hover:bg-yellow-100 dark:hover:bg-yellow-700"
                                    title="Move to Under Review"
                                >
                                    <span className={isDarkMode ? 'text-yellow-300' : 'text-yellow-600'}>Mark as Under Review</span>
                                </button>
                            </>
                        )}
                        <button
                            onClick={onClose}
                            className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 dark:hover:text-white"
                        >
                            <IoClose size={20} />
                        </button>
                    </div>
                </div>

                <div className="flex flex-row h-full min-h-0">
                    {/* Left: Image Tabs and Image Display */}
                    <div className="w-2/3 p-2 md:p-3 flex flex-col min-h-0" style={{ maxHeight: '100%' }}>
                        {/* Image Tabs */}
                        <div className="mb-2">
                            <ScrollableTabs tabs={imageTabs} activeTab={activeImageTab} setActiveTab={setActiveImageTab} />
                        </div>
                        
                        {/* Image Display with Zoom */}
                        <div 
                            className="flex-1 border rounded-lg p-2 md:p-3 relative overflow-hidden min-h-0" 
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
                                    onClick={handleRotate}
                                    className="p-1 rounded hover:bg-gray-200 text-gray-600"
                                    title="Rotate 90°"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
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
                                {imageSource ? (
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
                                        ) : documentObjectUrl ? (
                                            <div className="flex justify-center items-center min-h-full p-4">
                                                <img
                                                    src={documentObjectUrl || ""}
                                                    alt={`${activeImageTab} Document`}
                                                    className="object-contain rounded-lg shadow-lg transition-transform duration-200"
                                                    style={{ 
                                                        transform: `scale(${zoomLevel}) rotate(${rotationAngle}deg)`,
                                                        maxWidth: '100%',
                                                        maxHeight: '100%',
                                                        display: imageLoading ? 'none' : 'block'
                                                    }}
                                                    onLoad={handleImageLoad}
                                                    onError={handleImageError}
                                                />
                                            </div>
                                        ) : null}
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
                    <div className="w-1/3 p-2 md:p-3 flex flex-col border-l min-h-0" style={{ maxHeight: '100%' }}>
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
