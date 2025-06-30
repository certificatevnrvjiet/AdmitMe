import React from 'react'
import { useTheme } from '../context/ThemeContext';

function Footer() {
  const { isDarkMode } = useTheme();
  
  return (
    <div className={`bottom-0 w-full pt-0 shadow-md flex justify-between mt-5 px-8 fixed z-100 pb-0 ${
      isDarkMode ? 'bg-gray-800 text-gray-300' : 'bg-blue-100 text-gray-700'
    }`}>
      <div>
        <h5 className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>Project by:</h5>
        <div className='flex'>
        <ul className='pr-10'>
            <li>L. Goutham (23071A0530)</li>
            <li>G. Charmi Bai (23071A0516)</li>
        </ul>
        <ul>
            <li>M. Akhila (23071A0531)</li>
            <li>D. L. Sarvani (23071A0512)</li>
        </ul>
        </div>
      </div>  
      <div>
        <h5 className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>Project Guided by: </h5>
        <ul className='p-0'>
            
            <li>Mr. P. Sudheer Benarji, Assistant Professor [CSE, VNRVJIET]</li>
            <li>Dr. B.V. Kiranmayee, Professor [CSE, VNRVJIET]</li>
            
        </ul>
      </div>
      <div>
        <h5 className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>HOD</h5>
        <ul className='p-0'>
            <li>Dr. V. Baby [CSE, VNRVJIET]</li>
        </ul>
      </div>
      <div>
        <h5 className={`font-medium ${isDarkMode ? 'text-gray-200' : 'text-gray-900'}`}>Principal</h5>
        <ul className='p-0'>
            <li>Dr.C.D.Naidu</li>
        </ul>
      </div>
    </div>
  )
}

export default Footer