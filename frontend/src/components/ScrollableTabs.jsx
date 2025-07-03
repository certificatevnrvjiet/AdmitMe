import { useEffect, useRef } from 'react';


function ScrollableTabs({ tabs, activeTab, setActiveTab }) {
  const scrollContainerRef = useRef(null);
  const scrollPosition = useRef(0);

  // Handle horizontal scrolling with vertical mouse wheel
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;

    const onWheel = (e) => {
      if (e.deltaY !== 0) {
        e.preventDefault();
        el.scrollLeft += e.deltaY;
      }
    };

    el.addEventListener('wheel', onWheel, { passive: false });

    return () => {
      el.removeEventListener('wheel', onWheel);
    };
  }, []);

  // Restore scroll position after tab change
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (el) {
      el.scrollLeft = scrollPosition.current;
    }
  }, []);

  // Preserve scroll position before tab change
  const handleTabClick = (tabLabel) => {
    const el = scrollContainerRef.current;
    if (el) {
      scrollPosition.current = el.scrollLeft;
    }
    setActiveTab(tabLabel);
  };

  return (
    <div
      ref={scrollContainerRef}
      className="flex space-x-4 overflow-x-auto pb-2"
      style={{
        maxHeight: '100px',
        scrollbarWidth: 'none',      // Firefox
        msOverflowStyle: 'none',     // IE/Edge
      }}
    >
      {tabs.map((tabLabel) => (
        <button
          key={tabLabel}
          onClick={() => handleTabClick(tabLabel)}
          className={`px-4 py-2 whitespace-nowrap rounded-md ${
            activeTab === tabLabel
              ? 'bg-indigo-500 text-white'
              : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200'
          }`}
        >
          {tabLabel}
        </button>
      ))}
    </div>
  );
}


export default ScrollableTabs;