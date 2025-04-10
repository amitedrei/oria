import React, { useState } from 'react';
import './App.css';
import Header from './components/Header';
import MainLayout from './components/MainLayout';
import AboutPage from './pages/AboutPage';
import UploadPage from './pages/UploadPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  const [currentPage, setCurrentPage] = useState('upload');
  
  const renderPage = () => {
    switch(currentPage) {
      case 'about':
        return <AboutPage onNavigate={setCurrentPage} />;
      case 'upload':
        return <UploadPage onNavigate={setCurrentPage} />;
      case 'results':
        return <ResultsPage onNavigate={setCurrentPage} />;
      default:
        return <AboutPage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="app">
      <Header onNavigate={setCurrentPage} />
      <MainLayout>
        {renderPage()}
      </MainLayout>
    </div>
  );
}

export default App;