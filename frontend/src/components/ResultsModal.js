import React from 'react';
import Modal from './Modal';
import './ResultsModal.css';

function ResultsModal({ isOpen, onClose, songs }) {
    const sortedSongs = songs.sort((a, b) => b.percentage - a.percentage);
    const [playingId, setPlayingId] = React.useState(null);
    const [loadingId, setLoadingId] = React.useState(null);
    const [progress, setProgress] = React.useState(0);
    const audioRef = React.useRef(null);
    const timerRef = React.useRef(null);

    const handlePlay = async (song) => {
        if (playingId === song.id) {
            // Stop playback
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current.currentTime = 0;
            }
            setPlayingId(null);
            setProgress(0);
            clearInterval(timerRef.current);
            return;
        }
        setLoadingId(song.id);
        setProgress(0);

        // Create new audio element
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
        }
        const audio = new window.Audio(song.url);
        audioRef.current = audio;

        audio.addEventListener('canplaythrough', () => {
            setLoadingId(null);
            setPlayingId(song.id);
            audio.play();
            setProgress(0);
            let elapsed = 0;
            timerRef.current = setInterval(() => {
                elapsed += 0.1;
                setProgress((elapsed / 10) * 100);
                if (elapsed >= 10) {
                    audio.pause();
                    audio.currentTime = 0;
                    setPlayingId(null);
                    setProgress(0);
                    clearInterval(timerRef.current);
                }
            }, 100);
        }, { once: true });

        audio.addEventListener('error', () => {
            setLoadingId(null);
            setPlayingId(null);
            setProgress(0);
            clearInterval(timerRef.current);
        });
        audio.load();
    };

    React.useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
            }
            clearInterval(timerRef.current);
        };
    }, []);

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Top Matching Songs"
        >
            <div className="results-container">
                {sortedSongs.map(song => (
                    <div key={song.id} className="song-result-item">
                        <div className="song-info">
                            <div className="song-title">{song.name}</div>
                            <div className="song-artist">{song.artists.join(', ')}</div>
                            {song.url && (
                                <a 
                                    href={song.url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="song-url"
                                >
                                    Listen on Youtube
                                </a>
                            )}
                        </div>
                        <div className="match-info">
                            <div className="match-percentage">{Math.round(song.percentage)}%</div>
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${Math.round(song.percentage)}%` }}
                                ></div>
                            </div>
                        </div>
                        <div className="song-player">
                            <button
                                className={`player-btn${playingId === song.id ? ' playing' : ''}`}
                                onClick={() => handlePlay(song)}
                                disabled={loadingId === song.id}
                                style={{
                                    borderRadius: '50%',
                                    width: 40,
                                    height: 40,
                                    border: 'none',
                                    background: '#eee',
                                    position: 'relative',
                                    marginLeft: 16,
                                    cursor: loadingId === song.id ? 'wait' : 'pointer'
                                }}
                                aria-label={playingId === song.id ? 'Stop preview' : 'Play 10s preview'}
                            >
                                {loadingId === song.id ? (
                                    <span className="circular-loader" style={{
                                        width: 24,
                                        height: 24,
                                        display: 'inline-block',
                                        border: '3px solid #ccc',
                                        borderTop: '3px solid #333',
                                        borderRadius: '50%',
                                        animation: 'spin 1s linear infinite'
                                    }} />
                                ) : (
                                    <>
                                        <svg width="20" height="20" viewBox="0 0 20 20">
                                            {playingId === song.id ? (
                                                <rect x="5" y="4" width="3" height="12" fill="#333"/>
                                            ) : (
                                                <polygon points="6,4 16,10 6,16" fill="#333"/>
                                            )}
                                            {playingId === song.id && (
                                                <rect x="12" y="4" width="3" height="12" fill="#333"/>
                                            )}
                                        </svg>
                                        {playingId === song.id && (
                                            <svg
                                                style={{
                                                    position: 'absolute',
                                                    top: 0,
                                                    left: 0,
                                                    width: 40,
                                                    height: 40,
                                                    pointerEvents: 'none'
                                                }}
                                                width="40"
                                                height="40"
                                            >
                                                <circle
                                                    cx="20"
                                                    cy="20"
                                                    r="16"
                                                    stroke="#1976d2"
                                                    strokeWidth="3"
                                                    fill="none"
                                                    strokeDasharray={2 * Math.PI * 16}
                                                    strokeDashoffset={2 * Math.PI * 16 * (1 - progress / 100)}
                                                    style={{ transition: 'stroke-dashoffset 0.1s linear' }}
                                                />
                                            </svg>
                                        )}
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                ))}
            </div>
            <style>
                {`
                @keyframes spin {
                    0% { transform: rotate(0deg);}
                    100% { transform: rotate(360deg);}
                }
                .song-result-item {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                .song-player {
                    display: flex;
                    align-items: center;
                }
                `}
            </style>
        </Modal>
    );
}

export default ResultsModal;