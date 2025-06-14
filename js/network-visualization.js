/**
 * Network Visualization with Three Modes
 * 
 * Architecture: State-driven configuration system (inspired by Gemini's analysis)
 * Performance: Pre-processed data with boolean flags, CSS glow effects
 * 
 * Modes:
 * - Global: Node size = global popularity, glow = user's top artists
 * - Personal: Node size = user play count, glow = globally popular artists  
 * - Hybrid: Node size = combined metric, glow = overlap (popular + personal)
 */

class NetworkVisualization {
    constructor() {
        // State-driven configuration (Gemini's recommendation)
        this.currentMode = 'global';
        this.data = { nodes: [], links: [] };
        this.scales = {};
        this.simulation = null;
        
        // D3 selections
        this.svg = d3.select("svg");
        this.tooltip = d3.select(".tooltip");
        
        // Get container dimensions
        this.width = window.innerWidth - 320; // Sidebar width
        this.height = window.innerHeight;
        
        // Initialize
        this.setupSVG();
        this.setupEventListeners();
        this.loadData();
    }
    
    // Mode configurations (state-driven approach)
    get modeConfigs() {
        return {
            global: {
                name: 'Global',
                description: 'Node size shows global popularity. Your top artists glow.',
                radius: d => this.scales.global(d.listeners || 1),
                shouldGlow: d => d.isTopPersonal,
                tooltipContent: d => this.generateTooltip(d, 'global')
            },
            personal: {
                name: 'Personal', 
                description: 'Node size shows your play count. Popular artists glow.',
                radius: d => this.scales.personal(d.play_count || 1),
                shouldGlow: d => d.isTopGlobal,
                tooltipContent: d => this.generateTooltip(d, 'personal')
            },
            hybrid: {
                name: 'Hybrid',
                description: 'Combined view. Artists both popular and personal glow.',
                radius: d => this.scales.hybrid(d.listeners || 1, d.play_count || 1),
                shouldGlow: d => d.isTopPersonal && d.isTopGlobal,
                tooltipContent: d => this.generateTooltip(d, 'hybrid')
            }
        };
    }
    
