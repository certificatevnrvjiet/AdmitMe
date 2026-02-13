import React from 'react';
import { IoSearchSharp } from "react-icons/io5";
import { RiArrowDropDownLine } from "react-icons/ri";

const FilterBar = ({
    searchTerm, setSearchTerm,
    statusFilter, setStatusFilter,
    admissionCategoryFilter, setAdmissionCategoryFilter,
    StudenttypeFilter, setStudentTypeFilter,
    TenthboardFilter, setTenthBoardFilter,
    TwelfthboardFilter, setTwelfthBoardFilter,
    branchFilter, setBranchFilter,
    GenderFilter, setGenderFilter,
    department,
    isDarkMode
}) => {

    // Helper to create select dropdowns
    const SelectFilter = ({ value, onChange, options, minWidth = "w-full md:w-auto" }) => (
        <div className={`relative ${minWidth}`}>
            <select
                onChange={onChange}
                value={value}
                className={`appearance-none w-full bg-transparent border ${isDarkMode
                    ? 'border-gray-600 text-white bg-gray-700'
                    : 'border-gray-300 text-gray-700 bg-white'
                    } rounded-md py-2 pl-4 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500`}
            >
                {options.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
            </select>
            <RiArrowDropDownLine
                className={`absolute right-2 top-1/2 transform -translate-y-1/2 pointer-events-none ${isDarkMode ? 'text-white' : 'text-gray-700'}`}
                size={20}
            />
        </div>
    );

    return (
        <div className={`mt-8 shadow-sm rounded-lg mb-10 ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
            <div className="p-6">
                <div className="mb-4">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
                        <h3 className="text-lg font-medium text-indigo-400 mb-4 md:mb-0">
                            Student Verification Activity
                        </h3>

                        {/* Search Bar - Aligned with heading */}
                        <div className="relative w-full md:w-96">
                            <input
                                type="text"
                                placeholder="Search by Student Name..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className={`w-full pl-6 pr-10 py-3 border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-lg ${isDarkMode
                                    ? 'bg-gray-600 border-gray-500 text-white placeholder-gray-400'
                                    : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'
                                    }`}
                            />
                            <IoSearchSharp className="absolute right-4 top-1/2 -translate-y-1/2 h-6 w-6 text-gray-400" />
                        </div>
                    </div>

                    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                        {/* Filter Controls Group */}
                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-4 w-full flex-wrap">

                            <SelectFilter
                                value={StudenttypeFilter}
                                onChange={(e) => setStudentTypeFilter(e.target.value)}
                                options={[
                                    { value: "regular", label: "Regular" },
                                    { value: "le", label: "LE" }
                                ]}
                            />

                            <SelectFilter
                                value={admissionCategoryFilter}
                                onChange={(e) => setAdmissionCategoryFilter(e.target.value)}
                                options={[
                                    { value: "all", label: "All Categories" },
                                    { value: "Management", label: "Management" }
                                ]}
                            />

                            <SelectFilter
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                options={[
                                    { value: "all", label: "All Status" },
                                    { value: "verified", label: "Verified" },
                                    { value: "pending", label: "Pending" },
                                    { value: "not viewed", label: "Not Viewed" }
                                ]}
                            />

                            <SelectFilter
                                value={TenthboardFilter}
                                onChange={(e) => setTenthBoardFilter(e.target.value)}
                                options={[
                                    { value: "all", label: "All Tenth Boards" },
                                    { value: "tg bse", label: "TG BSE" },
                                    { value: "cbse", label: "CBSE" },
                                    { value: "icse", label: "ICSE" },
                                    { value: "ap bse", label: "AP BSE" },
                                    { value: "idbp", label: "IDBP" },
                                    { value: "ace and a level", label: "ACE and A Level" },
                                    { value: "other", label: "Other" }
                                ]}
                            />

                            <SelectFilter
                                value={TwelfthboardFilter}
                                onChange={(e) => setTwelfthBoardFilter(e.target.value)}
                                options={[
                                    { value: "all", label: "All Twelfth Boards" },
                                    { value: "tg bie", label: "TG BIE" },
                                    { value: "cbse", label: "CBSE" },
                                    { value: "icse", label: "ICSE" },
                                    { value: "ap bie", label: "AP BIE" },
                                    { value: "idbp", label: "IDBP" },
                                    { value: "ace and a level", label: "ACE and A Level" },
                                    { value: "other", label: "Other" }
                                ]}
                            />

                            {/* Branch Filter - Only for Admin */}
                            {department === 'admin' && (
                                <SelectFilter
                                    value={branchFilter}
                                    onChange={(e) => setBranchFilter(e.target.value)}
                                    options={[
                                        { value: "all", label: "All Branches" },
                                        { value: "aids", label: "AIDS" },
                                        { value: "ae", label: "AE" },
                                        { value: "ce", label: "CE" },
                                        { value: "csbs", label: "CSBS" },
                                        { value: "cse", label: "CSE" },
                                        { value: "aml", label: "AML" },
                                        { value: "cseds", label: "CSE-DS" },
                                        { value: "csecys", label: "CSE-CYS" },
                                        { value: "cseiot", label: "CSE-IOT" },
                                        { value: "eee", label: "EEE" },
                                        { value: "ece", label: "ECE" },
                                        { value: "eie", label: "EIE" },
                                        { value: "it", label: "IT" },
                                        { value: "me", label: "ME" },
                                        { value: "vlsi", label: "VLSI" },
                                        { value: "biotechnology", label: "Biotechnology" },
                                        { value: "rai", label: "Robotics and AI" }
                                    ]}
                                />
                            )}

                            <SelectFilter
                                value={GenderFilter}
                                onChange={(e) => setGenderFilter(e.target.value)}
                                options={[
                                    { value: "all", label: "All Gender" },
                                    { value: "female", label: "Female" },
                                    { value: "male", label: "Male" }
                                ]}
                            />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FilterBar;
