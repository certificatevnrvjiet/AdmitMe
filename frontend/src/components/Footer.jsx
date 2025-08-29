import React from 'react'
import { useTheme } from '../context/ThemeContext';

function Footer() {
  const { isDarkMode } = useTheme();
  
  return (
    <div
  id="app-footer" className={`bottom-0 w-full pt-2 pb-2 shadow-md fixed z-50 px-4 ${
    isDarkMode ? 'bg-gray-800 text-gray-300' : 'bg-blue-100 text-gray-700'
  }`}
>
  <div className="flex overflow-x-auto gap-6 md:justify-between text-sm max-w-6xl mx-auto">
    {/* Project By */}
    <div className="min-w-[200px] flex-shrink-0 whitespace-normal">
      <h5 className={`font-semibold mb-1 ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>Project by:</h5>
      <div className="grid grid-cols-2 gap-x-4 text-sm">
        <ul className='p-0 space-y-0.5'>
          <li>L. Goutham (23071A0530)</li>
          <li>G. Charmi Bai (23071A0516)</li>
        </ul>
        <ul className='p-0 space-y-0.5'>
          <li>M. Akhila (23071A0531)</li>
          <li>D. L. Sarvani (23071A0512)</li>
        </ul>
      </div>  
    </div>

    {/* Project Guided by */}
    <div className="min-w-[250px] flex-shrink-0 whitespace-normal">
      <h5 className={`font-medium mb-1 ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>Project Guided by:</h5>
      <ul className='p-0 space-y-0.5'>
        <li>Mr. P. Sudheer Benarji, Assistant Professor [CSE, VNRVJIET]</li>
        <li>Dr. B.V. Kiranmayee, Professor [CSE, VNRVJIET]</li>
      </ul>
    </div>

    {/* HOD */}
    <div className="min-w-[200px] flex-shrink-0 whitespace-normal">
      <h5 className={`font-medium mb-1 ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>HOD</h5>
      <ul className='p-0 space-y-0.5'>
        <li>Dr. V. Baby [CSE, VNRVJIET]</li>
      </ul>
    </div>

    {/* Principal */}
    <div className="min-w-[150px] flex-shrink-0 whitespace-normal">
      <h5 className={`font-medium mb-1 ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>Principal</h5>
      <ul className='p-0 space-y-0.5'>
        <li>Dr. C.D. Naidu</li>
      </ul>
    </div>
  </div>
</div>

  );
}

export default Footer;
