/**
 * Canvas Renderer - High-performance Canvas-based rendering
 * Implements Gemini's layered canvas architecture with HiDPI support
 */

console.log('📱 canvas_renderer.js loaded');

class CanvasRenderer extends BaseRenderer {
    constructor(container, options = {}) {
        super(container, options);
        
        this.layers = {};
        this.animationFrameId = null;
        this.needsRedraw = true;
        
        // Node rendering options
        this.nodeOptions = {
            minRadius: 4,
            maxRadius: 25,
            strokeWidth: 2,
            strokeColor: 'rgba(255, 255, 255, 0.8)',
            defaultColor: '#C0C0C0',
            ...options.nodeOptions
        };
    }
    
    /**
     * Initialize the Canvas renderer
     */
    initialize() {
        if (this.isInitialized) return;
        
        // Clear container
        this.container.innerHTML = '';
        
        // Create canvas layers (future-proof for multi-layer architecture)
        this.layers.nodes = this.createCanvasLayer('nodes-layer');
        
        // Setup resize observer
        this.setupResizeObserver();
        
        // Initial resize
        this.handleResize();
        
        this.isInitialized = true;
        
        if (this.options.debug) {
            console.log('CanvasRenderer: Initialized with layers:', Object.keys(this.layers));
        }
    }
    
    /**
     * Create a canvas layer with HiDPI support
     * @param {string} className - CSS class name for the canvas
     * @returns {Object} Object with canvas element and 2D context
     */
    createCanvasLayer(className) {
        const canvas = document.createElement('canvas');
        canvas.className = className;
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        
        this.container.appendChild(canvas);
        
        const ctx = canvas.getContext('2d');
        
        return { canvas, ctx };
    }
    
    /**
     * Setup resize observer for responsive canvas
     */
    setupResizeObserver() {
        if (typeof ResizeObserver !== 'undefined') {
            this.resizeObserver = new ResizeObserver(entries => {
                this.handleResize();
            });
            this.resizeObserver.observe(this.container);
        } else {
            // Fallback for older browsers
            window.addEventListener('resize', () => this.handleResize());
        }
    }
    
    /**
     * Handle container resize with HiDPI support
     */
    handleResize() {
        const rect = this.container.getBoundingClientRect();
        const dpr = this.options.enableHiDPI ? this.options.devicePixelRatio : 1;
        
        // Update options
        this.options.width = rect.width;
        this.options.height = rect.height;
        
        // Resize all canvas layers
        Object.values(this.layers).forEach(layer => {
            const { canvas, ctx } = layer;
            
            // Set actual canvas size (device pixels)
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            
            // Set CSS size (CSS pixels)
            canvas.style.width = `${rect.width}px`;
            canvas.style.height = `${rect.height}px`;
            
            // Scale context for HiDPI
            ctx.scale(dpr, dpr);
            
            // Set default rendering properties
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
        });
        
        this.needsRedraw = true;
        
        if (this.options.debug) {
            console.log(`CanvasRenderer: Resized to ${rect.width}x${rect.height} (DPR: ${dpr})`);
        }
    }
    
    /**
     * Update data and trigger redraw
     * @param {Array} nodes - Array of node objects
     * @param {Array} links - Array of link objects
     */
    updateData(nodes, links) {
        super.updateData(nodes, links);
        
        // Process nodes for rendering (add genre colors and sizes)
        this.processNodesForRendering();
        
        // Store links for edge rendering
        this.links = links || [];
        
        if (this.options.debug) {
            console.log(`CanvasRenderer: Updated with ${this.nodes.length} nodes, ${this.links.length} links`);
        }
        
        this.needsRedraw = true;
    }
    
    /**
     * Process nodes to add rendering properties
     */
    processNodesForRendering() {
        this.nodes.forEach(node => {
            // Classify genre and get color
            const genre = classifyArtistGenre(node);
            node.genre = genre;
            node.color = getGenreColor(genre);
            
            // Calculate radius based on listener count
            const listeners = node.listener_count || node.listeners || 1;
            const maxListeners = Math.max(...this.nodes.map(n => n.listener_count || n.listeners || 1));
            const minListeners = Math.min(...this.nodes.map(n => n.listener_count || n.listeners || 1));
            
            // Use square root scale for better visual perception
            const normalizedSize = Math.sqrt(listeners) / Math.sqrt(maxListeners);
            node.radius = this.lerp(this.nodeOptions.minRadius, this.nodeOptions.maxRadius, normalizedSize);
            
            // Add glow intensity based on personal play count
            const playCount = node.play_count || 0;
            const maxPlayCount = Math.max(...this.nodes.map(n => n.play_count || 0));
            node.glowIntensity = maxPlayCount > 0 ? (playCount / maxPlayCount) : 0;
            
            if (this.options.debug && Math.random() < 0.1) { // Debug 10% of nodes
                console.log(`Node ${node.name}: genre=${genre}, color=${node.color}, radius=${node.radius.toFixed(1)}`);
            }
        });
    }
    
    /**
     * Update zoom transform and trigger redraw
     * @param {Object} transform - D3 zoom transform {k, x, y}
     */
    updateTransform(transform) {
        super.updateTransform(transform);
        this.needsRedraw = true;
    }
    
