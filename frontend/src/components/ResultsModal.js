import { useState } from "react";
import Modal from "./Modal";
import "./ResultsModal.css";
import { FaHeart, FaRegHeart } from 'react-icons/fa'; 

export default function ResultsModal({ isOpen, onClose, songsResponse }) {
  const sortedSongs = [...(songsResponse?.songs || [])].sort(
    (a, b) => b.percentage - a.percentage
  );

  const [likedSongs, setLikedSongs] = useState({});

  // Create a stable key based on the post_embedding for differentiating likes
  const postEmbeddingKey = JSON.stringify(songsResponse?.post_embedding || []);

  const handleLike = async (song, isLiked) => {
    const newStatus = isLiked ? "unlike" : "like";
    const likeKey = `${song.id}_${postEmbeddingKey}`;
    try {
      const response = await fetch(`/songs/${newStatus}`, {
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

      if (!response.ok) throw new Error(`Failed to ${newStatus} the song`);

      setLikedSongs((prev) => ({ ...prev, [likeKey]: !isLiked }));
    } catch (error) {
      console.error(`Error ${newStatus} song:`, error);
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
                <div className="song-title">
                <a
                  href={song.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {song.name}
                </a>
                </div>
                <div className="song-artist">{song.artists.join(", ")}</div>
              </div>

              <div>
                <span className="song-percentage">{`${Math.round(
                song.percentage * 100
                )}%`}</span>

                <button
                onClick={() => handleLike(song, isLiked)}
                className="like-btn"
                >
                {isLiked ? <FaHeart /> : <FaRegHeart />}
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