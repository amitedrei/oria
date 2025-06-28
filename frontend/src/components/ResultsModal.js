import React from "react";
import Modal from "./Modal";
import "./ResultsModal.css";

export default function ResultsModal({ isOpen, onClose, songs }) {
  // Sort songs by descending percentage
  const sortedSongs = [...songs].sort((a, b) => b.percentage - a.percentage);

  return (
    isOpen && (
      <Modal isOpen={isOpen} onClose={onClose} title="Top Matching Songs">
        <div className="results-container">
          {sortedSongs.map((song) => (
            <div key={song.id} className="song-result-item">
              <div className="song-info">
                <div className="song-title">{song.name}</div>
                <div className="song-artist">{song.artists.join(", ")}</div>
              </div>

              <div className="song-player" style={{ display: "flex", alignItems: "center" }}>
                <button
                  onClick={() => window.open(song.url, "_blank")}
                  className="player-btn"
                  aria-label={`Open ${song.name} in new tab`}
                  style={{
                    borderRadius: "50%",
                    width: 40,
                    height: 40,
                    border: "none",
                    background: "#eee",
                    cursor: "pointer",
                    fontSize: 20,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    marginRight: 8,
                  }}
                >
                  ▶
                </button>
                <span className="song-percentage">{`${Math.round(song.percentage * 100)}%`}</span>
              </div>
            </div>
          ))}
        </div>
      </Modal>
    )
  );
}
