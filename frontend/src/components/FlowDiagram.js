import React, { useState, useRef, useCallback, useEffect } from 'react';
import { ZoomIn, ZoomOut, Move, RotateCcw } from 'lucide-react';
import './FlowDiagram.css';

const NODE_WIDTH = 100;
const NODE_HEIGHT = 50;

const initialNodes = [
  {
    id: '1',
    position: { x: 100, y: 200 },
    label: 'SONG',
    color: 'linear-gradient(145deg, #667eea 0%, #764ba2 100%)',
    borderColor: '#4facfe',
  },
  {
    id: '2',
    position: { x: 350, y: 100 },
    label: 'Audio',
    color: 'linear-gradient(145deg, #f093fb 0%, #f5576c 100%)',
    borderColor: '#f093fb',
  },
  {
    id: '3',
    position: { x: 350, y: 200 },
    label: 'Name',
    color: 'linear-gradient(145deg, #4facfe 0%, #00f2fe 100%)',
    borderColor: '#4facfe',
  },
  {
    id: '4',
    position: { x: 350, y: 300 },
    label: 'Chorus',
    color: 'linear-gradient(145deg, #fa709a 0%, #fee140 100%)',
    borderColor: '#fa709a',
  },
  {
    id: '5',
    position: { x: 500, y: 100 },
    label: 'Mood',
    color: 'linear-gradient(145deg, #46aa84 0%, #91b15f 100%)',
    borderColor: '#a8edea',
  },
  {
    id: '7',
    position: { x: 700, y: 250 },
    label: 'Description',
    color: 'linear-gradient(145deg, #ff9a9e 0%, #fecfef 100%)',
    borderColor: '#ff9a9e',
  },
  {
    id: '8',
    position: { x: 700, y: 150 },
    label: 'Emotion',
    color: 'linear-gradient(145deg, #a18cd1 0%, #fbc2eb 100%)',
    borderColor: '#a18cd1',
  },
  {
    id: '9',
    position: { x: 850, y: 200 },
    label: 'IMAGE&TEXT',
    color: 'linear-gradient(145deg, #667eea 0%, #764ba2 100%)',
    borderColor: '#4facfe',
  },
];

const connections = [
  { from: '1', to: '2', color: '#667eea' },
  { from: '1', to: '3', color: '#4facfe' },
  { from: '1', to: '4', color: '#fa709a' },
  { from: '2', to: '5', color: '#f093fb' },
  { from: '5', to: '8', color: '#91b15f', dashed: true },
  { from: '3', to: '7', color: '#00f2fe', dashed: true },
  { from: '4', to: '7', color: '#ff9a9e', dashed: true },
  { from: '7', to: '9', color: '#764ba2' },
  { from: '8', to: '9', color: '#a18cd1' },
];

