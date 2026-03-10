import React, { createContext, useContext, useState, useCallback } from 'react';

const VariantModalContext = createContext();

export function VariantModalProvider({ children }) {
  const [modal, setModal] = useState(null); // { artist, album, variant, discogs_id }

  const openVariantModal = useCallback((data) => {
    setModal(data);
  }, []);

  const closeVariantModal = useCallback(() => {
    setModal(null);
  }, []);

  return (
    <VariantModalContext.Provider value={{ modal, openVariantModal, closeVariantModal }}>
      {children}
    </VariantModalContext.Provider>
  );
}

export function useVariantModal() {
  return useContext(VariantModalContext);
}
