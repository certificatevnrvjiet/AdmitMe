import React from 'react';
import { IoDownload } from "react-icons/io5";
import { FaGoogleDrive } from 'react-icons/fa';

const QuickActions = ({
    userRole,
    syncLoading,
    handleSyncStudents,
    syncStatus,
    downloadLoading,
    handleDownloadExcel,
    SavingtoDrive,
    handleSavetoDrive,
    isDarkMode
}) => {
    return (
        <div className={`overflow-hidden shadow-sm rounded-lg ${isDarkMode ? 'bg-gray-700' : 'bg-white'}`}>
            <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-medium text-indigo-400">Quick Actions</h3>
                </div>
                <div className="space-y-4">
                    {userRole !== 'admin' &&
                        <button
                            className={`w-full px-4 py-2 rounded-md ${isDarkMode ? 'bg-indigo-600 text-white' : 'bg-indigo-500 text-white'} ${syncLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                            onClick={handleSyncStudents}
                            disabled={syncLoading}
                        >
                            {syncLoading ? 'Syncing...' : 'Extract and Fill 71 fields'}
                        </button>
                    }
                    {syncStatus && (
                        <div className="text-sm mt-2 text-indigo-400">{syncStatus}</div>
                    )}
                    <button
                        className={`w-full px-4 py-2 rounded-md flex items-center justify-center space-x-2 ${isDarkMode ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-green-500 text-white hover:bg-green-600'} ${downloadLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={handleDownloadExcel}
                        disabled={downloadLoading}
                    >
                        <IoDownload className="w-4 h-4" />
                        <span>{downloadLoading ? 'Downloading...' : 'Download Excel'}</span>
                    </button>
                    <button
                        className={`w-full px-4 py-2 rounded-md flex items-center justify-center space-x-2 ${isDarkMode ? 'bg-green-600 text-white hover:bg-green-700' : 'bg-green-500 text-white hover:bg-green-600'} ${SavingtoDrive ? 'opacity-50 cursor-not-allowed' : ''}`}
                        onClick={handleSavetoDrive}
                        disabled={SavingtoDrive}
                    >
                        <FaGoogleDrive className="text-white-600 text-xl" />
                        <span>{SavingtoDrive ? 'Saving...' : 'Save To Drive'}</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default QuickActions;
