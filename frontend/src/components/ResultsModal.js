import React from 'react';
import Modal from './Modal';
import './ResultsModal.css';

function ResultsModal({ isOpen, onClose, songs }) {
    const sortedSongs = songs.sort((a, b) => b.distance - a.distance);
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
                            <div className="match-percentage">{Math.round(song.distance * 100)}%</div>
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${Math.round(song.distance * 100)}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </Modal>
    );
}

export default ResultsModal;
