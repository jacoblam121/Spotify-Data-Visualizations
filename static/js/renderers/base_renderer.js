/**
 * Base Renderer - Abstract base class for all renderers
 * Implements Gemini's suggested renderer abstraction pattern
 */

class BaseRenderer {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            width: 800,
            height: 600,
            devicePixelRatio: window.devicePixelRatio || 1,
            enableHiDPI: true,
            debug: false,
            ...options
        };
        
        this.nodes = [];
        this.links = [];
        this.transform = { k: 1, x: 0, y: 0 }; // D3 zoom transform
        
        // Performance monitoring
        this.frameCount = 0;
        this.lastFPSUpdate = Date.now();
        this.currentFPS = 0;
        
        this.isInitialized = false;
    }
    
    /**
     * Initialize the renderer - must be implemented by subclasses
     */
    initialize() {
        throw new Error('initialize() must be implemented by subclass');
    }
    
    /**
     * Update data - must be implemented by subclasses
     * @param {Array} nodes - Array of node objects
     * @param {Array} links - Array of link objects
     */
    updateData(nodes, links) {
        this.nodes = nodes || [];
        this.links = links || [];
        
        if (this.options.debug) {
            console.log(`${this.constructor.name}: Updated data - ${this.nodes.length} nodes, ${this.links.length} links`);
        }
    }
    
    /**
     * Update zoom transform from D3 - must be implemented by subclasses
     * @param {Object} transform - D3 zoom transform {k, x, y}
     */
    updateTransform(transform) {
        this.transform = transform;
        
        if (this.options.debug) {
            console.log(`${this.constructor.name}: Transform updated - scale: ${transform.k.toFixed(2)}, translate: (${transform.x.toFixed(1)}, ${transform.y.toFixed(1)})`);
        }
    }
    
    /**
     * Render the visualization - must be implemented by subclasses
     */
    render() {
        throw new Error('render() must be implemented by subclass');
    }
    
    /**
     * Resize the renderer
     * @param {number} width - New width
     * @param {number} height - New height
     */
    resize(width, height) {
        this.options.width = width;
        this.options.height = height;
        
        if (this.options.debug) {
            console.log(`${this.constructor.name}: Resized to ${width}x${height}`);
        }
    }
    
    /**
     * Clean up renderer resources
     */
    destroy() {
        if (this.options.debug) {
            console.log(`${this.constructor.name}: Destroyed`);
        }
    }
    
    /**
     * Update FPS counter (called by render implementations)
     */
    updateFPS() {
        this.frameCount++;
        const now = Date.now();
        const elapsed = now - this.lastFPSUpdate;
        
        if (elapsed >= 1000) { // Update FPS every second
            this.currentFPS = Math.round((this.frameCount * 1000) / elapsed);
            this.frameCount = 0;
            this.lastFPSUpdate = now;
            
            // Update UI if element exists
            const fpsElement = document.getElementById('fps');
            if (fpsElement) {
                fpsElement.textContent = this.currentFPS;
            }
        }
    }
    
    /**
     * Get current performance stats
     * @returns {Object} Performance statistics
     */
    getPerformanceStats() {
        return {
            fps: this.currentFPS,
            nodeCount: this.nodes.length,
            linkCount: this.links.length,
            rendererType: this.constructor.name
        };
    }
    
    /**
     * Utility method to clamp values between min and max
     * @param {number} value - Value to clamp
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     * @returns {number} Clamped value
     */
    clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }
    
    /**
     * Utility method to interpolate between two values
     * @param {number} a - Start value
     * @param {number} b - End value
     * @param {number} t - Interpolation factor (0-1)
     * @returns {number} Interpolated value
     */
    lerp(a, b, t) {
        return a + (b - a) * this.clamp(t, 0, 1);
    }
}