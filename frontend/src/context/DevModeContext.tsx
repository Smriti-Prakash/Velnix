import React, { createContext, useContext, useState, useEffect } from 'react';

interface DevModeContextType {
  isMockMode: boolean;
  setIsMockMode: (val: boolean) => void;
}

const DevModeContext = createContext<DevModeContextType | undefined>(undefined);

export const DevModeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Default to mock mode since it makes local testing/scaffolding/demos seamless
  const [isMockMode, setIsMockMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('velnix_mock_mode');
    return saved !== null ? saved === 'true' : true;
  });

  useEffect(() => {
    localStorage.setItem('velnix_mock_mode', String(isMockMode));
  }, [isMockMode]);

  return (
    <DevModeContext.Provider value={{ isMockMode, setIsMockMode }}>
      {children}
    </DevModeContext.Provider>
  );
};

export const useDevMode = () => {
  const context = useContext(DevModeContext);
  if (!context) {
    throw new Error('useDevMode must be used within a DevModeProvider');
  }
  return context;
};
