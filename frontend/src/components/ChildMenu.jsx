import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
import { ChevronDownIcon } from '@heroicons/react/20/solid';
import React, { useState } from 'react';

export default function ChildMenu({ onSelect, Name, l }) {

  const [selectedItem, setSelectedItem] = useState(0);

  const handleItemClick=(item)=>{
    setSelectedItem(item);
    // console.log(item)
    onSelect(item);
  }
  // Function to handle item click and send the selected item to the parent

  return (
    <Menu as="div" className="relative inline-block mx-3 text-left basis-1/3">
      <div>
        <MenuButton className="inline-flex w-full pr-3 justify-center rounded-md bg-white text-sm font-semibold text-gray-900 hover:bg-gray-50">
          
          <ChevronDownIcon aria-hidden="true" className="-mr-1 size-5 text-gray-400" />
        </MenuButton>
      </div>

      <MenuItems
        transition
        className="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-white ring-1 shadow-lg ring-black/5 transition focus:outline-hidden data-closed:scale-95 data-closed:transform data-closed:opacity-0 data-enter:duration-100 data-enter:ease-out data-leave:duration-75 data-leave:ease-in"
        >
        <div className="py-1">
          {
            l.map(item=><MenuItem key={item}>
              <a
                href="#"
                className="block px-4 py-2 text-sm text-gray-700 data-focus:bg-gray-100 data-focus:text-gray-900 data-focus:outline-hidden"
              
                onClick={() => {handleItemClick(item)}}
              >
                {item}
              </a>
            </MenuItem>)
          }
        </div>
      </MenuItems>
    </Menu>
  );
}