const FlowDiagram = () => {
  const [nodes, setNodes] = useState(initialNodes);
  const [selectedNode, setSelectedNode] = useState(null);
  const [dragState, setDragState] = useState({ isDragging: false, nodeId: null, offset: { x: 0, y: 0 } });
  const [panState, setPanState] = useState({
    isPanning: false,
    start: { x: 0, y: 0 },
    startViewBox: { x: 0, y: 0, scale: 1 },
  });
  const [viewBox, setViewBox] = useState({ x: 60, y: 0, scale: 0.8 });
  const [flowParticles, setFlowParticles] = useState([]);
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  // Helpers
  const getNodeById = (id) => nodes.find((node) => node.id === id);

  const screenToWorld = (screenX, screenY) => {
    const container = containerRef.current;
    if (!container) return { x: screenX, y: screenY };
    const rect = container.getBoundingClientRect();
    return {
      x: (screenX - rect.left) / viewBox.scale + viewBox.x,
      y: (screenY - rect.top) / viewBox.scale + viewBox.y,
    };
  };

  // Mouse Handlers
  const handleMouseDown = (e, nodeId) => {
    e.stopPropagation();
    const node = getNodeById(nodeId);
    const worldPos = screenToWorld(e.clientX, e.clientY);
    setDragState({
      isDragging: true,
      nodeId,
      offset: {
        x: worldPos.x - node.position.x,
        y: worldPos.y - node.position.y,
      },
    });
    setSelectedNode(node);
    e.preventDefault();
  };

  const handleCanvasMouseDown = (e) => {
    if (!e.target.closest('[data-node]')) {
      setPanState({
        isPanning: true,
        start: { x: e.clientX, y: e.clientY },
        startViewBox: { ...viewBox },
      });
      setSelectedNode(null);
      e.preventDefault();
    }
  };

  const handleMouseMove = useCallback(
    (e) => {
      if (dragState.isDragging && dragState.nodeId) {
        const worldPos = screenToWorld(e.clientX, e.clientY);
        setNodes((prevNodes) =>
          prevNodes.map((node) =>
            node.id === dragState.nodeId
              ? {
                  ...node,
                  position: {
                    x: worldPos.x - dragState.offset.x,
                    y: worldPos.y - dragState.offset.y,
                  },
                }
              : node
          )
        );
      } else if (panState.isPanning) {
        const deltaX = (e.clientX - panState.start.x) / viewBox.scale;
        const deltaY = (e.clientY - panState.start.y) / viewBox.scale;
        setViewBox({
          x: panState.startViewBox.x - deltaX,
          y: panState.startViewBox.y - deltaY,
          scale: viewBox.scale,
        });
      }
    },
    [dragState, panState, viewBox.scale]
  );

  const handleMouseUp = useCallback(() => {
    setDragState({ isDragging: false, nodeId: null, offset: { x: 0, y: 0 } });
    setPanState({
      isPanning: false,
      start: { x: 0, y: 0 },
      startViewBox: { x: 0, y: 0, scale: 1 },
    });
  }, []);

  const handleWheel = useCallback(
    (e) => {
      e.preventDefault();
      const container = containerRef.current;
      const rect = container.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      const worldMouseX = mouseX / viewBox.scale + viewBox.x;
      const worldMouseY = mouseY / viewBox.scale + viewBox.y;
      const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
      const newScale = Math.max(0.1, Math.min(3, viewBox.scale * zoomFactor));
      const newX = worldMouseX - mouseX / newScale;
      const newY = worldMouseY - mouseY / newScale;
      setViewBox({ x: newX, y: newY, scale: newScale });
    },
    [viewBox]
  );

  // Controls
  const zoomIn = () => {
    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const worldCenterX = centerX / viewBox.scale + viewBox.x;
    const worldCenterY = centerY / viewBox.scale + viewBox.y;
    const newScale = Math.min(3, viewBox.scale * 1.2);
    const newX = worldCenterX - centerX / newScale;
    const newY = worldCenterY - centerY / newScale;
    setViewBox({ x: newX, y: newY, scale: newScale });
  };

  const zoomOut = () => {
    const container = containerRef.current;
    const rect = container.getBoundingClientRect();
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const worldCenterX = centerX / viewBox.scale + viewBox.x;
    const worldCenterY = centerY / viewBox.scale + viewBox.y;
    const newScale = Math.max(0.1, viewBox.scale * 0.8);
    const newX = worldCenterX - centerX / newScale;
    const newY = worldCenterY - centerY / newScale;
    setViewBox({ x: newX, y: newY, scale: newScale });
  };

  const resetView = () => {
    setViewBox({ x: 60, y: 0, scale: 0.8 });
    setNodes(initialNodes);
    setSelectedNode(null);
  };

  // Effects
  useEffect(() => {
    if (dragState.isDragging || panState.isPanning) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [dragState.isDragging, panState.isPanning, handleMouseMove, handleMouseUp]);

  // Flow particles
  const createFlowParticle = (connection) => {
    const fromNode = getNodeById(connection.from);
    const toNode = getNodeById(connection.to);
    if (!fromNode || !toNode) return;
    const particleId = Date.now() + Math.random();
    const newParticle = {
      id: particleId,
      startX: fromNode.position.x + NODE_WIDTH / 2,
      startY: fromNode.position.y + NODE_HEIGHT / 2,
      endX: toNode.position.x + NODE_WIDTH / 2,
      endY: toNode.position.y + NODE_HEIGHT / 2,
      color: connection.color,
      progress: 0,
    };
    setFlowParticles((prev) => [...prev, newParticle]);
    const animateParticle = () => {
      setFlowParticles((prev) =>
        prev.map((particle) =>
          particle.id === particleId
            ? { ...particle, progress: Math.min(particle.progress + 0.02, 1) }
            : particle
        )
      );
    };
    const interval = setInterval(animateParticle, 16);
    setTimeout(() => {
      clearInterval(interval);
      setFlowParticles((prev) => prev.filter((p) => p.id !== particleId));
    }, 2000);
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const randomConnection = connections[Math.floor(Math.random() * connections.length)];
      createFlowParticle(randomConnection);
    }, 1500);
    return () => clearInterval(interval);
  }, [nodes]);

  // Drawing helpers
  const getConnectionPath = (fromNode, toNode) => {
    if (!fromNode || !toNode) return '';
    const startX = fromNode.position.x + NODE_WIDTH / 2;
    const startY = fromNode.position.y + NODE_HEIGHT / 2;
    const endX = toNode.position.x + NODE_WIDTH / 2;
    const endY = toNode.position.y + NODE_HEIGHT / 2;
    return `M ${startX} ${startY} L ${endX} ${endY}`;
  };

  const getCursor = () => {
    if (dragState.isDragging || panState.isPanning) return 'grabbing';
    return 'grab';
  };

  // Render
  const renderNode = (node) => {
    return (<div
      key={node.id}
      data-node="true"
      className="node"
      style={{
        left: node.position.x,
        top: node.position.y,
        width: `${NODE_WIDTH}px`,
        height: `${NODE_HEIGHT}px`,
        background: node.color,
        border: `2px solid ${node.borderColor}`,
        cursor: dragState.isDragging && dragState.nodeId === node.id ? 'grabbing' : 'grab',
        transform: selectedNode?.id === node.id ? 'scale(1.05)' : 'scale(1)',
        boxShadow: selectedNode?.id === node.id
          ? `0 8px 25px ${node.borderColor}60, 0 0 20px ${node.borderColor}40`
          : `0 4px 15px ${node.borderColor}30`,
        transition: dragState.isDragging && dragState.nodeId === node.id ? 'none' : 'all 0.3s ease',
        zIndex: selectedNode?.id === node.id ? 10 : 5,
      }}
      onMouseDown={(e) => handleMouseDown(e, node.id)}
      onClick={(e) => {
        e.stopPropagation();
        setSelectedNode(node);
      }}
    >
      {node.label}
    </div>);
  }

  const renderPracticle = (particle) => {
    const currentX = particle.startX + (particle.endX - particle.startX) * particle.progress;
    const currentY = particle.startY + (particle.endY - particle.startY) * particle.progress;
    return (
      <circle
        key={particle.id}
        cx={currentX}
        cy={currentY}
        r={4}
        fill={particle.color}
        opacity={Math.sin(particle.progress * Math.PI)}
        filter="drop-shadow(0 0 8px rgba(79, 172, 254, 0.8))"
      />
    );
  }
          
  const renderConnection = (connection, index) => {
    const fromNode = getNodeById(connection.from);
    const toNode = getNodeById(connection.to);
    const path = getConnectionPath(fromNode, toNode);
    return (
      <g key={index}>
        <path
          d={path}
          stroke={connection.color}
          strokeWidth={connection.dashed ? 2 : 3}
          strokeDasharray={connection.dashed ? '8,4' : 'none'}
          fill="none"
          opacity={0.8}
          filter="drop-shadow(0 0 6px rgba(79, 172, 254, 0.4))"
          markerEnd={`url(#arrow-${index})`}
        />
        <path
          d={path}
          stroke={connection.color}
          strokeWidth={connection.dashed ? 4 : 6}
          strokeDasharray={connection.dashed ? '8,4' : 'none'}
          fill="none"
          opacity={0.2}
        />
      </g>
    );
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: '320px' }}>
      <div className='control-panel'>
        <button onClick={zoomIn} title="Zoom In">
          <ZoomIn size={16} />
        </button>
        <button onClick={zoomOut} title="Zoom Out">
          <ZoomOut size={16} />
        </button>
        <button onClick={resetView} title="Reset View">
          <RotateCcw size={16} />
        </button>
        <div className='scale-display'>
          <Move size={14} />
          {Math.round(viewBox.scale * 100)}%
        </div>
      </div>

      <div
        ref={containerRef}
        className="main-canvas"
        style={{cursor: getCursor()}}
        onMouseDown={handleCanvasMouseDown}
        onWheel={handleWheel}
      >
        <div className='background'  />

        <div
          className='view-container'
          style={{transform: `translate(${-viewBox.x}px, ${-viewBox.y}px) scale(${viewBox.scale})`}}
        >
          <svg ref={svgRef} className='connection'>
            {connections.map(renderConnection)}
            {flowParticles.map(renderPracticle)}
          </svg>

          {nodes.map(renderNode)}
        </div>
      </div>
    </div>
  );
};

export default FlowDiagram;
