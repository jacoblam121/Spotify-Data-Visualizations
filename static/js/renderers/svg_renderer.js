/**
 * SVG Renderer - Legacy fallback using existing SVG approach
 * Wrapped in renderer abstraction for easy comparison
 */

class SVGRenderer extends BaseRenderer {
    constructor(container, options = {}) {
        super(container, options);
        
        this.svg = null;
        this.nodeGroup = null;
        this.linkGroup = null;
        this.colorScale = null;
        
        // SVG-specific options
        this.svgOptions = {
            nodeStrokeWidth: 2,
            nodeStrokeColor: 'white',
            linkOpacity: 0.6,
            linkColor: 'rgba(255, 255, 255, 0.5)',
            ...options.svgOptions
        };
    }
    
    /**
     * Initialize the SVG renderer
     */
    initialize() {
        if (this.isInitialized) return;
        
        // Clear container
        this.container.innerHTML = '';
        
        // Create SVG element
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .style('background', '#000000'); // Match Canvas black background
        
        // Create groups for organization
        this.linkGroup = this.svg.append('g').attr('class', 'links');
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
        
        // Setup resize handling
        this.handleResize();
        window.addEventListener('resize', () => this.handleResize());
        
        this.isInitialized = true;
        
        if (this.options.debug) {
            console.log('SVGRenderer: Initialized');
        }
    }
    
    /**
     * Handle container resize
     */
    handleResize() {
        const rect = this.container.getBoundingClientRect();
        this.options.width = rect.width;
        this.options.height = rect.height;
        
        if (this.svg) {
            this.svg
                .attr('width', rect.width)
                .attr('height', rect.height);
        }
        
        if (this.options.debug) {
            console.log(`SVGRenderer: Resized to ${rect.width}x${rect.height}`);
        }
    }
    
    /**
     * Update data and redraw
     * @param {Array} nodes - Array of node objects
     * @param {Array} links - Array of link objects
     */
    updateData(nodes, links) {
        super.updateData(nodes, links);
        
        // Process nodes for rendering
        this.processNodesForRendering();
        
        // Create color scale
        this.createColorScale();
        
        // Render
        this.render();
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
            
            // Use square root scale for better visual perception
            const normalizedSize = Math.sqrt(listeners) / Math.sqrt(maxListeners);
            node.radius = 4 + (normalizedSize * 21); // 4-25 pixel range
            
            // Add glow class for high personal play count
            const playCount = node.play_count || 0;
            const maxPlayCount = Math.max(...this.nodes.map(n => n.play_count || 0));
            node.shouldGlow = maxPlayCount > 0 && (playCount / maxPlayCount) > 0.5;
        });
    }
    
    /**
     * Create D3 color scale (for compatibility)
     */
    createColorScale() {
        const listeners = this.nodes.map(d => d.listener_count || d.listeners || 1);
        this.colorScale = d3.scaleSequential()
            .domain(d3.extent(listeners))
            .interpolator(d3.interpolateViridis);
    }
    
    /**
     * Update zoom transform
     * @param {Object} transform - D3 zoom transform {k, x, y}
     */
    updateTransform(transform) {
        super.updateTransform(transform);
        
        if (this.nodeGroup && this.linkGroup) {
            const transformStr = `translate(${transform.x},${transform.y}) scale(${transform.k})`;
            this.nodeGroup.attr('transform', transformStr);
            this.linkGroup.attr('transform', transformStr);
        }
    }
    
    /**
     * Render the visualization
     */
    render() {
        if (!this.isInitialized || !this.svg) return;
        
        this.renderNodes();
        // Note: Links will be added in future subphases
    }
    
    /**
     * Render nodes using D3 data binding
     */
    renderNodes() {
        const nodes = this.nodeGroup
            .selectAll('circle')
            .data(this.nodes, d => d.id);
        
        // Remove old nodes
        nodes.exit().remove();
        
        // Add new nodes
        const newNodes = nodes.enter()
            .append('circle')
            .attr('class', 'node')
            .style('cursor', 'pointer');
        
        // Update all nodes (new and existing)
        const allNodes = newNodes.merge(nodes);
        
        allNodes
            .attr('r', d => d.radius)
            .attr('fill', d => d.color)
            .attr('stroke', this.svgOptions.nodeStrokeColor)
            .attr('stroke-width', this.svgOptions.nodeStrokeWidth)
            .classed('glow', d => d.shouldGlow)
            .attr('cx', d => d.x || 0)
            .attr('cy', d => d.y || 0);
        
        // Add glow effect styles if not already present
        this.addGlowStyles();
    }
    
    /**
     * Add CSS glow effects to SVG
     */
    addGlowStyles() {
        if (this.svg.select('defs').empty()) {
            const defs = this.svg.append('defs');
            
            // Create glow filter
            const filter = defs.append('filter')
                .attr('id', 'glow')
                .attr('x', '-50%')
                .attr('y', '-50%')
                .attr('width', '200%')
                .attr('height', '200%');
            
            filter.append('feGaussianBlur')
                .attr('stdDeviation', '3')
                .attr('result', 'coloredBlur');
            
            const merge = filter.append('feMerge');
            merge.append('feMergeNode').attr('in', 'coloredBlur');
            merge.append('feMergeNode').attr('in', 'SourceGraphic');
        }
        
        // Apply glow filter to glowing nodes
        this.nodeGroup.selectAll('.glow')
            .style('filter', 'url(#glow)');
    }
    
    /**
     * Get node at screen coordinates
     * @param {number} x - Screen X coordinate
     * @param {number} y - Screen Y coordinate
     * @returns {Object|null} Node object or null if none found
     */
    getNodeAtPosition(x, y) {
        // Transform screen coordinates
        const canvasX = (x - this.transform.x) / this.transform.k;
        const canvasY = (y - this.transform.y) / this.transform.k;
        
        // Find closest node
        for (const node of this.nodes) {
            if (!node.x || !node.y) continue;
            
            const dx = canvasX - node.x;
            const dy = canvasY - node.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance <= node.radius) {
                return node;
            }
        }
        
        return null;
    }
    
    /**
     * Update node positions (called by simulation tick)
     * @param {Array} nodes - Updated nodes with x,y positions
     */
    updateNodePositions(nodes) {
        this.nodeGroup.selectAll('circle')
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        super.destroy();
        
        if (this.svg) {
            this.svg.remove();
        }
        
        this.isInitialized = false;
    }
}