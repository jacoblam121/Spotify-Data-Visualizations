/**
 * Enhanced Network Visualization - Phase 2.1a
 * 
 * Main application class implementing renderer abstraction
 * and basic Canvas/SVG switching capability
 */

class EnhancedNetworkVisualization {
    constructor() {
        console.log('🚀 EnhancedNetworkVisualization constructor called');
        
        this.renderer = null;
        this.currentRendererType = 'canvas';
        this.data = { nodes: [], links: [] };
        this.simulation = null;
        
        // Configuration
        this.config = {
            forceStrength: -300,
            linkDistance: 150,
            centerForce: 0.1,
            collisionPadding: 8,
            alphaDecay: 0.0228, // D3 default
            velocityDecay: 0.4   // D3 default
        };
        
        // Get main container
        this.container = document.querySelector('.main');
        if (!this.container) {
            console.error('❌ Main container not found!');
            return;
        }
        console.log('✅ Main container found:', this.container);
        
        // Initialize
        console.log('🔧 Setting up event listeners...');
        this.setupEventListeners();
        
        console.log('📡 Starting data loading...');
        this.loadData();
    }
    
    /**
     * Setup UI event listeners
     */
    setupEventListeners() {
        // Renderer switching
        document.querySelectorAll('input[name="renderer"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.switchRenderer(e.target.value);
                }
            });
        });
        
        // Force controls
        const forceStrengthSlider = document.getElementById('forceStrength');
        const forceStrengthValue = document.getElementById('forceStrengthValue');
        
        forceStrengthSlider.addEventListener('input', (e) => {
            this.config.forceStrength = -parseFloat(e.target.value);
            forceStrengthValue.textContent = e.target.value;
            this.updateSimulationForces();
        });
        
        // Zoom sensitivity (for future use)
        const zoomSensitivitySlider = document.getElementById('zoomSensitivity');
        const zoomSensitivityValue = document.getElementById('zoomSensitivityValue');
        
        zoomSensitivitySlider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            zoomSensitivityValue.textContent = value.toFixed(1);
            // TODO: Apply to zoom behavior
        });
    }
    
    /**
     * Load network data
     */
    async loadData() {
        const loadingIndicator = document.getElementById('loadingIndicator');
        
        try {
            console.log('🔄 Starting data loading process...');
            loadingIndicator.textContent = 'Loading network data...';
            
            // Skip external file loading for now and use sample data
            console.log('📦 Using sample data for testing');
            loadingIndicator.textContent = 'Using sample data...';
            const networkData = this.getSampleData();
            
            console.log('📊 Processing network data...');
            loadingIndicator.textContent = 'Processing data...';
            this.processData(networkData);
            
            console.log('🎨 Initializing visualization...');
            loadingIndicator.textContent = 'Initializing visualization...';
            this.initializeVisualization();
            
            console.log('✅ Data loading complete!');
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
            
        } catch (error) {
            console.error('💥 Critical error during data loading:', error);
            loadingIndicator.textContent = 'Error: ' + error.message;
            loadingIndicator.style.color = '#F44336'; // Red color for errors
        }
    }
    
    /**
     * Process loaded network data
     * @param {Object} networkData - Raw network data
     */
    processData(networkData) {
        // Handle different data formats
        this.data.nodes = networkData.nodes || [];
        this.data.links = networkData.edges || networkData.links || [];
        
        // Extract from test format if needed (network_data structure)
        if (networkData.network_data && networkData.network_data.nodes) {
            this.data.nodes = networkData.network_data.nodes;
            this.data.links = networkData.network_data.edges || networkData.network_data.links || [];
        }
        // Alternative network structure
        else if (networkData.network && networkData.network.nodes) {
            this.data.nodes = networkData.network.nodes;
            this.data.links = networkData.network.edges || networkData.network.links || [];
        }
        
        // Ensure nodes have required properties
        this.data.nodes.forEach((node, index) => {
            node.id = node.id || node.name || `node-${index}`;
            node.x = node.x || Math.random() * 800;
            node.y = node.y || Math.random() * 600;
        });
        
        // Ensure links reference correct nodes
        this.data.links = this.data.links.filter(link => {
            const sourceExists = this.data.nodes.find(n => n.id === link.source || n.id === link.source.id);
            const targetExists = this.data.nodes.find(n => n.id === link.target || n.id === link.target.id);
            return sourceExists && targetExists;
        });
        
        console.log(`Processed ${this.data.nodes.length} nodes and ${this.data.links.length} links`);
        
        // Update UI stats
        this.updateStats();
    }
    
    /**
     * Initialize the visualization with current renderer
     */
    initializeVisualization() {
        // Initialize renderer
        this.initializeRenderer();
        
        // Initialize D3 force simulation
        this.initializeSimulation();
        
        // Setup zoom and pan
        this.setupZoomBehavior();
        
        console.log('Enhanced Network Visualization initialized');
    }
    
    /**
     * Initialize the current renderer
     */
    initializeRenderer() {
        // Clean up existing renderer
        if (this.renderer) {
            this.renderer.destroy();
        }
        
        // Create new renderer based on type
        const rendererOptions = {
            width: this.container.clientWidth,
            height: this.container.clientHeight,
            debug: true
        };
        
        switch (this.currentRendererType) {
            case 'canvas':
                this.renderer = new CanvasRenderer(this.container, rendererOptions);
                break;
            case 'svg':
                this.renderer = new SVGRenderer(this.container, rendererOptions);
                break;
            default:
                throw new Error(`Unknown renderer type: ${this.currentRendererType}`);
        }
        
        this.renderer.initialize();
        this.renderer.updateData(this.data.nodes, this.data.links);
        
        // Start Canvas render loop if using Canvas
        if (this.currentRendererType === 'canvas') {
            this.renderer.startRenderLoop();
        }
        
        console.log(`Initialized ${this.currentRendererType} renderer`);
    }
    
    /**
     * Initialize D3 force simulation
     */
    initializeSimulation() {
        // Create force simulation
        this.simulation = d3.forceSimulation(this.data.nodes)
            .force('link', d3.forceLink(this.data.links).id(d => d.id).distance(this.config.linkDistance))
            .force('charge', d3.forceManyBody().strength(this.config.forceStrength))
            .force('center', d3.forceCenter(this.container.clientWidth / 2, this.container.clientHeight / 2))
            .force('collision', d3.forceCollide().radius(d => (d.radius || 8) + this.config.collisionPadding))
            .alphaDecay(this.config.alphaDecay)
            .velocityDecay(this.config.velocityDecay);
        
        // Setup simulation tick handler
        this.simulation.on('tick', () => this.handleSimulationTick());
        
        console.log('Force simulation initialized');
    }
    
    /**
     * Handle simulation tick - update renderer
     */
    handleSimulationTick() {
        if (this.renderer) {
            if (this.currentRendererType === 'canvas') {
                // Canvas renderer uses render loop, just invalidate
                this.renderer.invalidate();
            } else if (this.currentRendererType === 'svg') {
                // SVG renderer needs explicit position updates
                this.renderer.updateNodePositions(this.data.nodes);
            }
        }
    }
    
    /**
     * Setup D3 zoom and pan behavior
     */
    setupZoomBehavior() {
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {
                if (this.renderer) {
                    this.renderer.updateTransform(event.transform);
                }
            });
        
        // Apply zoom to container or renderer surface
        if (this.currentRendererType === 'canvas') {
            // For Canvas, apply zoom to the canvas element
            const canvas = this.container.querySelector('canvas');
            if (canvas) {
                d3.select(canvas).call(zoom);
            }
        } else {
            // For SVG, apply zoom to the SVG element
            const svg = this.container.querySelector('svg');
            if (svg) {
                d3.select(svg).call(zoom);
            }
        }
        
        console.log('Zoom behavior setup complete');
    }
    
    /**
     * Switch renderer type
     * @param {string} rendererType - 'canvas' or 'svg'
     */
    switchRenderer(rendererType) {
        if (rendererType === this.currentRendererType) return;
        
        console.log(`Switching renderer from ${this.currentRendererType} to ${rendererType}`);
        
        this.currentRendererType = rendererType;
        
        // Pause simulation during switch
        if (this.simulation) {
            this.simulation.stop();
        }
        
        // Reinitialize with new renderer
        this.initializeRenderer();
        this.setupZoomBehavior();
        
        // Restart simulation
        if (this.simulation) {
            this.simulation.alpha(0.3).restart();
        }
        
        // Update UI
        document.getElementById('currentRenderer').textContent = 
            rendererType.charAt(0).toUpperCase() + rendererType.slice(1);
    }
    
    /**
     * Update simulation forces based on config
     */
    updateSimulationForces() {
        if (this.simulation) {
            this.simulation.force('charge').strength(this.config.forceStrength);
            this.simulation.alpha(0.3).restart();
        }
    }
    
    /**
     * Update UI statistics
     */
    updateStats() {
        document.getElementById('nodeCount').textContent = this.data.nodes.length;
        document.getElementById('edgeCount').textContent = this.data.links.length;
        document.getElementById('currentRenderer').textContent = 
            this.currentRendererType.charAt(0).toUpperCase() + this.currentRendererType.slice(1);
    }
    
    /**
     * Get sample data for testing
     */
    getSampleData() {
        // Add Unicode debugging and normalization
        const sampleNodes = [
            {"id": "taylor-swift", "name": "Taylor Swift", "listener_count": 5160232, "play_count": 5216, "genres_lastfm": ["country", "pop"]},
            {"id": "paramore", "name": "Paramore", "listener_count": 4779115, "play_count": 3460, "genres_lastfm": ["rock", "pop punk"]},
            {"id": "iu", "name": "IU", "listener_count": 913058, "play_count": 2265, "genres_lastfm": ["k-pop", "korean"]},
            {"id": "yorushika", "name": "ヨルシカ", "listener_count": 186967, "play_count": 1282, "genres_lastfm": ["j-pop", "japanese"]},
            {"id": "twice", "name": "TWICE", "listener_count": 1388675, "play_count": 1057, "genres_lastfm": ["k-pop", "korean"]},
            {"id": "ive", "name": "IVE", "listener_count": 837966, "play_count": 662, "genres_lastfm": ["k-pop", "korean"]},
            {"id": "blackpink", "name": "BLACKPINK", "listener_count": 1558082, "play_count": 481, "genres_lastfm": ["k-pop", "korean"]},
            {"id": "newjeans", "name": "NewJeans", "listener_count": 750000, "play_count": 320, "genres_lastfm": ["k-pop", "korean"]},
            {"id": "aimer", "name": "Aimer", "listener_count": 389315, "play_count": 885, "genres_lastfm": ["j-pop", "japanese"]},
            {"id": "yoasobi", "name": "YOASOBI", "listener_count": 425000, "play_count": 654, "genres_lastfm": ["j-pop", "japanese"]}
        ];
        
        // Unicode debugging and normalization (Gemini's recommendation)
        sampleNodes.forEach(node => {
            const originalName = node.name;
            node.name = node.name.normalize('NFC'); // Normalize Unicode
            
            // Debug Unicode issues
            if (originalName !== node.name) {
                console.log(`🔤 Normalized: "${originalName}" → "${node.name}"`);
            }
            
            // Log problematic characters for debugging
            if (node.id === 'yorushika') {
                console.log('🎌 Yorushika name check:');
                console.log('  Raw name:', JSON.stringify(node.name));
                console.log('  Char codes:', node.name.split('').map(c => c.charCodeAt(0)));
                console.log('  Length:', node.name.length);
            }
        });
        
        return {
            nodes: sampleNodes,
            links: [
                {"source": "iu", "target": "ive", "weight": 0.548231},
                {"source": "iu", "target": "twice", "weight": 0.467562},
                {"source": "ive", "target": "twice", "weight": 0.179055},
                {"source": "blackpink", "target": "twice", "weight": 0.122538},
                {"source": "blackpink", "target": "ive", "weight": 0.183212},
                {"source": "newjeans", "target": "ive", "weight": 0.265},
                {"source": "yorushika", "target": "aimer", "weight": 0.445},
                {"source": "aimer", "target": "yoasobi", "weight": 0.332},
                {"source": "taylor-swift", "target": "paramore", "weight": 0.184}
            ]
        };
    }
}

// Debug logging to track script execution
console.log('📜 network_enhanced_fixed.js loaded');

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('🌐 DOM Content Loaded - Initializing Enhanced Network Visualization');
    
    // Check if all dependencies are loaded
    if (typeof d3 === 'undefined') {
        console.error('❌ D3.js not loaded!');
        return;
    }
    
    if (typeof CanvasRenderer === 'undefined') {
        console.error('❌ CanvasRenderer not loaded!');
        return;
    }
    
    if (typeof SVGRenderer === 'undefined') {
        console.error('❌ SVGRenderer not loaded!');
        return;
    }
    
    console.log('✅ All dependencies loaded, starting visualization...');
    
    try {
        new EnhancedNetworkVisualization();
    } catch (error) {
        console.error('💥 Failed to initialize EnhancedNetworkVisualization:', error);
        console.error('Stack trace:', error.stack);
        
        // Emergency fallback - show error message
        const loadingIndicator = document.getElementById('loadingIndicator');
        if (loadingIndicator) {
            loadingIndicator.textContent = 'Initialization failed: ' + error.message;
            loadingIndicator.style.color = '#F44336';
        }
    }
});