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
        this.currentMode = 'global'; // Add tri-mode support
        this.data = { nodes: [], links: [] };
        this.simulation = null;
        this.scales = {}; // Add scales for different modes
        
        // Configuration
        this.config = {
            forceStrength: -300,
            linkDistance: 150,
            centerForce: 0.1,
            collisionPadding: 8,
            alphaDecay: 0.0228, // D3 default
            velocityDecay: 0.4,  // D3 default
            zoomSensitivity: 1.0 // Zoom sensitivity multiplier
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
     * Mode configurations (tri-mode system from original architecture)
     */
    get modeConfigs() {
        return {
            global: {
                name: 'Global',
                description: 'Node size shows global popularity. Your top artists glow.',
                radius: d => this.scales.global ? this.scales.global(d.listener_count || d.listeners || 1) : 10,
                shouldGlow: d => d.isTopPersonal || false,
                tooltipContent: d => this.generateTooltip(d, 'global')
            },
            personal: {
                name: 'Personal', 
                description: 'Node size shows your play count. Popular artists glow.',
                radius: d => this.scales.personal ? this.scales.personal(d.play_count || 1) : 10,
                shouldGlow: d => d.isTopGlobal || false,
                tooltipContent: d => this.generateTooltip(d, 'personal')
            },
            hybrid: {
                name: 'Hybrid',
                description: 'Combined view. Artists both popular and personal glow.',
                radius: d => this.scales.hybrid ? this.scales.hybrid(d.listener_count || d.listeners || 1, d.play_count || 1) : 10,
                shouldGlow: d => (d.isTopPersonal && d.isTopGlobal) || false,
                tooltipContent: d => this.generateTooltip(d, 'hybrid')
            }
        };
    }
    
    /**
     * Setup UI event listeners
     */
    setupEventListeners() {
        // Mode switching (tri-mode system)
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.setMode(e.target.value);
                }
            });
        });
        
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
            // Invert the slider value: higher slider = stronger attraction (less negative)
            // Slider range 50-800 becomes force range -800 to -50
            const sliderValue = parseFloat(e.target.value);
            const maxSlider = parseFloat(forceStrengthSlider.max);
            const minSlider = parseFloat(forceStrengthSlider.min);
            
            // Invert: min slider value (50) -> max force magnitude (-800)
            // max slider value (800) -> min force magnitude (-50)
            this.config.forceStrength = -(maxSlider + minSlider - sliderValue);
            
            forceStrengthValue.textContent = e.target.value;
            this.updateSimulationForces();
        });
        
        // Zoom sensitivity (for future use)
        const zoomSensitivitySlider = document.getElementById('zoomSensitivity');
        const zoomSensitivityValue = document.getElementById('zoomSensitivityValue');
        
        zoomSensitivitySlider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            this.config.zoomSensitivity = value;
            zoomSensitivityValue.textContent = value.toFixed(1);
            this.updateZoomBehavior();
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
            await this.processData(networkData);
            
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
    async processData(networkData) {
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
        
        // Preprocess nodes for tri-mode system
        this.preprocessNodesForModes();
        
        // Create scales for different modes
        this.createScales();
        
        // Preload artist images if available
        await this.preloadArtistImages();
        
        // Update UI stats
        this.updateStats();
    }
    
    /**
     * Preprocess nodes for tri-mode system (from original architecture)
     */
    preprocessNodesForModes() {
        // Calculate thresholds for "top" artists (top 20% approach)
        const listeners = this.data.nodes.map(d => d.listener_count || d.listeners || 0);
        const playCounts = this.data.nodes.map(d => d.play_count || 0);
        
        const globalThreshold = d3.quantile(listeners.sort(d3.descending), 0.8); // Top 20%
        const personalThreshold = d3.quantile(playCounts.filter(d => d > 0).sort(d3.descending), 0.8);
        
        console.log(`📊 Mode thresholds - Global: ${globalThreshold}, Personal: ${personalThreshold}`);
        
        // Preprocess each node with boolean flags for performance
        this.data.nodes.forEach(d => {
            // Normalize data structure
            d.listeners = d.listener_count || d.listeners || 0;
            d.play_count = d.play_count || 0;
            
            // Pre-calculate boolean flags (massive performance improvement)
            d.isTopGlobal = d.listeners >= (globalThreshold || 0);
            d.isTopPersonal = d.play_count >= (personalThreshold || 0);
            
            // Ensure we have valid data for scales (handle 0 values)
            d.listeners = Math.max(d.listeners, 1);
            d.play_count = Math.max(d.play_count, 1);
            
            if (d.isTopGlobal || d.isTopPersonal) {
                console.log(`⭐ Special artist: ${d.name} (Global: ${d.isTopGlobal}, Personal: ${d.isTopPersonal})`);
            }
        });
    }
    
    /**
     * Create scales for different visualization modes
     */
    createScales() {
        // Use square root scales for better visual perception
        const listeners = this.data.nodes.map(d => d.listeners);
        const playCounts = this.data.nodes.map(d => d.play_count);
        
        this.scales.global = d3.scaleSqrt()
            .domain(d3.extent(listeners))
            .range([8, 30]);
            
        this.scales.personal = d3.scaleSqrt()
            .domain(d3.extent(playCounts))
            .range([8, 30]);
            
        // Hybrid scale: weighted combination
        this.scales.hybrid = (listeners, playCount) => {
            const normalizedListeners = this.scales.global(listeners);
            const normalizedPlays = this.scales.personal(playCount);
            return (normalizedListeners * 0.6) + (normalizedPlays * 0.4); // Weight towards global
        };
        
        console.log('📏 Scales created for tri-mode system');
    }
    
    /**
     * Preload artist profile images asynchronously
     */
    async preloadArtistImages() {
        console.log('🖼️ Starting artist image preloading...');
        
        const nodesWithImages = this.data.nodes.filter(node => node.photo_url);
        console.log(`📊 Found ${nodesWithImages.length} nodes with photo URLs`);
        
        if (nodesWithImages.length === 0) {
            console.log('⚠️ No photo URLs found in data');
            return;
        }
        
        const imagePromises = nodesWithImages.map(node => this.loadSingleImage(node));
        
        try {
            const results = await Promise.allSettled(imagePromises);
            
            let successCount = 0;
            let failCount = 0;
            
            results.forEach((result, index) => {
                const node = nodesWithImages[index];
                if (result.status === 'fulfilled') {
                    node.imageObj = result.value;
                    node.imageLoaded = true;
                    successCount++;
                    console.log(`✅ Loaded image for ${node.name}`);
                } else {
                    node.imageObj = null;
                    node.imageLoaded = false;
                    failCount++;
                    console.warn(`❌ Failed to load image for ${node.name}:`, result.reason);
                }
            });
            
            console.log(`🎯 Image preloading complete: ${successCount} success, ${failCount} failed`);
            
        } catch (error) {
            console.error('💥 Error during image preloading:', error);
        }
    }
    
    /**
     * Load a single image with timeout and error handling
     * @param {Object} node - Node object with photo_url
     * @returns {Promise<HTMLImageElement>} Promise that resolves to loaded image
     */
    loadSingleImage(node) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.crossOrigin = 'anonymous'; // Required for Canvas operations with external images
            
            // Set up timeout (5 seconds)
            const timeout = setTimeout(() => {
                reject(new Error(`Image load timeout after 5000ms: ${node.photo_url}`));
            }, 5000);
            
            img.onload = () => {
                clearTimeout(timeout);
                console.log(`🎨 Successfully loaded image for ${node.name}`);
                resolve(img);
            };
            
            img.onerror = () => {
                clearTimeout(timeout);
                reject(new Error(`Image load error: ${node.photo_url}`));
            };
            
            // Start loading
            img.src = node.photo_url;
        });
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
        
        // Apply initial mode
        this.updateModeDescription();
        this.updateRendererWithMode();
        
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
        this.zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .filter((event) => {
                // Apply zoom sensitivity to wheel events
                if (event.type === 'wheel') {
                    // Modify the wheel delta based on sensitivity
                    const sensitivity = this.config.zoomSensitivity;
                    event.deltaY *= (1 / sensitivity); // Invert because higher sensitivity should zoom faster
                }
                return true;
            })
            .on('zoom', (event) => {
                if (this.renderer) {
                    this.renderer.updateTransform(event.transform);
                }
            });
        
        this.applyZoomToRenderer();
        
        console.log('Zoom behavior setup complete');
    }
    
    /**
     * Apply zoom behavior to current renderer element
     */
    applyZoomToRenderer() {
        if (!this.zoom) return;
        
        // Apply zoom to container or renderer surface
        if (this.currentRendererType === 'canvas') {
            // For Canvas, apply zoom to the canvas element
            const canvas = this.container.querySelector('canvas');
            if (canvas) {
                d3.select(canvas).call(this.zoom);
            }
        } else {
            // For SVG, apply zoom to the SVG element
            const svg = this.container.querySelector('svg');
            if (svg) {
                d3.select(svg).call(this.zoom);
            }
        }
    }
    
    /**
     * Update zoom behavior with new sensitivity
     */
    updateZoomBehavior() {
        if (this.zoom) {
            // Update the filter function with new sensitivity
            this.zoom.filter((event) => {
                if (event.type === 'wheel') {
                    const sensitivity = this.config.zoomSensitivity;
                    event.deltaY *= (1 / sensitivity);
                }
                return true;
            });
            
            // Reapply to renderer
            this.applyZoomToRenderer();
            
            console.log(`Zoom sensitivity updated to ${this.config.zoomSensitivity}`);
        }
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
        this.applyZoomToRenderer();
        
        // Restart simulation
        if (this.simulation) {
            this.simulation.alpha(0.3).restart();
        }
        
        // Update UI
        document.getElementById('currentRenderer').textContent = 
            rendererType.charAt(0).toUpperCase() + rendererType.slice(1);
    }
    
    /**
     * Set visualization mode (tri-mode system)
     * @param {string} newMode - 'global', 'personal', or 'hybrid'
     */
    setMode(newMode) {
        if (newMode === this.currentMode) return;
        
        console.log(`🎭 Switching mode from ${this.currentMode} to ${newMode}`);
        
        this.currentMode = newMode;
        
        // Update mode description
        this.updateModeDescription();
        
        // Trigger re-rendering with new mode
        if (this.renderer) {
            // Re-process nodes with new mode
            this.updateRendererWithMode();
        }
    }
    
    /**
     * Update mode description in UI
     */
    updateModeDescription() {
        const config = this.modeConfigs[this.currentMode];
        const descElement = document.getElementById('modeDescription');
        if (descElement) {
            descElement.textContent = config.description;
        }
    }
    
    /**
     * Update renderer with current mode settings
     */
    updateRendererWithMode() {
        if (!this.renderer) return;
        
        // Re-process nodes with current mode configuration
        const config = this.modeConfigs[this.currentMode];
        
        this.data.nodes.forEach(node => {
            // Update radius based on current mode
            node.radius = config.radius(node);
            
            // Update glow intensity based on current mode
            node.shouldGlow = config.shouldGlow(node);
            node.glowIntensity = node.shouldGlow ? 1.0 : 0.0;
        });
        
        // Update renderer data
        this.renderer.updateData(this.data.nodes, this.data.links);
        
        // Debug tri-mode system
        const sampleNode = this.data.nodes[0];
        if (sampleNode) {
            console.log(`✨ Updated visualization for ${this.currentMode} mode`);
            console.log(`  Sample node "${sampleNode.name}": radius=${sampleNode.radius}, shouldGlow=${sampleNode.shouldGlow}`);
        }
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
        
        // Update mode-specific statistics
        const config = this.modeConfigs[this.currentMode];
        const glowingNodes = this.data.nodes.filter(config.shouldGlow);
        
        // Update FPS display if available
        const fpsElement = document.getElementById('fps');
        if (fpsElement && this.renderer && this.renderer.fps) {
            fpsElement.textContent = Math.round(this.renderer.fps);
        }
        
        console.log(`📊 Stats updated - Mode: ${this.currentMode}, Glowing nodes: ${glowingNodes.length}`);
    }
    
    /**
     * Generate tooltip content for different modes
     */
    generateTooltip(d, mode) {
        const modeSpecific = {
            global: `<strong>Global Rank:</strong> ${d.isTopGlobal ? 'Top 20%' : 'Lower tier'}<br/>`,
            personal: `<strong>Your Plays:</strong> ${d.play_count.toLocaleString()}<br/>`,
            hybrid: `<strong>Combined Score:</strong> ${this.scales.hybrid(d.listeners, d.play_count).toFixed(1)}<br/>`
        };
        
        return `
            <div style="border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 10px; margin-bottom: 10px;">
                <strong style="font-size: 16px;">${d.name}</strong><br/>
                <em>${d.canonical || d.name}</em>
            </div>
            <div style="margin: 5px 0;"><strong>Global Listeners:</strong> ${d.listeners.toLocaleString()}</div>
            ${modeSpecific[mode]}
            <div style="margin: 5px 0;"><strong>Status:</strong> ${this.modeConfigs[this.currentMode].shouldGlow(d) ? '✨ Glowing' : 'Normal'}</div>
        `;
    }
    
    /**
     * Get sample data for testing
     */
    getSampleData() {
        // Using verified URLs from real dataset (phase1_test_results.json)
        const sampleNodes = [
            {"id": "taylor-swift", "name": "Taylor Swift", "listener_count": 5160232, "play_count": 5216, "genres_lastfm": ["country", "pop"], "photo_url": "https://i.scdn.co/image/ab6761610000e5ebe672b5f553298dcdccb0e676"},
            {"id": "paramore", "name": "Paramore", "listener_count": 4779115, "play_count": 3460, "genres_lastfm": ["rock", "pop punk"], "photo_url": "https://i.scdn.co/image/ab6761610000e5ebb10c34546a4ca2d7faeb8865"},
            {"id": "ive", "name": "Ive", "listener_count": 837966, "play_count": 662, "genres_lastfm": ["k-pop", "korean"], "photo_url": "https://i.scdn.co/image/0078316432cdfb6733c3bde0dc61754d45442d0f"},
            {"id": "yorushika", "name": "Yorushika", "listener_count": 186967, "play_count": 1282, "genres_lastfm": ["j-pop", "japanese"], "photo_url": "https://i.scdn.co/image/ab6761610000e5ebe62cff9c6018ae5616b01eab"},
            {"id": "iu", "name": "IU", "listener_count": 913058, "play_count": 2265, "genres_lastfm": ["k-pop", "korean"], "photo_url": "https://i.scdn.co/image/ab6761610000e5eb789f38042e5ef8911fc3826b"},
            {"id": "aimer", "name": "Aimer", "listener_count": 389315, "play_count": 885, "genres_lastfm": ["j-pop", "japanese"], "photo_url": "https://i.scdn.co/image/ab6761610000e5eb7e58b86655f447e0ef0278b8"},
            {"id": "luna", "name": "*LUNA", "listener_count": 450000, "play_count": 720, "genres_lastfm": ["k-pop", "korean"], "photo_url": "https://i.scdn.co/image/ab6761610000e5eb45d443b065a66c92d166f598"},
            {"id": "rose", "name": "Rosé", "listener_count": 380000, "play_count": 590, "genres_lastfm": ["k-pop", "korean"], "photo_url": "https://i.scdn.co/image/ab6761610000e5ebcfb4350222919670128ff2dc"},
            {"id": "younha", "name": "Younha", "listener_count": 320000, "play_count": 480, "genres_lastfm": ["k-pop", "korean"], "photo_url": "https://i.scdn.co/image/ab6761610000e5ebf5e315e40a6d4ffd36c10d94"},
            {"id": "yoasobi", "name": "yoasobi", "listener_count": 425000, "play_count": 654, "genres_lastfm": ["j-pop", "japanese"], "photo_url": "https://i.scdn.co/image/ab6761610000e5eb507349709ae19263301a62f7"}
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