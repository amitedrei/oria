import React, { useState, useEffect, useRef } from 'react';
import './MusicAnalysisLoader.css';

const MusicAnalysisLoader = ({ 
  songs = [], 
  onComplete, 
  apiResponse = null, 
  forceComplete = false
}) => {
  const [allSongs, setAllSongs] = useState([]);
  const [visibleNodes, setVisibleNodes] = useState([]);
  const [connections, setConnections] = useState([]);
  const [isComplete, setIsComplete] = useState(false);
  const [phase, setPhase] = useState('scanning');
  const [progress, setProgress] = useState(0);
  const [fadeOut, setFadeOut] = useState(false);
  const [animationComplete, setAnimationComplete] = useState(false);
  const [isLoadingSongs, setIsLoadingSongs] = useState(true);
  const [error, setError] = useState(null);
  const hasStartedRef = useRef(false);   
  const hasCompletedRef = useRef(false); 
  const resultsProcessedRef = useRef(false);
  const addSongsIntervalRef = useRef(null);

  const phases = [
    { id: 'scanning', text: 'Analyzing your image' },
    { id: 'matching', text: 'Finding matches' },
    { id: 'ranking', text: 'Ranking results' },
    { id: 'finalizing', text: 'Preparing songs' },
    { id: 'complete', text: 'Results ready' }
  ];

  const fetchSongs = async () => {
    try {
      setIsLoadingSongs(true);
      const isMobile = window.innerWidth <= 480;
      const count = isMobile ? 15 : 20;
      const response = await fetch(`/songs/?count=${count}`);
      if (!response.ok) throw new Error('Failed to fetch songs');
      const songsData = await response.json();
      setAllSongs(songsData);
      setIsLoadingSongs(false);
    } catch (error) {
      setError(error.message);
      const count = window.innerWidth <= 480 ? 15 : 20;
      const fallbackSongs = Array.from({ length: count }, (_, i) => ({
        id: `song-${i}`,
        name: `Track ${i + 1}`,
        link: '',
        thumbnail: `https://picsum.photos/64/64?random=${i}`,
        artists: [`Artist ${i + 1}`]
      }));
      setAllSongs(fallbackSongs);
      setIsLoadingSongs(false);
    }
  };

  const generateRandomNonOverlappingPositions = (count, existingPositions = []) => {
    const canvas = document.querySelector('.music-loader-canvas');
    const canvasRect = canvas ? canvas.getBoundingClientRect() : { width: 700, height: 320 };
    const canvasWidth = canvasRect.width;
    const canvasHeight = canvasRect.height;
    
    const isMobile = window.innerWidth <= 480;
    const isTablet = window.innerWidth <= 768;
    
    const margin = isMobile ? 30 : (isTablet ? 40 : 50);
    const nodeSize = isMobile ? 40 : (isTablet ? 48 : 56);
    const safeDistance = nodeSize + (isMobile ? 20 : 30);
    
    const maxPerRow = Math.floor((canvasWidth - 2 * margin) / safeDistance);
    const maxPerCol = Math.floor((canvasHeight - 2 * margin) / safeDistance);
    const maxNodes = maxPerRow * maxPerCol;
    
    const actualCount = Math.min(count, maxNodes);
    const positions = [];
    const allPositions = [...existingPositions];
    const maxAttempts = 200;
    
    for (let i = 0; i < actualCount; i++) {
      let attempts = 0;
      let position = null;
      
      while (attempts < maxAttempts && !position) {
        const x = margin + Math.random() * (canvasWidth - 2 * margin);
        const y = margin + Math.random() * (canvasHeight - 2 * margin);
        
        const tooClose = allPositions.some(p => {
          const dx = p.x - x;
          const dy = p.y - y;
          return Math.hypot(dx, dy) < safeDistance;
        });
        
        if (!tooClose) {
          position = { x, y };
          break;
        }
        attempts++;
      }
      
      if (!position) {
        const row = Math.floor(i / maxPerRow);
        const col = i % maxPerRow;
        const gridX = margin + (col + 0.5) * ((canvasWidth - 2 * margin) / maxPerRow);
        const gridY = margin + (row + 0.5) * ((canvasHeight - 2 * margin) / maxPerCol);
        
        position = {
          x: gridX + (Math.random() - 0.5) * 10,
          y: gridY + (Math.random() - 0.5) * 10
        };
      }
      
      positions.push(position);
      allPositions.push(position);
    }
    
    return positions;
  };

  const prepareSongs = (songs) => {
    const positions = generateRandomNonOverlappingPositions(songs.length);
    return songs.map((song, index) => ({
      ...song,
      ...positions[index],
      uniqueId: song.id,
      visible: false,
      animationDelay: index * 100
    }));
  };

  const generateConnections = (nodes) => {
    const visibleNodes = nodes.filter(n => n.visible);
    const connections = [];
    
    for (let i = 0; i < visibleNodes.length; i++) {
      for (let j = i + 1; j < visibleNodes.length; j++) {
        const node1 = visibleNodes[i];
        const node2 = visibleNodes[j];
        const distance = Math.sqrt(
          Math.pow(node2.x - node1.x, 2) + 
          Math.pow(node2.y - node1.y, 2)
        );
        
        if (distance < 200 && Math.random() > 0.5) {
          connections.push({
            id: `${node1.uniqueId}-${node2.uniqueId}`,
            x1: node1.x,
            y1: node1.y,
            x2: node2.x,
            y2: node2.y,
            distance,
            angle: Math.atan2(node2.y - node1.y, node2.x - node1.x) * 180 / Math.PI
          });
        }
      }
    }
    
    return connections;
  };

  useEffect(() => {
    fetchSongs();
  }, []);

  useEffect(() => {
    if (
      hasStartedRef.current ||
      hasCompletedRef.current ||
      allSongs.length === 0 ||
      isLoadingSongs ||
      error
    ) return;
  
    hasStartedRef.current = true;
    const prepared = prepareSongs(allSongs);
    setVisibleNodes(prepared);
    
    const runAnimation = async () => {
      const start = Date.now();
      setPhase('scanning');
      setProgress(0);

      const canvas = document.querySelector('.music-loader-canvas');
      const canvasRect = canvas ? canvas.getBoundingClientRect() : { width: 700, height: 320 };
      const isMobile = window.innerWidth <= 480;
      const isTablet = window.innerWidth <= 768;
      
      const nodeSize = isMobile ? 40 : (isTablet ? 48 : 56);
      const safeDistance = nodeSize + (isMobile ? 20 : 30);
      const margin = isMobile ? 30 : (isTablet ? 40 : 50);
      
      const maxPerRow = Math.floor((canvasRect.width - 2 * margin) / safeDistance);
      const maxPerCol = Math.floor((canvasRect.height - 2 * margin) / safeDistance);
      const totalCapacity = maxPerRow * maxPerCol;
      const maxVisible = Math.min(Math.max(totalCapacity - 5, 10), 20);
      
      const defaultInitial = isMobile ? 6 : isTablet ? 8 : 10;
      const initialSongs = Math.min(Math.floor(maxVisible * 0.5), defaultInitial);
      for (let i = 0; i < initialSongs && i < prepared.length; i++) {
        if (hasCompletedRef.current || error) break;

        setVisibleNodes(prev => {
          const updated = [...prev];
          updated[i] = { ...updated[i], visible: true };
          return updated;
        });

        if (i > 3) {
          const visibleSongs = prepared.slice(0, i + 1).map(s => ({ ...s, visible: true }));
          setConnections(generateConnections(visibleSongs));
        }

        setProgress(Math.round((i / prepared.length) * 25));
        await new Promise(r => setTimeout(r, 100));
      }

      const songsPerInterval = isMobile ? 1 : 2;
      const intervalTime = isMobile ? 1500 : 1000;
      const addedRef = { current: initialSongs };
      
      addSongsIntervalRef.current = setInterval(() => {
        if (hasCompletedRef.current || error || resultsProcessedRef.current || addedRef.current >= maxVisible || addedRef.current >= prepared.length) {
          clearInterval(addSongsIntervalRef.current);
          return;
        }

        const toAdd = Math.min(songsPerInterval, maxVisible - addedRef.current, prepared.length - addedRef.current);
        
        if (toAdd > 0) {
          setVisibleNodes(prev => {
            const updated = [...prev];
            for (let j = 0; j < toAdd; j++) {
              const idx = addedRef.current + j;
              if (updated[idx]) {
                updated[idx] = { ...updated[idx], visible: true };
              }
            }
            return updated;
          });
          
          addedRef.current += toAdd;
          
          setConnections(generateConnections(prepared.slice(0, addedRef.current).map((s, idx) => ({ ...s, visible: idx < addedRef.current }))));
        }
      }, intervalTime);

      setPhase('matching');
      await new Promise(r => setTimeout(r, 600));
      setProgress(50);

      setPhase('ranking');
      await new Promise(r => setTimeout(r, 600));
      setProgress(75);

      setPhase('finalizing');
      await new Promise(r => setTimeout(r, 600));
      setProgress(95);

      const elapsed = Date.now() - start;
      if (elapsed < 3000) {
        await new Promise(r => setTimeout(r, 3000 - elapsed));
      }

      setProgress(100);
      setAnimationComplete(true);
    };
  
    runAnimation();
  }, [allSongs, isLoadingSongs, error]);

  useEffect(() => {
    if (!animationComplete || !apiResponse || apiResponse.error || fadeOut || resultsProcessedRef.current) return;

    const processResults = async () => {
      resultsProcessedRef.current = true;
      
      if (addSongsIntervalRef.current) {
        clearInterval(addSongsIntervalRef.current);
      }
      
      const sortedResults = [...apiResponse].sort((a, b) => b.percentage - a.percentage);
      const rankMap = {};
      sortedResults.forEach((song, index) => {
        let rank;
        if (index === 0) rank = 'rank-1';
        else if (index === 1) rank = 'rank-2';
        else if (index === 2) rank = 'rank-3';
        else rank = 'rank-other';
        rankMap[song.id] = rank;
      });
      
      const resultSongIds = apiResponse.map(song => song.id);
      const currentVisibleNodes = visibleNodes.filter(n => n.visible);
      
      const visibleResultIds = currentVisibleNodes
        .filter(n => resultSongIds.includes(n.id))
        .map(n => n.id);
      
      const newResultSongs = apiResponse.filter(song => 
        !currentVisibleNodes.some(n => n.id === song.id)
      );
      
      if (newResultSongs.length > 0) {
        const currentPositions = currentVisibleNodes.map(n => ({ x: n.x, y: n.y }));
        const newPositions = generateRandomNonOverlappingPositions(
          newResultSongs.length, 
          currentPositions
        );
        
        const newNodes = newResultSongs.map((song, i) => ({
          ...song,
          x: newPositions[i].x,
          y: newPositions[i].y,
          uniqueId: song.id,
          visible: false,
          isResult: true,
          rankClass: rankMap[song.id]
        }));
        
        setVisibleNodes(prev => [...prev, ...newNodes]);
        
        await new Promise(resolve => setTimeout(resolve, 300));
        
        for (let i = 0; i < newNodes.length; i++) {
          setVisibleNodes(prev => prev.map(node => {
            if (node.uniqueId === newNodes[i].uniqueId) {
              return { ...node, visible: true };
            }
            return node;
          }));
          await new Promise(resolve => setTimeout(resolve, 150));
        }
      }
      
      const nodesToHide = currentVisibleNodes.filter(n => !resultSongIds.includes(n.id));
      
      if (nodesToHide.length > 0) {
        for (let i = 0; i < nodesToHide.length; i++) {
          setVisibleNodes(prev => prev.map(node => {
            if (node.uniqueId === nodesToHide[i].uniqueId) {
              return { ...node, visible: false };
            }
            return node;
          }));
          await new Promise(resolve => setTimeout(resolve, 80));
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 600));
      
      setVisibleNodes(prev => prev.map(node => {
        if (resultSongIds.includes(node.id)) {
          return { 
            ...node, 
            isFinalResult: true, 
            scaled: true,
            rankClass: rankMap[node.id]
          };
        }
        return node;
      }));
      
      const finalVisibleResults = visibleNodes.filter(node => 
        resultSongIds.includes(node.id) && node.visible !== false
      );
      setConnections(generateConnections(finalVisibleResults));
      
      hasCompletedRef.current = true;
      setPhase('complete');
      setProgress(100);
      
      await new Promise(r => setTimeout(r, 800));
      setFadeOut(true);
      await new Promise(r => setTimeout(r, 600));
      
      setIsComplete(true);
      if (onComplete) onComplete(apiResponse);
    };

    processResults();
  }, [animationComplete, apiResponse, fadeOut, onComplete]);

  useEffect(() => {
    if ((animationComplete && (forceComplete || error)) || (forceComplete && !apiResponse)) {
      if (addSongsIntervalRef.current) {
        clearInterval(addSongsIntervalRef.current);
      }
      
      const completeSequence = async () => {
        setFadeOut(true);
        await new Promise(resolve => setTimeout(resolve, 600));
        
        setIsComplete(true);
        if (onComplete) {
          onComplete(error ? { error } : null);
        }
      };
      
      completeSequence();
    }
  }, [animationComplete, forceComplete, error, onComplete, apiResponse]);

  useEffect(() => {
    if (forceComplete && !apiResponse) {
      setError('Connection interrupted');
    }
  }, [forceComplete, apiResponse]);

  useEffect(() => {
    if (apiResponse && addSongsIntervalRef.current) {
      clearInterval(addSongsIntervalRef.current);
    }
  }, [apiResponse]);

  useEffect(() => {
    return () => {
      if (addSongsIntervalRef.current) {
        clearInterval(addSongsIntervalRef.current);
      }
    };
  }, []);

  const getCurrentPhase = () => phases.find(p => p.id === phase) || phases[0];
  const currentPhase = getCurrentPhase();
  const activePhaseIndex = phases.findIndex(p => p.id === phase);

  if (isComplete) {
    return null;
  }

  return (
    <div className="music-loader-overlay">
      <div className={`music-loader-container ${fadeOut ? 'fade-out' : ''} ${error ? 'error' : ''}`}>
        <div className="music-loader-header">
          <h2 className="music-loader-title">Finding Your Perfect Match</h2>
          <p className="music-loader-subtitle">
            {error ? 'Connection error occurred' : 'We are analyzing your image'}
          </p>
        </div>
        
        <div className="music-loader-canvas">
          <div className="music-loader-grid" />
          
          {connections.map(conn => (
            <div
              key={conn.id}
              className="music-loader-connection"
              style={{
                left: `${conn.x1}px`,
                top: `${conn.y1}px`,
                width: `${conn.distance}px`,
                transform: `rotate(${conn.angle}deg)`,
                transformOrigin: 'left center'
              }}
            />
          ))}
          
          {visibleNodes.map((song) => (
            <div
              key={song.uniqueId}
              className={`music-loader-song ${song.visible ? 'visible' : 'hidden'} ${song.isResult ? 'result-song' : ''} ${song.isFinalResult ? 'final-result' : ''} ${song.scaled ? 'scaled' : ''} ${song.rankClass || ''}`}
              style={{
                left: `${song.x}px`,
                top: `${song.y}px`,
                transitionDelay: `${song.visible ? song.animationDelay : 0}ms`
              }}
            >
              <div className="music-loader-song-circle">
                <img 
                  src={song.thumbnail} 
                  alt={song.name}
                  className="music-loader-song-thumbnail"
                  loading="lazy"
                />
              </div>
            </div>
          ))}
        </div>
        
        <div className="music-loader-progress">
          <div className={`music-loader-phase ${phase === 'complete' ? 'complete' : ''}`}>
            {error ? 'Error' : currentPhase.text}
          </div>
          
          <div className="music-loader-phase-dots">
            {phases.map((phase, index) => (
              <div 
                key={phase.id}
                className={`music-loader-phase-dot ${index <= activePhaseIndex ? 'active' : ''}`}
              />
            ))}
          </div>
          
          <div className={`music-loader-percentage ${progress === 100 ? 'complete' : ''}`}>
            {progress}%
          </div>
        </div>
        
        <div className="music-loader-progress-bar">
          <div 
            className="music-loader-progress-fill"
            style={{ transform: `scaleX(${progress / 100})` }}
          />
        </div>
      </div>
    </div>
  );
};

export default MusicAnalysisLoader;