    setupSVG() {
        this.svg.attr("width", this.width).attr("height", this.height);
        
        // Create container groups
        this.linkGroup = this.svg.append("g").attr("class", "links");
        this.linkLabelGroup = this.svg.append("g").attr("class", "link-labels");
        this.nodeGroup = this.svg.append("g").attr("class", "nodes");
        this.textGroup = this.svg.append("g").attr("class", "texts");
        
        // Setup zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                const transform = event.transform;
                this.linkGroup.attr("transform", transform);
                this.linkLabelGroup.attr("transform", transform);
                this.nodeGroup.attr("transform", transform);
                this.textGroup.attr("transform", transform);
            });
        
        this.svg.call(zoom);
    }
    
    setupEventListeners() {
        // Mode switching
        document.querySelectorAll('input[name="mode"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.setMode(e.target.value);
                }
            });
        });
        
        // Force controls
        document.getElementById('forceStrength').addEventListener('input', (e) => {
            if (this.simulation) {
                this.simulation.force("charge").strength(-e.target.value);
                this.simulation.alpha(0.3).restart();
            }
        });
        
        document.getElementById('linkDistance').addEventListener('input', (e) => {
            if (this.simulation) {
                this.simulation.force("link").distance(e.target.value);
                this.simulation.alpha(0.3).restart();
            }
        });
        
        document.getElementById('showLabels').addEventListener('change', (e) => {
            this.linkLabelGroup.style("opacity", e.target.checked ? 0.7 : 0);
        });
    }
    
    async loadData() {
        try {
            // Try to load from external JSON first, fallback to embedded data
            let networkData;
            try {
                networkData = await d3.json("bidirectional_network_100artists_20250613_012900.json");
            } catch {
                // Fallback to sample data based on corrected_network_d3.html
                networkData = this.getSampleData();
            }
            
            this.processData(networkData);
            this.createScales();
            this.initializeVisualization();
            
            // Hide loading indicator
            document.getElementById('loadingIndicator').style.display = 'none';
            
        } catch (error) {
            console.error('Error loading data:', error);
            document.getElementById('loadingIndicator').textContent = 'Error loading data';
        }
    }
    
    processData(networkData) {
        // Extract nodes and links
        this.data.nodes = networkData.nodes || [];
        this.data.links = networkData.edges || networkData.links || [];
        
        // Data preprocessing (Gemini's recommendation)
        this.preprocessNodes();
        
        console.log(`Loaded ${this.data.nodes.length} nodes, ${this.data.links.length} links`);
    }
    
    preprocessNodes() {
        // Calculate thresholds for "top" artists (Gemini's boolean flags approach)
        const listeners = this.data.nodes.map(d => d.listeners || d.listener_count || 0);
        const playCounts = this.data.nodes.map(d => d.play_count || 0);
        
        const globalThreshold = d3.quantile(listeners.sort(d3.descending), 0.8); // Top 20%
        const personalThreshold = d3.quantile(playCounts.filter(d => d > 0).sort(d3.descending), 0.8);
        
        // Preprocess each node
        this.data.nodes.forEach(d => {
            // Normalize data structure
            d.listeners = d.listeners || d.listener_count || 0;
            d.play_count = d.play_count || 0;
            d.name = d.name || d.id;
            d.canonical = d.canonical || d.name;
            
            // Pre-calculate boolean flags (massive performance improvement)
            d.isTopGlobal = d.listeners >= globalThreshold;
            d.isTopPersonal = d.play_count >= personalThreshold;
            
            // Ensure we have valid data for scales (handle 0 values)
            d.listeners = Math.max(d.listeners, 1);
            d.play_count = Math.max(d.play_count, 1);
        });
        
        console.log(`Global threshold: ${globalThreshold}, Personal threshold: ${personalThreshold}`);
    }
    
    createScales() {
        // Use sqrt scales for better visual perception (Gemini's recommendation)
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
        
        // Color scale based on listener count
        this.colorScale = d3.scaleSequential()
            .domain(d3.extent(listeners))
            .interpolator(d3.interpolateViridis);
    }
    
    initializeVisualization() {
        // Create force simulation
        this.simulation = d3.forceSimulation(this.data.nodes)
            .force("link", d3.forceLink(this.data.links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(this.width / 2, this.height / 2))
            .force("collision", d3.forceCollide().radius(d => d.currentRadius + 8));
        
        // Create visual elements
        this.createLinks();
        this.createNodes();
        this.createLabels();
        
        // Start in global mode
        this.updateVisualization();
        this.updateStats();
        
        // Setup simulation tick
        this.simulation.on("tick", () => this.tick());
    }
    
    createLinks() {
        this.links = this.linkGroup
            .selectAll("line")
            .data(this.data.links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", d => Math.sqrt(d.weight || d.lastfm_similarity || 0.5) * 6);
        
        this.linkLabels = this.linkLabelGroup
            .selectAll("text")
            .data(this.data.links)
            .enter().append("text")
            .attr("class", "link-label")
            .text(d => (d.weight || d.lastfm_similarity || 0).toFixed(2))
            .style("opacity", 0.7);
    }
    
    createNodes() {
        this.nodes = this.nodeGroup
            .selectAll("circle")
            .data(this.data.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("fill", d => this.colorScale(d.listeners))
            .on("mouseover", (event, d) => this.showTooltip(event, d))
            .on("mouseout", () => this.hideTooltip())
            .on("click", (event, d) => this.handleNodeClick(event, d))
            .call(this.createDragBehavior());
    }
    
    createLabels() {
        this.labels = this.textGroup
            .selectAll("text")
            .data(this.data.nodes)
            .enter().append("text")
            .text(d => d.name)
            .attr("font-size", "12px")
            .attr("text-anchor", "middle")
            .attr("fill", "white")
            .attr("font-weight", "bold")
            .attr("text-shadow", "2px 2px 4px rgba(0,0,0,0.8)")
            .style("pointer-events", "none");
    }
    
    createDragBehavior() {
        return d3.drag()
            .on("start", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on("drag", (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on("end", (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }
    
    setMode(newMode) {
        if (newMode === this.currentMode) return;
        
        this.currentMode = newMode;
        this.updateVisualization();
        this.updateStats();
        this.updateModeDescription();
    }
    
    updateVisualization() {
        const config = this.modeConfigs[this.currentMode];
        
        // Smooth transitions (with staggered delays per Gemini's suggestion)
        const transition = d3.transition().duration(750);
        
        // Update node radius and cache current radius for collision detection
        this.nodes
            .transition(transition)
            .delay((d, i) => i * 2) // Staggered animation
            .attr("r", d => {
                d.currentRadius = config.radius(d);
                return d.currentRadius;
            });
        
        // Update glow effect using CSS classes (much more performant than SVG filters)
        this.nodes
            .classed("glow", config.shouldGlow);
        
        // Update collision force with new radii
        if (this.simulation) {
            this.simulation.force("collision").radius(d => d.currentRadius + 8);
            // Don't restart simulation for visual-only changes
        }
    }
    
    updateModeDescription() {
        const config = this.modeConfigs[this.currentMode];
        document.getElementById('modeDescription').textContent = config.description;
        document.getElementById('currentMode').textContent = config.name;
    }
    
    updateStats() {
        const config = this.modeConfigs[this.currentMode];
        const glowingNodes = this.data.nodes.filter(config.shouldGlow);
        
        document.getElementById('nodeCount').textContent = this.data.nodes.length;
        document.getElementById('edgeCount').textContent = this.data.links.length;
        document.getElementById('glowingCount').textContent = glowingNodes.length;
    }
    
    showTooltip(event, d) {
        const config = this.modeConfigs[this.currentMode];
        
        this.tooltip.transition().duration(200).style("opacity", 1);
        this.tooltip.html(config.tooltipContent(d))
            .style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 50) + "px");
        
        // Highlight connections
        this.highlightConnections(d);
    }
    
    hideTooltip() {
        this.tooltip.transition().duration(500).style("opacity", 0);
        this.clearHighlights();
    }
    
    highlightConnections(node) {
        const connectedNodes = new Set();
        
        this.data.links.forEach(link => {
            if (link.source.id === node.id || link.target.id === node.id) {
                connectedNodes.add(link.source.id);
                connectedNodes.add(link.target.id);
            }
        });
        
        // Fade non-connected nodes
        this.nodes.style("opacity", d => connectedNodes.has(d.id) ? 1 : 0.3);
        
        // Highlight connected links
        this.links
            .classed("highlighted", d => d.source.id === node.id || d.target.id === node.id)
            .style("opacity", d => (d.source.id === node.id || d.target.id === node.id) ? 1 : 0.1);
    }
    
    clearHighlights() {
        this.nodes.style("opacity", 1);
        this.links.classed("highlighted", false).style("opacity", 0.7);
    }
    
    handleNodeClick(event, d) {
        if (d.url) {
            window.open(d.url, '_blank');
        }
    }
    
    generateTooltip(d, mode) {
        const modeSpecific = {
            global: `<strong>Global Rank:</strong> ${d.isTopGlobal ? 'Top 20%' : 'Lower tier'}<br/>`,
            personal: `<strong>Your Plays:</strong> ${d.play_count.toLocaleString()}<br/>`,
            hybrid: `<strong>Combined Score:</strong> ${this.scales.hybrid(d.listeners, d.play_count).toFixed(1)}<br/>`
        };
        
        return `
            <div style="border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 10px; margin-bottom: 10px;">
                <strong style="font-size: 16px;">${d.name}</strong><br/>
                <em>${d.canonical}</em>
            </div>
            <div style="margin: 5px 0;"><strong>Global Listeners:</strong> ${d.listeners.toLocaleString()}</div>
            ${modeSpecific[mode]}
            <div style="margin: 5px 0;"><strong>Status:</strong> ${this.modeConfigs[this.currentMode].shouldGlow(d) ? '✨ Glowing' : 'Normal'}</div>
            ${d.url ? `<div style="margin: 5px 0;"><strong>Profile:</strong> <a href="${d.url}" target="_blank" style="color: #64b5f6;">View on Last.fm</a></div>` : ''}
        `;
    }
    
    tick() {
        this.links
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        this.linkLabels
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2);
        
        this.nodes
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
        
        this.labels
            .attr("x", d => d.x)
            .attr("y", d => d.y + 4);
    }
    
    // Fallback sample data (based on corrected_network_d3.html)
    getSampleData() {
        return {
            nodes: [
                {"id": "taylor-swift", "name": "taylor swift", "canonical": "Taylor Swift", "listeners": 5160232, "play_count": 5216, "url": "https://www.last.fm/music/Taylor+Swift"},
                {"id": "paramore", "name": "paramore", "canonical": "Paramore", "listeners": 4779115, "play_count": 3460, "url": "https://www.last.fm/music/Paramore"},
                {"id": "iu", "name": "iu", "canonical": "IU", "listeners": 913058, "play_count": 2265, "url": "https://www.last.fm/music/IU"},
                {"id": "yorushika", "name": "ヨルシカ", "canonical": "ヨルシカ", "listeners": 186967, "play_count": 1282, "url": "https://www.last.fm/music/ヨルシカ"},
                {"id": "twice", "name": "twice", "canonical": "TWICE", "listeners": 1388675, "play_count": 1057, "url": "https://www.last.fm/music/TWICE"},
                {"id": "aimer", "name": "aimer", "canonical": "Aimer", "listeners": 389315, "play_count": 885, "url": "https://www.last.fm/music/Aimer"},
                {"id": "tonight-alive", "name": "tonight alive", "canonical": "Tonight Alive", "listeners": 319335, "play_count": 852, "url": "https://www.last.fm/music/Tonight+Alive"},
                {"id": "ive", "name": "ive", "canonical": "Ive", "listeners": 837966, "play_count": 662, "url": "https://www.last.fm/music/Ive"},
                {"id": "blackpink", "name": "blackpink", "canonical": "BLACKPINK", "listeners": 1558082, "play_count": 481, "url": "https://www.last.fm/music/BLACKPINK"},
                {"id": "dreamcatcher", "name": "dreamcatcher", "canonical": "Dreamcatcher", "listeners": 494541, "play_count": 462, "url": "https://www.last.fm/music/Dreamcatcher"}
            ],
            links: [
                {"source": "paramore", "target": "tonight-alive", "weight": 0.19963},
                {"source": "bol4", "target": "iu", "weight": 1.0},
                {"source": "iu", "target": "ive", "weight": 0.548231},
                {"source": "iu", "target": "twice", "weight": 0.467562},
                {"source": "dreamcatcher", "target": "iu", "weight": 0.424168},
                {"source": "aimer", "target": "yorushika", "weight": 0.438745},
                {"source": "ive", "target": "twice", "weight": 0.179055},
                {"source": "blackpink", "target": "twice", "weight": 0.122538},
                {"source": "dreamcatcher", "target": "twice", "weight": 0.117865},
                {"source": "blackpink", "target": "dreamcatcher", "weight": 0.183212}
            ]
        };
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new NetworkVisualization();
});