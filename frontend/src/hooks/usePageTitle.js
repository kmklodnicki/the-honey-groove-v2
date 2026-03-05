import { useEffect } from 'react';

const BASE_TITLE = 'the Honey Groove';

export const usePageTitle = (subtitle) => {
  useEffect(() => {
    document.title = subtitle ? `${BASE_TITLE} · ${subtitle}` : BASE_TITLE;
    return () => { document.title = BASE_TITLE; };
  }, [subtitle]);
};
