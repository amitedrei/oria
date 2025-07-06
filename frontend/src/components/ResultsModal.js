import { useState } from "react";
import Modal from "./Modal";
import "./ResultsModal.css";

export default function ResultsModal({ isOpen, onClose, songsResponse }) {
  const sortedSongs = [...(songsResponse?.songs || [])].sort(
    (a, b) => b.percentage - a.percentage
  );

  const [likedSongs, setLikedSongs] = useState({});

  // Create a stable key based on the post_embedding for differentiating likes
  const postEmbeddingKey = JSON.stringify(songsResponse?.post_embedding || []);

  const handleLike = async (song) => {
    const likeKey = `${song.id}_${postEmbeddingKey}`;
    try {
      const response = await fetch("/songs/like", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          song_id: song.id,
          post_embedding: songsResponse.post_embedding,
          song_embedding: song.song_embedding,
        }),
      });

      if (!response.ok) throw new Error("Failed to like the song");

      setLikedSongs((prev) => ({ ...prev, [likeKey]: true }));
    } catch (error) {
      console.error("Error liking song:", error);
    }
  };

  return (
    isOpen && (
      <Modal isOpen={isOpen} onClose={onClose} title="Top Matching Songs">
        <div className="results-container">
          {sortedSongs.map((song) => {
            const likeKey = `${song.id}_${postEmbeddingKey}`;
            const isLiked = likedSongs[likeKey];

            return (
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
                  <span className="song-percentage">{`${Math.round(
                    song.percentage * 100
                  )}%`}</span>

                  <button
                    onClick={() => handleLike(song)}
                    disabled={isLiked}
                    className="like-btn"
                    style={{
                      marginLeft: 12,
                      padding: "6px 14px",
                      borderRadius: 8,
                      background: isLiked ? "#888" : "#6200ea",
                      color: "#fff",
                      border: "none",
                      cursor: isLiked ? "default" : "pointer",
                      fontWeight: "bold",
                      marginRight: 4,
                      transition: "background 0.3s ease",
                    }}
                  >
                    {isLiked ? "Liked" : "Like!"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </Modal>
    )
  );
}