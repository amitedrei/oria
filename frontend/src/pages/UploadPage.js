import React, { useState, useRef } from 'react';
import { ArrowRight, X, Loader } from 'lucide-react';

function UploadPage({ onNavigate }) {
  const [dragActive, setDragActive] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [additionalText, setAdditionalText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [alertMessage, setAlertMessage] = useState(null);
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

  const handleSubmit = () => {
    if (!imageFile) {
      showAlert("Please upload an image first");
      return;
    }
    
    setIsLoading(true);
    
    // Simulate processing time
    setTimeout(() => {
      setIsLoading(false);
      onNavigate('results');
    }, 1500);
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
          style={{ display: "none" }}
        />
      </div>
      
      <input 
        type="text" 
        className="input-field" 
        placeholder="Type your additional text" 
        value={additionalText}
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
    </div>
  );
}

export default UploadPage;