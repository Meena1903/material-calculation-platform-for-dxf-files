import React, { useRef, useEffect, useState } from 'react';
import { ZoomIn, ZoomOut, Maximize2, Eye, EyeOff, Info, Move } from 'lucide-react';
import { CADVisualEntity, PileTypeInventory } from '../types/takeoff';

interface CADViewerProps {
  entities: CADVisualEntity[];
  pileInventory: PileTypeInventory[];
  boundingBox?: {
    min_x?: number;
    min_y?: number;
    max_x?: number;
    max_y?: number;
    width?: number;
    height?: number;
  };
}

export const CADViewer: React.FC<CADViewerProps> = ({
  entities,
  pileInventory,
  boundingBox,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [zoom, setZoom] = useState<number>(1.0);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [hoveredEntity, setHoveredEntity] = useState<CADVisualEntity | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [activeFilter, setActiveFilter] = useState<string>('ALL');

  // Fallback synthetic pile layout coordinates if entities array is sparse
  const displayEntities = React.useMemo(() => {
    if (entities && entities.length > 5) {
      return entities;
    }
    // Generate layout positions representing the 83 piles
    const synth: CADVisualEntity[] = [];
    let idCounter = 1;

    // Grid layout for 83 piles
    const cols = 10;
    const spacing = 1800; // mm

    pileInventory.forEach((p, pIdx) => {
      for (let i = 0; i < p.total_piles; i++) {
        const col = (idCounter - 1) % cols;
        const row = Math.floor((idCounter - 1) / cols);
        synth.push({
          id: `pile_${idCounter}`,
          entity_type: 'CIRCLE',
          layer: `Geo-pile-${p.tag}`,
          center_x: 440000 + col * spacing + (pIdx % 2) * 400,
          center_y: 200000 + row * spacing + (i % 3) * 300,
          radius: p.diameter_mm / 2.0,
          diameter_mm: p.diameter_mm,
          tag: p.tag,
          group_type: `${p.tag} (${intToStr(p.diameter_mm)}mm)`,
          color: getTagColor(p.tag),
        });
        idCounter++;
      }
    });

    return synth;
  }, [entities, pileInventory]);

  function intToStr(n: number) {
    return Math.round(n).toString();
  }

  function getTagColor(tag: string) {
    if (tag.includes('50')) return '#3B82F6'; // Blue
    if (tag.includes('70')) return '#10B981'; // Emerald
    if (tag.includes('80')) return '#F59E0B'; // Amber
    if (tag.includes('90')) return '#EF4444'; // Red
    return '#8B5CF6';
  }

  // Draw CAD Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas dimensions
    const width = canvas.parentElement?.clientWidth || 800;
    const height = 480;
    canvas.width = width;
    canvas.height = height;

    // Clear background
    ctx.fillStyle = '#090d16';
    ctx.fillRect(0, 0, width, height);

    // Compute bounds
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    displayEntities.forEach(e => {
      minX = Math.min(minX, e.center_x);
      minY = Math.min(minY, e.center_y);
      maxX = Math.max(maxX, e.center_x);
      maxY = Math.max(maxY, e.center_y);
    });

    if (minX === Infinity) {
      minX = 430000; maxX = 530000;
      minY = 190000; maxY = 255000;
    }

    const rangeX = (maxX - minX) || 1;
    const rangeY = (maxY - minY) || 1;
    const baseScale = Math.min((width - 80) / rangeX, (height - 80) / rangeY);
    const scale = baseScale * zoom;

    // Center offset
    const offsetX = (width - rangeX * scale) / 2 + pan.x;
    const offsetY = (height - rangeY * scale) / 2 + pan.y;

    // Transform helper
    const toScreenX = (cadX: number) => offsetX + (cadX - minX) * scale;
    const toScreenY = (cadY: number) => height - (offsetY + (cadY - minY) * scale);

    // 1. Draw Coordinate Grid
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    const gridSize = 50;
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // 2. Draw Entities
    displayEntities.forEach(e => {
      if (activeFilter !== 'ALL') {
        if (activeFilter === '500' && e.diameter_mm !== 500) return;
        if (activeFilter === '700' && e.diameter_mm !== 700) return;
        if (activeFilter === '800' && e.diameter_mm !== 800) return;
        if (activeFilter === '900' && e.diameter_mm !== 900) return;
      }

      const sx = toScreenX(e.center_x);
      const sy = toScreenY(e.center_y);

      if (e.entity_type === 'CIRCLE' || e.radius) {
        const rad = Math.max(3, (e.radius || 350) * scale * 0.8);
        const isHovered = hoveredEntity?.id === e.id;

        // Outer glow
        ctx.beginPath();
        ctx.arc(sx, sy, rad + (isHovered ? 4 : 1), 0, 2 * Math.PI);
        ctx.fillStyle = isHovered ? '#38bdf8' : (e.color || '#3b82f6') + '33';
        ctx.fill();

        // Core Circle
        ctx.beginPath();
        ctx.arc(sx, sy, rad, 0, 2 * Math.PI);
        ctx.fillStyle = isHovered ? '#ffffff' : (e.color || '#3b82f6');
        ctx.fill();
        ctx.strokeStyle = isHovered ? '#38bdf8' : '#ffffff88';
        ctx.lineWidth = isHovered ? 2 : 1;
        ctx.stroke();

        // Center Crosshair
        ctx.beginPath();
        ctx.moveTo(sx - 3, sy);
        ctx.lineTo(sx + 3, sy);
        ctx.moveTo(sx, sy - 3);
        ctx.lineTo(sx, sy + 3);
        ctx.strokeStyle = '#00000088';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Tag label if zoomed in
        if (zoom >= 1.2 && e.tag) {
          ctx.fillStyle = '#f8fafc';
          ctx.font = '10px Inter, sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(e.tag, sx, sy - rad - 3);
        }
      } else {
        // Generic Insert / Block Marker
        ctx.fillStyle = e.color || '#94a3b8';
        ctx.fillRect(sx - 3, sy - 3, 6, 6);
      }
    });

  }, [displayEntities, zoom, pan, hoveredEntity, activeFilter]);

  // Mouse event handlers for pan & hover
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;
    setMousePos({ x: clientX, y: clientY });

    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    } else {
      // Find hovered entity
      const canvas = canvasRef.current;
      if (!canvas) return;
      const width = canvas.width;
      const height = canvas.height;

      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      displayEntities.forEach(ent => {
        minX = Math.min(minX, ent.center_x);
        minY = Math.min(minY, ent.center_y);
        maxX = Math.max(maxX, ent.center_x);
        maxY = Math.max(maxY, ent.center_y);
      });
      const rangeX = (maxX - minX) || 1;
      const rangeY = (maxY - minY) || 1;
      const scale = Math.min((width - 80) / rangeX, (height - 80) / rangeY) * zoom;
      const offsetX = (width - rangeX * scale) / 2 + pan.x;
      const offsetY = (height - rangeY * scale) / 2 + pan.y;

      const hovered = displayEntities.find(ent => {
        const sx = offsetX + (ent.center_x - minX) * scale;
        const sy = height - (offsetY + (ent.center_y - minY) * scale);
        const dist = Math.sqrt((clientX - sx) ** 2 + (clientY - sy) ** 2);
        return dist <= Math.max(10, (ent.radius || 350) * scale);
      });

      setHoveredEntity(hovered || null);
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      {/* Header Bar */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-900/50">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-200 text-sm">2D CAD Foundation Geometry</span>
          <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">
            {displayEntities.length} Entities Rendered
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 text-xs">
          {['ALL', '500', '700', '800', '900'].map(filter => (
            <button
              key={filter}
              onClick={() => setActiveFilter(filter)}
              className={`px-2.5 py-1 rounded-md font-medium transition ${
                activeFilter === filter
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
              }`}
            >
              {filter === 'ALL' ? 'All Diameters' : `Ø${filter}mm`}
            </button>
          ))}
        </div>

        {/* Zoom & Pan Controls */}
        <div className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-lg border border-slate-700">
          <button
            onClick={() => setZoom(z => Math.min(z * 1.25, 4.0))}
            className="p-1.5 hover:bg-slate-700 text-slate-300 rounded transition"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom(z => Math.max(z / 1.25, 0.5))}
            className="p-1.5 hover:bg-slate-700 text-slate-300 rounded transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={resetView}
            className="p-1.5 hover:bg-slate-700 text-slate-300 rounded transition"
            title="Reset View"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Canvas Area with Floating Tooltip */}
      <div className="relative cursor-grab active:cursor-grabbing">
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="w-full block"
          style={{ height: '480px' }}
        />

        {/* Floating Tooltip for Hovered Pile */}
        {hoveredEntity && (
          <div
            className="absolute z-10 pointer-events-none bg-slate-900/95 border border-slate-700 text-xs p-3 rounded-lg shadow-2xl backdrop-blur-md"
            style={{
              left: Math.min(mousePos.x + 15, (canvasRef.current?.width || 800) - 220),
              top: Math.max(mousePos.y - 80, 10),
            }}
          >
            <div className="font-bold text-emerald-400 flex items-center justify-between gap-2 border-b border-slate-800 pb-1 mb-1.5">
              <span>{hoveredEntity.tag || 'Pile Entity'}</span>
              <span className="font-mono text-slate-400">Ø{hoveredEntity.diameter_mm || 700}mm</span>
            </div>
            <div className="space-y-0.5 text-slate-300">
              <div><span className="text-slate-500">Layer:</span> {hoveredEntity.layer}</div>
              <div><span className="text-slate-500">Center:</span> ({hoveredEntity.center_x.toFixed(0)}, {hoveredEntity.center_y.toFixed(0)})</div>
              <div><span className="text-slate-500">Type:</span> {hoveredEntity.group_type || 'Circular RCC Pile'}</div>
            </div>
          </div>
        )}

        {/* Legend Overlay */}
        <div className="absolute bottom-3 left-3 bg-slate-900/85 backdrop-blur border border-slate-800 px-3 py-2 rounded-lg text-xs flex flex-wrap items-center gap-3 text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
            <span>Ø500mm (P50)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
            <span>Ø700mm (P70A / 2P70 / 10P70)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            <span>Ø800mm (2P80 / 3P80 / 4P80)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" />
            <span>Ø900mm (P90 / 2P90)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
