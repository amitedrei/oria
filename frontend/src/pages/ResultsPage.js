import React from 'react';
import { ArrowLeft } from 'lucide-react';

function ResultsPage({ onNavigate }) {
  const songs = [
    { id: 1, title: 'xxxxxxx', artist: 'Artist', matchPercentage: 94 },
    { id: 2, title: 'xxxxxxx', artist: 'Artist', matchPercentage: 88 },
    { id: 3, title: 'xxxxxxx', artist: 'Artist', matchPercentage: 85 }
  ];

  return (
    <div className="card">
      <h1 className="results-title">Your best songs</h1>
      
      <div className="song-list">
        {songs.map(song => (
          <div key={song.id} className="song-item">
            <div className="song-image"></div>
            <div className="song-details">
              <div className="song-title">{song.title}</div>
              <div className="song-artist">{song.artist}</div>
            </div>
            <div className="match-percentage">
              <span className="percentage">{song.matchPercentage} %</span>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${song.matchPercentage}%` }}
                ></div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <button className="show-more-button">show more</button>
      
      <button className="button" onClick={() => onNavigate('upload')}>
        <span className="button-text">back</span>
        <ArrowLeft size={16} />
      </button>
    </div>
  );
}

export default ResultsPage;