    /**
     * Start the render loop
     */
    startRenderLoop() {
        if (this.animationFrameId) return; // Already running
        
        const renderFrame = () => {
            if (this.needsRedraw) {
                this.render();
                this.needsRedraw = false;
            }
            
            this.updateFPS();
            this.animationFrameId = requestAnimationFrame(renderFrame);
        };
        
        renderFrame();
    }
    
    /**
     * Stop the render loop
     */
    stopRenderLoop() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }
    
    /**
     * Render the visualization
     */
    render() {
        if (!this.isInitialized || !this.layers.nodes) return;
        
        const { ctx } = this.layers.nodes;
        const { width, height } = this.options;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Apply zoom transform
        ctx.save();
        ctx.translate(this.transform.x, this.transform.y);
        ctx.scale(this.transform.k, this.transform.k);
        
        // Render in proper order for visual layering
        this.renderEdges(ctx);  // Bottom layer
        this.renderNodes(ctx);  // Middle layer  
        this.renderLabels(ctx); // Top layer
        
        ctx.restore();
    }
    
    /**
     * Render all edges (Gemini's batched approach for performance)
     * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
     */
    renderEdges(ctx) {
        if (!this.links || this.links.length === 0) return;
        
        // Batch all edges into single path for performance
        ctx.beginPath();
        this.links.forEach(link => {
            // Handle D3 force link format (source/target can be objects or IDs)
            const source = typeof link.source === 'object' ? link.source : this.nodes.find(n => n.id === link.source);
            const target = typeof link.target === 'object' ? link.target : this.nodes.find(n => n.id === link.target);
            
            if (source && target && source.x !== undefined && source.y !== undefined && 
                target.x !== undefined && target.y !== undefined) {
                ctx.moveTo(source.x, source.y);
                ctx.lineTo(target.x, target.y);
            }
        });
        
        // Style edges based on weight (subtle white with varying opacity)
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.stroke();
    }
    
    /**
     * Render all nodes
     * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
     */
    renderNodes(ctx) {
        this.nodes.forEach(node => {
            if (!node.x || !node.y) return; // Skip nodes without positions
            
            const radius = node.radius || this.nodeOptions.minRadius;
            const color = node.color || this.nodeOptions.defaultColor;
            
            // Apply glow effect if node has high personal play count
            if (node.glowIntensity > 0.5) {
                ctx.shadowBlur = node.glowIntensity * 15;
                ctx.shadowColor = color;
            } else {
                ctx.shadowBlur = 0;
            }
            
            // Draw node
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
            ctx.fillStyle = color;
            ctx.fill();
            
            // Draw border
            ctx.beginPath();
            ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
            ctx.strokeStyle = this.nodeOptions.strokeColor;
            ctx.lineWidth = this.nodeOptions.strokeWidth;
            ctx.stroke();
            
            // Reset shadow
            ctx.shadowBlur = 0;
        });
    }
    
    /**
     * Render text labels for nodes (with zoom-based culling)
     * @param {CanvasRenderingContext2D} ctx - Canvas rendering context
     */
    renderLabels(ctx) {
        // Performance optimization: only render labels if zoomed in enough
        const minScale = 0.5; // Only show labels when zoom >= 50%
        if (this.transform.k < minScale) return;
        
        // Setup text rendering with comprehensive font stack for international support
        ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK JP", "Yu Gothic UI", "Meiryo", "Hiragino Sans", "MS Gothic", sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Add text shadow for better readability on colored backgrounds
        ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
        ctx.shadowBlur = 3;
        ctx.shadowOffsetX = 1;
        ctx.shadowOffsetY = 1;
        
        this.nodes.forEach(node => {
            if (!node.x || !node.y) return;
            
            // Performance culling: skip tiny nodes when zoomed out
            const apparentRadius = (node.radius || this.nodeOptions.minRadius) * this.transform.k;
            if (apparentRadius < 8) return; // Skip labels for very small nodes
            
            // Render artist name
            const label = node.name || node.id;
            ctx.fillText(label, node.x, node.y);
        });
        
        // Reset shadow
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
    }
    
    /**
     * Get node at screen coordinates (for interaction)
     * @param {number} x - Screen X coordinate
     * @param {number} y - Screen Y coordinate
     * @returns {Object|null} Node object or null if none found
     */
    getNodeAtPosition(x, y) {
        // Transform screen coordinates to canvas coordinates
        const canvasX = (x - this.transform.x) / this.transform.k;
        const canvasY = (y - this.transform.y) / this.transform.k;
        
        // Find closest node within radius
        for (const node of this.nodes) {
            if (!node.x || !node.y) continue;
            
            const dx = canvasX - node.x;
            const dy = canvasY - node.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const radius = node.radius || this.nodeOptions.minRadius;
            
            if (distance <= radius) {
                return node;
            }
        }
        
        return null;
    }
    
    /**
     * Force a redraw on next frame
     */
    invalidate() {
        this.needsRedraw = true;
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        super.destroy();
        
        this.stopRenderLoop();
        
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
        }
        
        // Clear container
        this.container.innerHTML = '';
        
        this.isInitialized = false;
    }
}