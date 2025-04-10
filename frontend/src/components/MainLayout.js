import React from 'react';

function MainLayout({ children }) {
  return (
    <main className="main-layout">
      {children}
    </main>
  );
}

export default MainLayout;