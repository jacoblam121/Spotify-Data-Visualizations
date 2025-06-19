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
            
            // Try to load from the latest network file
            let networkData;
            let loadSuccess = false;
            
            // Try Phase 1 data files in order of preference (relative to parent directory)
            const dataFiles = [
                '../phase1_test_50artists_20250617_222247.json',
                '../bidirectional_network_100artists_20250613_012900.json',
                '../phase1_test_50artists_20250617_220745.json'
            ];
            
            console.log(`📁 Attempting to load data files:`, dataFiles);
            
            for (let i = 0; i < dataFiles.length; i++) {
                const file = dataFiles[i];
                try {
                    console.log(`🔍 Trying to load: ${file}`);
                    loadingIndicator.textContent = `Loading ${file}...`;
                    
                    networkData = await d3.json(file);
                    console.log(`✅ Successfully loaded: ${file}`, networkData);
                    loadSuccess = true;
                    break;
                    
                } catch (e) {
                    console.warn(`❌ Failed to load ${file}:`, e);
                    loadingIndicator.textContent = `Failed ${file}, trying next...`;
                    // Continue to next file
                }
            }
            
            if (!loadSuccess) {
                console.log('📦 All files failed, using fallback sample data');
                loadingIndicator.textContent = 'Using sample data...';
                networkData = this.getSampleData();
            }
            
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
            
            // Try emergency fallback
            try {
                console.log('🚨 Attempting emergency fallback...');
                this.processData(this.getSampleData());
                this.initializeVisualization();
                loadingIndicator.textContent = 'Loaded with sample data (some errors occurred)';
                loadingIndicator.style.color = '#FF9800'; // Orange for warnings
            } catch (fallbackError) {
                console.error('💥 Emergency fallback also failed:', fallbackError);
                loadingIndicator.textContent = 'Complete failure - check console for details';
            }
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
        
        console.log('Force simulation initialized');\n    }\n    \n    /**\n     * Handle simulation tick - update renderer\n     */\n    handleSimulationTick() {\n        if (this.renderer) {\n            if (this.currentRendererType === 'canvas') {\n                // Canvas renderer uses render loop, just invalidate\n                this.renderer.invalidate();\n            } else if (this.currentRendererType === 'svg') {\n                // SVG renderer needs explicit position updates\n                this.renderer.updateNodePositions(this.data.nodes);\n            }\n        }\n    }\n    \n    /**\n     * Setup D3 zoom and pan behavior\n     */\n    setupZoomBehavior() {\n        const zoom = d3.zoom()\n            .scaleExtent([0.1, 10])\n            .on('zoom', (event) => {\n                if (this.renderer) {\n                    this.renderer.updateTransform(event.transform);\n                }\n            });\n        \n        // Apply zoom to container or renderer surface\n        if (this.currentRendererType === 'canvas') {\n            // For Canvas, apply zoom to the canvas element\n            const canvas = this.container.querySelector('canvas');\n            if (canvas) {\n                d3.select(canvas).call(zoom);\n            }\n        } else {\n            // For SVG, apply zoom to the SVG element\n            const svg = this.container.querySelector('svg');\n            if (svg) {\n                d3.select(svg).call(zoom);\n            }\n        }\n        \n        console.log('Zoom behavior setup complete');\n    }\n    \n    /**\n     * Switch renderer type\n     * @param {string} rendererType - 'canvas' or 'svg'\n     */\n    switchRenderer(rendererType) {\n        if (rendererType === this.currentRendererType) return;\n        \n        console.log(`Switching renderer from ${this.currentRendererType} to ${rendererType}`);\n        \n        this.currentRendererType = rendererType;\n        \n        // Pause simulation during switch\n        if (this.simulation) {\n            this.simulation.stop();\n        }\n        \n        // Reinitialize with new renderer\n        this.initializeRenderer();\n        this.setupZoomBehavior();\n        \n        // Restart simulation\n        if (this.simulation) {\n            this.simulation.alpha(0.3).restart();\n        }\n        \n        // Update UI\n        document.getElementById('currentRenderer').textContent = \n            rendererType.charAt(0).toUpperCase() + rendererType.slice(1);\n    }\n    \n    /**\n     * Update simulation forces based on config\n     */\n    updateSimulationForces() {\n        if (this.simulation) {\n            this.simulation.force('charge').strength(this.config.forceStrength);\n            this.simulation.alpha(0.3).restart();\n        }\n    }\n    \n    /**\n     * Update UI statistics\n     */\n    updateStats() {\n        document.getElementById('nodeCount').textContent = this.data.nodes.length;\n        document.getElementById('edgeCount').textContent = this.data.links.length;\n        document.getElementById('currentRenderer').textContent = \n            this.currentRendererType.charAt(0).toUpperCase() + this.currentRendererType.slice(1);\n    }\n    \n    /**\n     * Get sample data for testing\n     */\n    getSampleData() {\n        return {\n            nodes: [\n                {\"id\": \"taylor-swift\", \"name\": \"Taylor Swift\", \"listener_count\": 5160232, \"play_count\": 5216},\n                {\"id\": \"paramore\", \"name\": \"Paramore\", \"listener_count\": 4779115, \"play_count\": 3460},\n                {\"id\": \"iu\", \"name\": \"IU\", \"listener_count\": 913058, \"play_count\": 2265, \"genres_lastfm\": [\"k-pop\", \"korean\"]},\n                {\"id\": \"yorushika\", \"name\": \"ヨルシカ\", \"listener_count\": 186967, \"play_count\": 1282, \"genres_lastfm\": [\"j-pop\", \"japanese\"]},\n                {\"id\": \"twice\", \"name\": \"TWICE\", \"listener_count\": 1388675, \"play_count\": 1057, \"genres_lastfm\": [\"k-pop\", \"korean\"]},\n                {\"id\": \"ive\", \"name\": \"IVE\", \"listener_count\": 837966, \"play_count\": 662, \"genres_lastfm\": [\"k-pop\", \"korean\"]},\n                {\"id\": \"blackpink\", \"name\": \"BLACKPINK\", \"listener_count\": 1558082, \"play_count\": 481, \"genres_lastfm\": [\"k-pop\", \"korean\"]}\n            ],\n            links: [\n                {\"source\": \"iu\", \"target\": \"ive\", \"weight\": 0.548231},\n                {\"source\": \"iu\", \"target\": \"twice\", \"weight\": 0.467562},\n                {\"source\": \"ive\", \"target\": \"twice\", \"weight\": 0.179055},\n                {\"source\": \"blackpink\", \"target\": \"twice\", \"weight\": 0.122538},\n                {\"source\": \"blackpink\", \"target\": \"ive\", \"weight\": 0.183212}\n            ]\n        };\n    }\n}\n\n// Initialize when page loads\ndocument.addEventListener('DOMContentLoaded', () => {\n    new EnhancedNetworkVisualization();\n});