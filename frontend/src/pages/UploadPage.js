import React, { useState, useRef } from 'react';
import { ArrowRight, X, Loader } from 'lucide-react';
import ResultsModal from '../components/ResultsModal';

function UploadPage({ onNavigate }) {
  const [dragActive, setDragActive] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [additionalText, setAdditionalText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [alertMessage, setAlertMessage] = useState(null);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        handleFiles(file);
      } else {
        showAlert("Please upload an image file");
      }
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files[0]);
    }
  };

  const handleFiles = (file) => {
    setImageFile(file);
  };

  const onButtonClick = () => {
    fileInputRef.current.click();
  };

  const removeImage = (e) => {
    // Prevent triggering the upload dialog
    e.stopPropagation();
    setImageFile(null);
    // Reset the file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const showAlert = (message) => {
    setAlertMessage(message);
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      setAlertMessage(null);
    }, 3000);
  };

  const closeAlert = () => {
    setAlertMessage(null);
  };

  const handleSubmit = async () => {
    if (!imageFile) {
      showAlert("Please upload an image first");
      return;
    }
    
    setIsLoading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', imageFile);
      formData.append('text', additionalText);

      const response = await fetch('http://0.0.0.0:8000/songs/find-songs', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to fetch songs');
      }

      const data = await response.json();
      setSearchResults(data);
      setShowResultsModal(true);
    } catch (error) {
      showAlert("Failed to process your request. Please try again.");
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card">
      <h1 className="upload-title">Lets find your perfect song</h1>
      
      <div 
        className={`upload-area ${dragActive ? "active" : ""} ${imageFile ? "has-image" : ""}`}
        onClick={imageFile ? null : onButtonClick}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        {imageFile ? (
          <div className="preview-container">
            <div className="image-preview-wrapper">
              <img 
                src={URL.createObjectURL(imageFile)} 
                alt="Preview" 
                className="image-preview" 
              />
              <button 
                className="remove-button" 
                onClick={removeImage}
                aria-label="Remove image"
                disabled={isLoading}
              >
                <X size={18} />
              </button>
            </div>
            <p className="file-name">{imageFile.name}</p>
          </div>
        ) : (
          <p className="upload-text">*Drag or upload your image</p>
        )}
        <input
          ref={fileInputRef}
          type="file"
          className="input-file"
          accept="image/*"
          onChange={handleChange}
          disabled={isLoading}
          style={{ display: "none" }}
        />
      </div>
      
      <input 
        type="text" 
        className="input-field" 
        placeholder="Type your additional text" 
        value={additionalText}
        disabled={isLoading}
        onChange={(e) => setAdditionalText(e.target.value)}
      />
      
      <button className="button" onClick={handleSubmit} disabled={isLoading}>
        <span className="button-text">{isLoading ? "processing..." : "continue"}</span>
        {isLoading ? (
          <Loader size={16} className="spinner" />
        ) : (
          <ArrowRight size={16} />
        )}
      </button>
      
      {alertMessage && (
        <div className="alert-overlay">
          <div className="alert-dialog">
            <p>{alertMessage}</p>
            <button className="alert-button" onClick={closeAlert}>
              Got it
            </button>
          </div>
        </div>
      )}

      <ResultsModal 
        isOpen={showResultsModal}
        onClose={() => setShowResultsModal(false)}
        songs={searchResults}
      />
    </div>
  );
}

export default UploadPage;