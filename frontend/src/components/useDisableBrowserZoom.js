import { useEffect } from 'react';

// Custom hook to disable browser zoom when enabled=true
export default function useDisableBrowserZoom(enabled) {
  useEffect(() => {
    if (!enabled) return;
    const wheelListener = (e) => {
      if (e.ctrlKey) {
        e.preventDefault();
      }
    };
    const keyListener = (e) => {
      if (e.ctrlKey && (e.key === '+' || e.key === '-' || e.key === '=' || e.key === '0')) {
        e.preventDefault();
      }
    };
    const touchListener = (e) => {
      if (e.touches && e.touches.length > 1) {
        e.preventDefault();
      }
    };
    window.addEventListener('wheel', wheelListener, { passive: false });
    window.addEventListener('keydown', keyListener, { passive: false });
    window.addEventListener('touchmove', touchListener, { passive: false });
    return () => {
      window.removeEventListener('wheel', wheelListener, { passive: false });
      window.removeEventListener('keydown', keyListener, { passive: false });
      window.removeEventListener('touchmove', touchListener, { passive: false });
    };
  }, [enabled]);
}
