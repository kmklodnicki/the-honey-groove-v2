const GA_ID = process.env.REACT_APP_GA_MEASUREMENT_ID;

// Load gtag.js dynamically
if (GA_ID && typeof window !== 'undefined' && !document.querySelector(`script[src*="googletagmanager"]`)) {
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_ID}`;
  document.head.appendChild(script);

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', GA_ID);
}

export const trackEvent = (eventName, params = {}) => {
  if (typeof window.gtag === 'function') {
    window.gtag('event', eventName, params);
  }
};
