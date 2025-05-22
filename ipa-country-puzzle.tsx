import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';

const IPACountryPuzzle = () => {
  const mountRef = useRef(null);
  const [language, setLanguage] = useState('english');
  const [difficulty, setDifficulty] = useState('medium');
  const [gameState, setGameState] = useState('setup'); // 'setup', 'playing', 'complete'
  const [score, setScore] = useState(0);
  const [piecesPlaced, setPiecesPlaced] = useState(0);
  const [totalPieces, setTotalPieces] = useState(0);
  
  // Example IPA symbols for demo purposes
  const ipaSymbolsByLanguage = {
    english: ['æ', 'ð', 'ŋ', 'ʃ', 'θ', 'ʊ', 'ʒ', 'ə'],
    spanish: ['β', 'ɣ', 'ŋ', 'ɲ', 'r', 'ʎ', 'ʝ', 'x'],
    french: ['ɛ̃', 'œ̃', 'ɑ̃', 'ø', 'œ', 'ʁ', 'ɥ', 'ɲ'],
  };
  
  // Countries corresponding to languages - highly detailed and recognizable shapes
  const countryShapes = {
    english: [
      // UK outline - much more detailed and recognizable
      new THREE.Vector2(-0.1, 1.0),   // Northern Scotland
      new THREE.Vector2(-0.3, 0.9),
      new THREE.Vector2(-0.7, 0.8),   // Western Scotland
      new THREE.Vector2(-0.5, 0.6),   // Scotland inlet
      new THREE.Vector2(-0.8, 0.5),   // Scottish islands
      new THREE.Vector2(-0.6, 0.4),
      new THREE.Vector2(-0.3, 0.3),   // North Sea coast
      new THREE.Vector2(-0.4, 0.2),   // Northern England
      new THREE.Vector2(-0.7, 0.2),   // Irish Sea / Wales
      new THREE.Vector2(-0.5, 0),     // Wales
      new THREE.Vector2(-0.3, -0.1),  // Bristol Channel
      new THREE.Vector2(-0.6, -0.3),  // Cornwall
      new THREE.Vector2(-0.4, -0.4),  // South coast
      new THREE.Vector2(-0.1, -0.5),  // Southeast England
      new THREE.Vector2(0.2, -0.4),   // Kent
      new THREE.Vector2(0.3, -0.2),   // Thames Estuary
      new THREE.Vector2(0.1, 0),      // East Anglia
      new THREE.Vector2(0.2, 0.2),    // The Wash
      new THREE.Vector2(0, 0.4),      // Yorkshire
      new THREE.Vector2(-0.1, 0.7),   // Northeast England
      new THREE.Vector2(0.1, 0.9),    // Northern Scotland
    ],
    spanish: [
      // Spain outline - much more distinctive Iberian peninsula shape
      new THREE.Vector2(-0.9, 0.5),   // Northwest corner (Galicia)
      new THREE.Vector2(-0.8, 0.3),   // Northern coast
      new THREE.Vector2(-0.6, 0.4),   // Bay of Biscay
      new THREE.Vector2(-0.4, 0.5),   // Northern coast
      new THREE.Vector2(-0.2, 0.6),   // Pyrenees mountains
      new THREE.Vector2(0, 0.5),      // Catalonia
      new THREE.Vector2(0.2, 0.3),    // Barcelona coast
      new THREE.Vector2(0.4, 0.2),    // Valencia
      new THREE.Vector2(0.6, 0),      // Southeastern point (Murcia)
      new THREE.Vector2(0.5, -0.2),   // Almeria
      new THREE.Vector2(0.2, -0.3),   // Strait of Gibraltar
      new THREE.Vector2(0, -0.4),     // Southern point
      new THREE.Vector2(-0.3, -0.3),  // Cadiz/Huelva
      new THREE.Vector2(-0.6, -0.2),  // Portuguese border
      new THREE.Vector2(-0.8, 0),     // Portuguese border
      new THREE.Vector2(-0.9, 0.2),   // Northwest/Portuguese border
    ],
    french: [
      // France outline - clearly showing the "hexagon" shape France is known for
      new THREE.Vector2(-0.7, 0.5),   // Brittany peninsula
      new THREE.Vector2(-0.9, 0.4),   // Western Brittany
      new THREE.Vector2(-0.8, 0.2),   // Loire estuary
      new THREE.Vector2(-0.6, 0),     // Western coast
      new THREE.Vector2(-0.4, -0.2),  // Bordeaux/Aquitaine
      new THREE.Vector2(-0.3, -0.4),  // Pyrenees/Spanish border
      new THREE.Vector2(-0.1, -0.6),  // Mediterranean/Spanish border
      new THREE.Vector2(0.2, -0.5),   // Mediterranean coast
      new THREE.Vector2(0.5, -0.4),   // Southern France
      new THREE.Vector2(0.6, -0.2),   // Cote d'Azur/Italian border
      new THREE.Vector2(0.7, 0),      // Alps/Italian border
      new THREE.Vector2(0.6, 0.2),    // Swiss border
      new THREE.Vector2(0.5, 0.4),    // German border
      new THREE.Vector2(0.3, 0.5),    // Belgian border
      new THREE.Vector2(0.1, 0.6),    // English Channel
      new THREE.Vector2(-0.1, 0.5),   // Normandy
      new THREE.Vector2(-0.4, 0.6),   // English Channel coast
    ]
  };
  
  useEffect(() => {
    if (gameState !== 'playing') return;
    
    // Scene setup
    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    
    // Camera setup
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 5;
    
    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mountRef.current.appendChild(renderer.domElement);
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 10, 10);
    scene.add(directionalLight);
    
    // Simple camera controls implementation
    let cameraRotation = 0;
    let cameraDistance = 5;
    let cameraHeight = 0;
    
    const updateCameraPosition = () => {
      camera.position.x = Math.sin(cameraRotation) * cameraDistance;
      camera.position.z = Math.cos(cameraRotation) * cameraDistance;
      camera.position.y = cameraHeight;
      camera.lookAt(0, 0, 0);
    };
    
    // Initial camera position
    updateCameraPosition();
    
    // Country outline with better visual appearance
    // This is now just a guide - removed the filled shape since pieces will form it
    
    // Create country shape divided into puzzle pieces
    const shape = countryShapes[language];
    const shapeBounds = new THREE.Box2();
    shape.forEach(point => shapeBounds.expandByPoint(point));
    
    // Calculate piece dimensions based on country shape
    const shapeWidth = shapeBounds.max.x - shapeBounds.min.x;
    const shapeHeight = shapeBounds.max.y - shapeBounds.min.y;
    
    // Calculate number of pieces based on difficulty
    const difficultyFactors = { easy: 4, medium: 6, hard: 8 };
    const pieceCount = difficultyFactors[difficulty];
    setTotalPieces(pieceCount);
    
    // Create a grid of points within the shape to use as piece centers
    const gridSize = Math.ceil(Math.sqrt(pieceCount));
    const cellWidth = shapeWidth / gridSize;
    const cellHeight = shapeHeight / gridSize;
    
    // Create a faint outline of the entire country as a guide with improved visibility
    const outlineMaterial = new THREE.LineBasicMaterial({ 
      color: 0x004499, 
      linewidth: 3, 
      transparent: true, 
      opacity: 0.5 
    });
    const outlineGeometry = new THREE.BufferGeometry();
    const points = [];
    
    // Create a closed loop of points for the outline
    for (let i = 0; i < shape.length; i++) {
      const point = shape[i];
      points.push(new THREE.Vector3(point.x, point.y, -0.09)); // Slightly behind the pieces
    }
    // Close the loop by adding the first point again
    if (shape.length > 0) {
      const firstPoint = shape[0];
      points.push(new THREE.Vector3(firstPoint.x, firstPoint.y, -0.09));
    }
    
    outlineGeometry.setFromPoints(points);
    const outlineMesh = new THREE.Line(outlineGeometry, outlineMaterial);
    scene.add(outlineMesh);
    
    // Add a semi-transparent country shape for better visibility
    const countryShapeGeometry = new THREE.ShapeGeometry(new THREE.Shape(shape));
    const countryShapeMaterial = new THREE.MeshBasicMaterial({
      color: 0xaaccff,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide,
    });
    const countryShapeMesh = new THREE.Mesh(countryShapeGeometry, countryShapeMaterial);
    countryShapeMesh.position.z = -0.1; // Behind the pieces but in front of the outline
    scene.add(countryShapeMesh);
    
    // Create adjacency map for puzzle pieces
    const pieceAdjacency = [];
    for (let i = 0; i < pieceCount; i++) {
      pieceAdjacency[i] = [];
      const row = Math.floor(i / gridSize);
      const col = i % gridSize;
      
      // Check adjacent pieces (right, left, top, bottom)
      // Right neighbor
      if (col < gridSize - 1 && i + 1 < pieceCount) {
        pieceAdjacency[i].push(i + 1);
      }
      // Left neighbor
      if (col > 0) {
        pieceAdjacency[i].push(i - 1);
      }
      // Bottom neighbor
      if (row < Math.floor((pieceCount - 1) / gridSize) && i + gridSize < pieceCount) {
        pieceAdjacency[i].push(i + gridSize);
      }
      // Top neighbor
      if (row > 0) {
        pieceAdjacency[i].push(i - gridSize);
      }
    }
    
    // Generate country outline shape
    const countryPath = new THREE.Path();
    if (shape.length > 0) {
      countryPath.moveTo(shape[0].x, shape[0].y);
      for (let i = 1; i < shape.length; i++) {
        countryPath.lineTo(shape[i].x, shape[i].y);
      }
      countryPath.closePath();
    }
    
    // Function to create floating symbols
    const createSymbolPlaceholder = (symbolText, position) => {
      // Create a simple 2D plane with the IPA symbol
      const geometry = new THREE.PlaneGeometry(0.8, 0.8);
      
      // Create canvas for the symbol
      const canvas = document.createElement('canvas');
      canvas.width = 512;
      canvas.height = 512;
      const ctx = canvas.getContext('2d');
      
      // Fill with white background
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, 512, 512);
      
      // Draw black border
      ctx.strokeStyle = 'black';
      ctx.lineWidth = 20;
      ctx.strokeRect(20, 20, 472, 472);
      
      // Draw the IPA symbol
      ctx.fillStyle = 'black';
      ctx.font = 'bold 300px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(symbolText, 256, 256);
      
      // Create texture from canvas
      const texture = new THREE.CanvasTexture(canvas);
      const material = new THREE.MeshBasicMaterial({
        map: texture,
        side: THREE.DoubleSide
      });
      
      // Create mesh
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(position.x, position.y, 0.3); // Position above everything else
      
      return mesh;
    };
    
    // Initialize the pieces array
    const pieces = [];
    
    // Array to store symbol meshes
    const symbolMeshes = [];
    
    // Create floating IPA symbols for each puzzle location BEFORE creating pieces
    // This ensures the symbols are visible regardless of piece rendering issues
    const symbolPositions = [];
    
    for (let i = 0; i < pieceCount; i++) {
      // Calculate position within the country shape
      const col = i % gridSize;
      const row = Math.floor(i / gridSize);
      const centerX = shapeBounds.min.x + (col + 0.5) * cellWidth;
      const centerY = shapeBounds.min.y + (row + 0.5) * cellHeight;
      
      symbolPositions.push({
        index: i,
        x: centerX,
        y: centerY,
        symbol: ipaSymbolsByLanguage[language][i % ipaSymbolsByLanguage[language].length]
      });
    }
    
    // Add floating symbols for each valid position
    symbolPositions.forEach(pos => {
      // Simple test to see if position is within country shape
      const testPoint = new THREE.Vector2(pos.x, pos.y);
      
      // Check if point is inside the country path
      let pointInPath = false;
      for (let i = 0, j = shape.length - 1; i < shape.length; j = i++) {
        if (((shape[i].y > testPoint.y) !== (shape[j].y > testPoint.y)) &&
            (testPoint.x < (shape[j].x - shape[i].x) * (testPoint.y - shape[i].y) / (shape[j].y - shape[i].y) + shape[i].x)) {
          pointInPath = !pointInPath;
        }
      }
      
      if (pointInPath) {
        const symbolMesh = createSymbolPlaceholder(pos.symbol, {x: pos.x, y: pos.y});
        symbolMeshes.push({
          mesh: symbolMesh,
          targetX: pos.x,
          targetY: pos.y,
          index: pos.index,
          placed: false
        });
        scene.add(symbolMesh);
      }
    });
    
    // Add visual feedback effect for correctly positioned pieces
    const addGlowEffect = (piece) => {
      // Create a highlight effect when a piece is correctly placed
      const pieceGeometry = piece.geometry.clone();
      const glowMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ff00,
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide
      });
      
      const glowMesh = new THREE.Mesh(pieceGeometry, glowMaterial);
      glowMesh.position.z = -0.05; // Slightly behind the piece
      glowMesh.scale.set(1.05, 1.05, 1.05); // Slightly larger than the piece
      
      piece.add(glowMesh);
      piece.userData.glowEffect = glowMesh;
      
      return glowMesh;
    };
    
    // Function to check if pieces can connect and snap together
    const checkConnections = (piece) => {
      if (!piece.userData.isPlaced) return;
      
      // Check connections with adjacent pieces
      piece.userData.adjacentPieces.forEach(adjIndex => {
        const adjPiece = pieces[adjIndex];
        
        if (adjPiece && adjPiece.userData.isPlaced) {
          // Calculate distance between pieces
          const distance = Math.sqrt(
            Math.pow(piece.position.x - adjPiece.position.x, 2) +
            Math.pow(piece.position.y - adjPiece.position.y, 2)
          );
          
          // If they're close enough to their correct positions relative to each other
          const expectedDistance = Math.sqrt(
            Math.pow(cellWidth * (piece.userData.gridCol - adjPiece.userData.gridCol), 2) +
            Math.pow(cellHeight * (piece.userData.gridRow - adjPiece.userData.gridRow), 2)
          );
          
          if (Math.abs(distance - expectedDistance) < 0.3) {
            // Visual feedback to show connection
            if (!piece.userData.glowEffect) {
              addGlowEffect(piece);
            }
            if (!adjPiece.userData.glowEffect) {
              addGlowEffect(adjPiece);
            }
            
            // Add to connection graph (for potential group movement)
            if (!piece.userData.group) {
              if (!adjPiece.userData.group) {
                // Create a new group
                const group = { pieces: [piece, adjPiece] };
                piece.userData.group = group;
                adjPiece.userData.group = group;
              } else {
                // Add to existing group
                adjPiece.userData.group.pieces.push(piece);
                piece.userData.group = adjPiece.userData.group;
              }
            } else if (!adjPiece.userData.group) {
              // Add adjacent piece to this piece's group
              piece.userData.group.pieces.push(adjPiece);
              adjPiece.userData.group = piece.userData.group;
            } else if (piece.userData.group !== adjPiece.userData.group) {
              // Merge groups
              const group1 = piece.userData.group;
              const group2 = adjPiece.userData.group;
              
              // Add all pieces from group2 to group1
              group2.pieces.forEach(p => {
                if (!group1.pieces.includes(p)) {
                  group1.pieces.push(p);
                  p.userData.group = group1;
                }
              });
            }
          }
        }
      });
    };
    
    // Add magnetic attraction effect between adjacent pieces
    const applyMagneticAttraction = (piece) => {
      if (!piece || !piece.userData.isPlaced) return;
      
      // Check for nearby pieces that should connect
      let hasAttraction = false;
      
      piece.userData.adjacentPieces.forEach(adjIndex => {
        const adjPiece = pieces[adjIndex];
        
        if (adjPiece && !adjPiece.userData.isPlaced) {
          // Calculate distance to adjacent piece
          const distance = Math.sqrt(
            Math.pow(piece.position.x - adjPiece.position.x, 2) +
            Math.pow(piece.position.y - adjPiece.position.y, 2)
          );
          
          // Apply magnetic attraction if within range
          if (distance < 1.5) {
            // Calculate attraction force (stronger as pieces get closer)
            const attractionStrength = 0.02 * (1.5 - distance);
            
            // Move the non-placed piece toward its proper position relative to the placed piece
            const expectedX = piece.position.x + cellWidth * (adjPiece.userData.gridCol - piece.userData.gridCol);
            const expectedY = piece.position.y + cellHeight * (adjPiece.userData.gridRow - piece.userData.gridRow);
            
            adjPiece.position.x += (expectedX - adjPiece.position.x) * attractionStrength;
            adjPiece.position.y += (expectedY - adjPiece.position.y) * attractionStrength;
            
            // Also move the symbol
            const adjSymbol = symbolMeshes.find(sm => sm.index === adjIndex);
            if (adjSymbol) {
              adjSymbol.mesh.position.x = adjPiece.position.x;
              adjSymbol.mesh.position.y = adjPiece.position.y;
            }
            
            hasAttraction = true;
            
            // If very close to correct position, snap into place
            if (distance < 0.5) {
              adjPiece.position.x = expectedX;
              adjPiece.position.y = expectedY;
              adjPiece.userData.isPlaced = true;
              
              // Update score and placed pieces count
              setScore(prevScore => prevScore + 100);
              setPiecesPlaced(prevCount => {
                const newCount = prevCount + 1;
                if (newCount === totalPieces) {
                  // Game complete
                  setTimeout(() => setGameState('complete'), 1000);
                }
                return newCount;
              });
              
              // Check for new connections with this newly placed piece
              checkConnections(adjPiece);
            }
          }
        }
      });
      
      // Add visual hint for magnetic attraction
      if (hasAttraction && !piece.userData.isAttracting) {
        piece.userData.isAttracting = true;
        piece.userData.originalColor = piece.material.color.clone();
        piece.material.color.set(0x88aaff);  // Subtle blue hint
        
        // Reset color after a short time
        setTimeout(() => {
          if (piece.userData.originalColor) {
            piece.material.color.copy(piece.userData.originalColor);
          }
          piece.userData.isAttracting = false;
        }, 300);
      }
    };
    
    // Generate puzzle pieces that actually form the country shape
    for (let i = 0; i < pieceCount; i++) {
      // Calculate position within the country shape grid
      const col = i % gridSize;
      const row = Math.floor(i / gridSize);
      
      // Map grid position to country shape coordinates
      const centerX = shapeBounds.min.x + (col + 0.5) * cellWidth;
      const centerY = shapeBounds.min.y + (row + 0.5) * cellHeight;
      
      // Create piece shape - determined by its position in the country
      const pieceShape = new THREE.Shape();
      
      // Calculate corners of this cell in the grid
      const x0 = shapeBounds.min.x + col * cellWidth;
      const y0 = shapeBounds.min.y + row * cellHeight;
      const x1 = x0 + cellWidth;
      const y1 = y0 + cellHeight;
      
      // Make the edges slightly irregular for a puzzle-like appearance
      const jitter = 0.05; // Amount of irregularity
      const tabDepth = cellWidth * 0.15; // Size of the puzzle "tabs"
      
      // Create tabs/indents on the edges
      const hasRightTab = col < gridSize - 1 && i + 1 < pieceCount;
      const hasBottomTab = row < Math.floor((pieceCount - 1) / gridSize) && i + gridSize < pieceCount;
      const hasLeftTab = col > 0;
      const hasTopTab = row > 0;
      
      // Create an array of points for this puzzle piece with tabs
      const piecePoints = [];
      
      // Top left corner
      piecePoints.push(new THREE.Vector2(
        x0 + (Math.random() - 0.5) * jitter, 
        y0 + (Math.random() - 0.5) * jitter
      ));
      
      // Top edge with possible tab
      if (hasTopTab) {
        const midX = (x0 + x1) / 2;
        piecePoints.push(new THREE.Vector2(midX - tabDepth, y0));
        piecePoints.push(new THREE.Vector2(midX, y0 - tabDepth)); // Tab sticking out
        piecePoints.push(new THREE.Vector2(midX + tabDepth, y0));
      }
      
      // Top right corner
      piecePoints.push(new THREE.Vector2(
        x1 + (Math.random() - 0.5) * jitter, 
        y0 + (Math.random() - 0.5) * jitter
      ));
      
      // Right edge with possible tab
      if (hasRightTab) {
        const midY = (y0 + y1) / 2;
        piecePoints.push(new THREE.Vector2(x1, midY - tabDepth));
        piecePoints.push(new THREE.Vector2(x1 + tabDepth, midY)); // Tab sticking out
        piecePoints.push(new THREE.Vector2(x1, midY + tabDepth));
      }
      
      // Bottom right corner
      piecePoints.push(new THREE.Vector2(
        x1 + (Math.random() - 0.5) * jitter, 
        y1 + (Math.random() - 0.5) * jitter
      ));
      
      // Bottom edge with possible tab
      if (hasBottomTab) {
        const midX = (x0 + x1) / 2;
        piecePoints.push(new THREE.Vector2(midX + tabDepth, y1));
        piecePoints.push(new THREE.Vector2(midX, y1 + tabDepth)); // Tab sticking out
        piecePoints.push(new THREE.Vector2(midX - tabDepth, y1));
      }
      
      // Bottom left corner
      piecePoints.push(new THREE.Vector2(
        x0 + (Math.random() - 0.5) * jitter, 
        y1 + (Math.random() - 0.5) * jitter
      ));
      
      // Left edge with possible tab
      if (hasLeftTab) {
        const midY = (y0 + y1) / 2;
        piecePoints.push(new THREE.Vector2(x0, midY + tabDepth));
        piecePoints.push(new THREE.Vector2(x0 - tabDepth, midY)); // Tab sticking out
        piecePoints.push(new THREE.Vector2(x0, midY - tabDepth));
      }
      
      // Create the shape from the points
      pieceShape.moveTo(piecePoints[0].x, piecePoints[0].y);
      for (let j = 1; j < piecePoints.length; j++) {
        pieceShape.lineTo(piecePoints[j].x, piecePoints[j].y);
      }
      pieceShape.closePath();
      
      // Check if this grid cell actually intersects with the country shape
      // Skip if this piece falls outside the country shape
      const cellBounds = new THREE.Box2(
        new THREE.Vector2(x0, y0),
        new THREE.Vector2(x1, y1)
      );
      let isInsideCountry = false;
      
      // Simple method: if center point is inside the country path, include this piece
      const testPoint = new THREE.Vector2(centerX, centerY);
      
      // Very basic inside/outside test using ray casting
      let pointInPath = false;
      for (let i = 0, j = shape.length - 1; i < shape.length; j = i++) {
        if (((shape[i].y > testPoint.y) !== (shape[j].y > testPoint.y)) &&
            (testPoint.x < (shape[j].x - shape[i].x) * (testPoint.y - shape[i].y) / (shape[j].y - shape[i].y) + shape[i].x)) {
          pointInPath = !pointInPath;
        }
      }
      
      // Only create pieces that are within the country shape
      if (pointInPath) {
        const extrudeSettings = {
          depth: 0.2,
          bevelEnabled: true,
          bevelThickness: 0.05,
          bevelSize: 0.05,
          bevelSegments: 3
        };
        
        const pieceGeometry = new THREE.ExtrudeGeometry(pieceShape, extrudeSettings);
        
        // Create material with random color
        const pieceMaterial = new THREE.MeshStandardMaterial({
          color: new THREE.Color(0.5 + Math.random() * 0.5, 0.5 + Math.random() * 0.5, 0.5 + Math.random() * 0.5),
          metalness: 0.2,
          roughness: 0.5
        });
        
        const pieceMesh = new THREE.Mesh(pieceGeometry, pieceMaterial);
        
        // For demo, randomly place pieces off to the side
        pieceMesh.position.set(
          -5 + Math.random() * 2,  // Random position to the left
          -2 + Math.random() * 4,  // Random vertical position
          0.2                      // Slightly in front of the country outline
        );
        
        // Store target position for drag & drop and connectivity info
        pieceMesh.userData = {
          targetX: centerX,
          targetY: centerY,
          isPlaced: false,
          symbolIndex: i,
          adjacentPieces: pieceAdjacency[i],
          gridRow: row,
          gridCol: col,
          group: null,  // Will hold reference to connected group
          glowEffect: null // Will hold reference to glow effect
        };
        
        scene.add(pieceMesh);
        pieces.push(pieceMesh);
        
        // Also move the corresponding symbol to match this piece's initial position
        const symbolMesh = symbolMeshes.find(sm => sm.index === i);
        if (symbolMesh) {
          symbolMesh.mesh.position.x = pieceMesh.position.x;
          symbolMesh.mesh.position.y = pieceMesh.position.y;
        }
      }
    }
    
    // Setup raycaster for interaction
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let selectedPiece = null;
    let isDragging = false;
    
    // Event handlers
    const onMouseDown = (event) => {
      // Calculate mouse position in normalized device coordinates (-1 to +1)
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      
      // Update the picking ray with the camera and mouse position
      raycaster.setFromCamera(mouse, camera);
      
      // Find intersections
      const intersects = raycaster.intersectObjects(pieces);
      
      if (intersects.length > 0) {
        // Get the first piece that was clicked
        selectedPiece = intersects[0].object;
        isDragging = true;
      }
    };
    
    // Move symbol meshes when their corresponding pieces are moved
    const onMouseMove = (event) => {
      if (isDragging && selectedPiece) {
        // Calculate mouse position in normalized device coordinates
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        // Convert to world coordinates
        raycaster.setFromCamera(mouse, camera);
        const plane = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
        const point = new THREE.Vector3();
        raycaster.ray.intersectPlane(plane, point);
        
        // Move the piece to the mouse position
        selectedPiece.position.x = point.x;
        selectedPiece.position.y = point.y;
        
        // Move the corresponding symbol if it exists
        const selectedIndex = selectedPiece.userData.symbolIndex;
        const symbolMesh = symbolMeshes.find(sm => sm.index === selectedIndex);
        if (symbolMesh) {
          symbolMesh.mesh.position.x = point.x;
          symbolMesh.mesh.position.y = point.y;
        }
        
        // If this piece is part of a group, move the entire group
        if (selectedPiece.userData.isPlaced && selectedPiece.userData.group) {
          const deltaX = point.x - selectedPiece.userData.targetX;
          const deltaY = point.y - selectedPiece.userData.targetY;
          
          selectedPiece.userData.group.pieces.forEach(piece => {
            if (piece !== selectedPiece) {
              piece.position.x = piece.userData.targetX + deltaX;
              piece.position.y = piece.userData.targetY + deltaY;
              
              // Also move the symbol for this piece
              const pieceIndex = piece.userData.symbolIndex;
              const pieceSymbol = symbolMeshes.find(sm => sm.index === pieceIndex);
              if (pieceSymbol) {
                pieceSymbol.mesh.position.x = piece.position.x;
                pieceSymbol.mesh.position.y = piece.position.y;
              }
            }
          });
        }
      }
    };
    
    const onMouseUp = () => {
      if (isDragging && selectedPiece) {
        // Check if the piece is close to its target position
        const targetX = selectedPiece.userData.targetX;
        const targetY = selectedPiece.userData.targetY;
        const distance = Math.sqrt(
          Math.pow(selectedPiece.position.x - targetX, 2) +
          Math.pow(selectedPiece.position.y - targetY, 2)
        );
        
        // If close enough, snap to position
        if (distance < 0.5 && !selectedPiece.userData.isPlaced) {
          selectedPiece.position.x = targetX;
          selectedPiece.position.y = targetY;
          selectedPiece.userData.isPlaced = true;
          
          // Move the corresponding symbol to the target position
          const selectedIndex = selectedPiece.userData.symbolIndex;
          const symbolMesh = symbolMeshes.find(sm => sm.index === selectedIndex);
          if (symbolMesh) {
            symbolMesh.mesh.position.x = targetX;
            symbolMesh.mesh.position.y = targetY;
            symbolMesh.placed = true;
          }
          
          // Update score and placed pieces count
          setScore(prevScore => prevScore + 100);
          setPiecesPlaced(prevCount => {
            const newCount = prevCount + 1;
            if (newCount === totalPieces) {
              // Game complete
              setTimeout(() => setGameState('complete'), 1000);
            }
            return newCount;
          });
          
          // Check connections with adjacent pieces
          checkConnections(selectedPiece);
        }
      }
      
      // Reset
      isDragging = false;
      selectedPiece = null;
    };
    
    // Add keyboard controls for camera movement
    const onKeyDown = (event) => {
      switch(event.key) {
        case 'ArrowLeft':
          cameraRotation += 0.1;
          break;
        case 'ArrowRight':
          cameraRotation -= 0.1;
          break;
        case 'ArrowUp':
          cameraDistance = Math.max(3, cameraDistance - 0.5);
          break;
        case 'ArrowDown':
          cameraDistance = Math.min(10, cameraDistance + 0.5);
          break;
        case 'w':
          cameraHeight += 0.5;
          break;
        case 's':
          cameraHeight -= 0.5;
          break;
      }
      updateCameraPosition();
    };
    
    // Add mouse wheel event for zooming
    const onWheel = (event) => {
      event.preventDefault();
      // Adjust camera distance based on wheel direction
      if (event.deltaY > 0) {
        cameraDistance = Math.min(10, cameraDistance + 0.5);
      } else {
        cameraDistance = Math.max(3, cameraDistance - 0.5);
      }
      updateCameraPosition();
    };
    
    // Add event listeners
    renderer.domElement.addEventListener('mousedown', onMouseDown, false);
    renderer.domElement.addEventListener('mousemove', onMouseMove, false);
    renderer.domElement.addEventListener('mouseup', onMouseUp, false);
    renderer.domElement.addEventListener('wheel', onWheel);
    window.addEventListener('keydown', onKeyDown);
    
    // Update animation loop to apply magnetic attraction
    const animate = () => {
      requestAnimationFrame(animate);
      
      // Apply magnetic attraction for all placed pieces
      pieces.forEach(piece => {
        if (piece.userData.isPlaced && !isDragging) {
          applyMagneticAttraction(piece);
        }
      });
      
      renderer.render(scene, camera);
    };
    
    animate();
    
    // Cleanup
    return () => {
      if (mountRef.current && mountRef.current.contains(renderer.domElement)) {
        renderer.domElement.removeEventListener('mousedown', onMouseDown);
        renderer.domElement.removeEventListener('mousemove', onMouseMove);
        renderer.domElement.removeEventListener('mouseup', onMouseUp);
        renderer.domElement.removeEventListener('wheel', onWheel);
        window.removeEventListener('keydown', onKeyDown);
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, [language, difficulty, gameState, totalPieces]);
  
  const startGame = () => {
    setGameState('playing');
    setScore(0);
    setPiecesPlaced(0);
  };
  
  const resetGame = () => {
    setGameState('setup');
  };
  
  return (
    <div className="flex flex-col h-full">
      <div className="bg-blue-600 text-white p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">Interactive IPA Country Puzzle</h1>
        <div className="flex space-x-4">
          <div className="flex items-center">
            <span className="mr-2">Score:</span>
            <span className="font-bold">{score}</span>
          </div>
          <div className="flex items-center">
            <span className="mr-2">Pieces:</span>
            <span className="font-bold">{piecesPlaced}/{totalPieces}</span>
          </div>
        </div>
      </div>
      
      {gameState === 'setup' && (
        <div className="flex flex-col items-center justify-center flex-grow bg-gray-100 p-6">
          <div className="bg-white rounded-lg shadow-md p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-center mb-6">IPA Country Puzzle</h2>
            <p className="mb-6 text-gray-700">
              Assemble the puzzle pieces to create the country shape. Each piece contains an IPA symbol from the language of that country.
            </p>
            
            <div className="mb-4">
              <label className="block text-gray-700 mb-2 font-semibold">Select Language/Country:</label>
              <select 
                className="w-full p-2 border rounded"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="english">English (United Kingdom)</option>
                <option value="spanish">Spanish (Spain)</option>
                <option value="french">French (France)</option>
              </select>
            </div>
            
            <div className="mb-4">
              <div className="grid grid-cols-3 gap-2 mt-2">
                <div 
                  className={`${language === 'english' ? 'border-2 border-blue-500 bg-blue-50' : 'border'} p-2 rounded text-center cursor-pointer hover:bg-gray-50`}
                  onClick={() => setLanguage('english')}
                >
                  <div className="text-xl mb-1">🇬🇧</div>
                  <div className="font-medium">United Kingdom</div>
                </div>
                <div 
                  className={`${language === 'spanish' ? 'border-2 border-blue-500 bg-blue-50' : 'border'} p-2 rounded text-center cursor-pointer hover:bg-gray-50`}
                  onClick={() => setLanguage('spanish')}
                >
                  <div className="text-xl mb-1">🇪🇸</div>
                  <div className="font-medium">Spain</div>
                </div>
                <div 
                  className={`${language === 'french' ? 'border-2 border-blue-500 bg-blue-50' : 'border'} p-2 rounded text-center cursor-pointer hover:bg-gray-50`}
                  onClick={() => setLanguage('french')}
                >
                  <div className="text-xl mb-1">🇫🇷</div>
                  <div className="font-medium">France</div>
                </div>
              </div>
            </div>
            
            <div className="mb-6">
              <label className="block text-gray-700 mb-2">Difficulty:</label>
              <select 
                className="w-full p-2 border rounded"
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <option value="easy">Easy (4 pieces)</option>
                <option value="medium">Medium (6 pieces)</option>
                <option value="hard">Hard (8 pieces)</option>
              </select>
            </div>
            
            <button 
              className="w-full bg-blue-600 text-white rounded-lg py-3 font-bold hover:bg-blue-700 transition"
              onClick={startGame}
            >
              Start Game
            </button>
          </div>
        </div>
      )}
      
      {gameState === 'playing' && (
        <div 
          ref={mountRef} 
          className="flex-grow"
          style={{ width: '100%', height: '500px' }}
        ></div>
      )}
      
      {gameState === 'complete' && (
        <div className="flex flex-col items-center justify-center flex-grow bg-gray-100 p-6">
          <div className="bg-white rounded-lg shadow-md p-6 w-full max-w-md text-center">
            <h2 className="text-2xl font-bold mb-4">Puzzle Complete!</h2>
            <p className="text-xl mb-4">Your Score: {score}</p>
            <p className="mb-6">You've successfully assembled all IPA symbols for {language}!</p>
            
            <button 
              className="w-full bg-blue-600 text-white rounded-lg py-3 font-bold hover:bg-blue-700 transition"
              onClick={resetGame}
            >
              Play Again
            </button>
          </div>
        </div>
      )}
      
      <div className="bg-gray-200 p-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-bold">Instructions:</h3>
            <p>Drag and drop the puzzle pieces to form the country shape. The IPA symbols appear directly on each puzzle piece!</p>
            <p><span className="text-blue-600 font-bold">✦ Features:</span> Pieces attract each other magnetically when they're close to the correct position!</p>
            {gameState === 'playing' && (
              <p className="mt-2 text-sm">
                <strong>Camera Controls:</strong> Use arrow keys to rotate and zoom. Use W/S keys to move up/down. Mouse wheel to zoom in/out.
              </p>
            )}
          </div>
          
          {gameState === 'playing' && (
            <button 
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition"
              onClick={resetGame}
            >
              Reset
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default IPACountryPuzzle;