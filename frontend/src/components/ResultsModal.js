import { useEffect, useRef, useState } from "react";
import Modal from "./Modal";
import "./ResultsModal.css";

export default function ResultsModal({ isOpen, onClose, songs }) {
  const sortedSongs = [...songs].sort((a, b) => b.percentage - a.percentage);
  const [playingId, setPlayingId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [playerReady, setPlayerReady] = useState(false);
  const playerRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;

    const createPlayer = () => {
      playerRef.current = new window.YT.Player("yt-player", {
        height: "0",
        width: "0",
        videoId: "",
        playerVars: {
          autoplay: 0,
          controls: 0,
          rel: 0,
          modestbranding: 1,
          origin: window.location.origin,
        },
        events: {
          onReady: () => setPlayerReady(true),
          onStateChange: (e) => {
            if (e.data === window.YT.PlayerState.ENDED) {
              clearInterval(intervalRef.current);
              setPlayingId(null);
              setProgress(0);
            }
          },
        },
      });
    };

    // Load the IFrame API script if needed
    if (!document.getElementById("youtube-iframe-api")) {
      window.onYouTubeIframeAPIReady = createPlayer;
      const tag = document.createElement("script");
      tag.id = "youtube-iframe-api";
      tag.src = "https://www.youtube.com/iframe_api";
      document.body.appendChild(tag);
    } else if (window.YT && window.YT.Player) {
      createPlayer();
    }

    return () => {
      clearInterval(intervalRef.current);
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
      setPlayerReady(false);
      setPlayingId(null);
      setProgress(0);
    };
  }, [isOpen]);

  const handlePlay = (song) => {
    if (!playerReady || !playerRef.current) return;
    const player = playerRef.current;
    const state = player.getPlayerState();
    const videoId = new URL(song.url).searchParams.get("v");

    if (playingId === song.id) {
      if (state === window.YT.PlayerState.PLAYING) {
        player.pauseVideo();
        clearInterval(intervalRef.current);
        setPlayingId(null);
        setProgress(0);
      } else if (state === window.YT.PlayerState.PAUSED) {
        player.playVideo();
        intervalRef.current = setInterval(() => {
          setProgress((prev) => {
            const next = prev + 1;
            if (next >= 100) {
              player.pauseVideo();
              clearInterval(intervalRef.current);
              setPlayingId(null);
              return 0;
            }
            return next;
          });
        }, 100);
        setPlayingId(song.id);
      }
      return;
    }

    player.loadVideoById(videoId);
    player.playVideo();
    setPlayingId(song.id);
    setProgress(0);
    clearInterval(intervalRef.current);

    intervalRef.current = setInterval(() => {
      setProgress((prev) => {
        const next = prev + 1;
        if (next >= 100) {
          player.pauseVideo();
          clearInterval(intervalRef.current);
          setPlayingId(null);
          return 0;
        }
        return next;
      });
    }, 100);
  };

  return (
    <>
      <div
        id="yt-player"
        style={{
          position: "absolute",
          visibility: "hidden",
          width: 0,
          height: 0,
        }}
      />

      {isOpen && (
        <Modal isOpen={isOpen} onClose={onClose} title="Top Matching Songs">
          <div className="results-container">
            {sortedSongs.map((song) => (
              <div key={song.id} className="song-result-item">
                <div className="song-info">
                  <div className="song-title">{song.name}</div>
                  <div className="song-artist">{song.artists.join(", ")}</div>
                </div>
                <div className="song-player" style={{ position: "relative" }}>
                  <button
                    onClick={() => handlePlay(song)}
                    disabled={!playerReady}
                    className={`player-btn ${
                      playingId === song.id ? "playing" : ""
                    }`}
                    aria-label={
                      playingId === song.id &&
                      playerRef.current.getPlayerState() ===
                        window.YT.PlayerState.PLAYING
                        ? "Pause preview"
                        : "Play 10s preview"
                    }
                    style={{
                      borderRadius: "50%",
                      width: 40,
                      height: 40,
                      border: "none",
                      background: "#eee",
                      cursor: playerReady ? "pointer" : "wait",
                      fontSize: 20,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    {!playerReady
                      ? "⏳"
                      : playingId === song.id &&
                        playerRef.current.getPlayerState() ===
                          window.YT.PlayerState.PLAYING
                      ? "⏸"
                      : "▶"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Modal>
      )}
    </>
  );
}
