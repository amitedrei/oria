import { ArrowRight, Loader, X } from "lucide-react";
import { useRef, useState } from "react";
import MusicAnalysisLoader from "../components/MusicAnalysisLoader";
import ResultsModal from "../components/ResultsModal";

function UploadPage({ onNavigate }) {
  const [dragActive, setDragActive] = useState(false);
  const [imageFile, setImageFile] = useState(null);
  const [additionalText, setAdditionalText] = useState("");
  const [alertMessage, setAlertMessage] = useState(null);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [searchResults, setSearchResults] = useState();
  const [showMusicLoader, setShowMusicLoader] = useState(false);
  const [apiResponse, setApiResponse] = useState(null);
  const [forceComplete, setForceComplete] = useState(false);
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
      if (file.type.startsWith("image/")) {
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
    e.stopPropagation();
    setImageFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const showAlert = (message) => {
    setAlertMessage(message);
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

    setApiResponse(null);
    setForceComplete(false);
    setShowMusicLoader(true);

    try {
      const formData = new FormData();
      formData.append("image", imageFile);
      formData.append("text", additionalText);

      const response = await fetch("/songs/find-songs", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to fetch songs");
      }

      const data = await response.json();
      setSearchResults(data);
      setApiResponse(data.songs);
    } catch (error) {
      setForceComplete(true);
      setTimeout(() => {
        setShowMusicLoader(false);
        showAlert("Failed to process your request. Please try again.");
      }, 500);
      console.error("Error:", error);
    }
  };

  return (
    <div className="card">
      <h1 className="upload-title">Lets find your perfect song</h1>

      <div
        className={`upload-area ${dragActive ? "active" : ""} ${
          imageFile ? "has-image" : ""
        }`}
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
                disabled={showMusicLoader}
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
          disabled={showMusicLoader}
          style={{ display: "none" }}
        />
      </div>

      <input
        type="text"
        className="input-field"
        placeholder="Type your additional text"
        value={additionalText}
        disabled={showMusicLoader}
        onChange={(e) => setAdditionalText(e.target.value)}
      />

      <button
        className="button"
        onClick={handleSubmit}
        disabled={showMusicLoader}
      >
        <span className="button-text">
          {showMusicLoader ? "processing..." : "continue"}
        </span>
        {showMusicLoader ? (
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

      {showMusicLoader && (
        <MusicAnalysisLoader
          songs={[]}
          apiResponse={apiResponse}
          forceComplete={forceComplete}
          onComplete={(responseData) => {
            setShowMusicLoader(false);
            if (responseData && !forceComplete) {
              setShowResultsModal(true);
            }
          }}
        />
      )}

      <ResultsModal
        isOpen={showResultsModal}
        onClose={() => setShowResultsModal(false)}
        songsResponse={searchResults}
      />
    </div>
  );
}

export default UploadPage;
