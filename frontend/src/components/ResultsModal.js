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

              <div className="song-player">
                <button
                  onClick={() => window.open(song.url, "_blank")}
                  className="player-btn"
                  aria-label={`Open ${song.name} in new tab`}
                >
                  ▶
                </button>
                <span>{`${Math.round(song.percentage * 100)}%`}</span>
              </div>
            </div>
          ))}
        </div>
      </Modal>
    )
  );
}
