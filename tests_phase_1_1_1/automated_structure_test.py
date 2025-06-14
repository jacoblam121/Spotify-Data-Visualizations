#!/usr/bin/env python3
"""
Automated Structure Test for Phase 1.1.1
==========================================

Automated tests that can be run without manual interaction to validate
file structure, data parsing, and basic properties of the visualizations.
"""

import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class FileAnalysis:
    """Analysis results for a single file"""
    filename: str
    exists: bool
    file_size: int
    d3_version: Optional[str]
    node_count: int
    edge_count: int
    has_sidebar: bool
    has_controls: bool
    has_zoom: bool
    has_tooltips: bool
    data_structure: Dict[str, Any]
    css_features: List[str]
    js_features: List[str]


class AutomatedStructureTest:
    """Automated analysis of visualization files"""
    
    def __init__(self, project_root: str = ".."):
        self.project_root = Path(project_root)
        self.files_to_test = [
            "network_d3.html",
            "real_network_d3.html", 
            "corrected_network_d3.html"
        ]
    
    def run_analysis(self) -> Dict[str, FileAnalysis]:
        """Run automated analysis on all files"""
        print("🤖 Running Automated Structure Analysis")
        print("=" * 50)
        
        results = {}
        
        for filename in self.files_to_test:
            print(f"\n🔍 Analyzing {filename}...")
            analysis = self._analyze_file(filename)
            results[filename] = analysis
            self._print_file_summary(analysis)
        
        # Generate comparison
        self._print_comparison(results)
        
        # Save results
        self._save_analysis(results)
        
        return results
    
    def _analyze_file(self, filename: str) -> FileAnalysis:
        """Analyze a single HTML file"""
        file_path = self.project_root / filename
        
        if not file_path.exists():
            return FileAnalysis(
                filename=filename,
                exists=False,
                file_size=0,
                d3_version=None,
                node_count=0,
                edge_count=0,
                has_sidebar=False,
                has_controls=False,
                has_zoom=False,
                has_tooltips=False,
                data_structure={},
                css_features=[],
                js_features=[]
            )
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic file info
        file_size = len(content)
        
        # Extract D3 version
        d3_version = self._extract_d3_version(content)
        
        # Extract embedded data
        nodes, edges = self._extract_data(content)
        
        # Analyze structure
        has_sidebar = self._has_sidebar(content)
        has_controls = self._has_controls(content)
        has_zoom = self._has_zoom(content)
        has_tooltips = self._has_tooltips(content)
        
        # Extract features
        css_features = self._extract_css_features(content)
        js_features = self._extract_js_features(content)
        
        # Analyze data structure
        data_structure = self._analyze_data_structure(nodes, edges)
        
        return FileAnalysis(
            filename=filename,
            exists=True,
            file_size=file_size,
            d3_version=d3_version,
            node_count=len(nodes),
            edge_count=len(edges),
            has_sidebar=has_sidebar,
            has_controls=has_controls,
            has_zoom=has_zoom,
            has_tooltips=has_tooltips,
            data_structure=data_structure,
            css_features=css_features,
            js_features=js_features
        )
    
    def _extract_d3_version(self, content: str) -> Optional[str]:
        """Extract D3.js version from script tag"""
        match = re.search(r'd3\.v(\d+)\.min\.js', content)
        return f"v{match.group(1)}" if match else None
    
    def _extract_data(self, content: str) -> tuple:
        """Extract nodes and edges data from JavaScript"""
        nodes = []
        edges = []
        
        # Extract nodes array
        nodes_match = re.search(r'const nodes = (\[.*?\]);', content, re.DOTALL)
        if nodes_match:
            try:
                nodes_str = nodes_match.group(1)
                # Simple JSON parsing (may need adjustment for complex data)
                nodes = json.loads(nodes_str)
            except json.JSONDecodeError:
                # Fallback: count manually
                nodes = re.findall(r'\{"id":', content)
        
        # Extract edges/links array
        edges_match = re.search(r'const (?:links|edges) = (\[.*?\]);', content, re.DOTALL)
        if edges_match:
            try:
                edges_str = edges_match.group(1)
                edges = json.loads(edges_str)
            except json.JSONDecodeError:
                # Fallback: count manually
                edges = re.findall(r'\{"source":', content)
        
        return nodes, edges
    
    def _has_sidebar(self, content: str) -> bool:
        """Check if file has sidebar"""
        return 'sidebar' in content.lower() or 'class="sidebar"' in content
    
    def _has_controls(self, content: str) -> bool:
        """Check if file has interactive controls"""
        return bool(re.search(r'input.*type=["\']range["\']', content)) or 'control' in content.lower()
    
    def _has_zoom(self, content: str) -> bool:
        """Check if file has zoom functionality"""
        return 'd3.zoom' in content
    
    def _has_tooltips(self, content: str) -> bool:
        """Check if file has tooltips"""
        return 'tooltip' in content.lower()
    
    def _extract_css_features(self, content: str) -> List[str]:
        """Extract notable CSS features"""
        features = []
        
        if 'gradient' in content.lower():
            features.append('gradients')
        if 'backdrop-filter' in content:
            features.append('backdrop_blur')
        if 'transition' in content.lower():
            features.append('transitions')
        if '@media' in content:
            features.append('responsive')
        if 'flex' in content.lower():
            features.append('flexbox')
        if 'box-shadow' in content:
            features.append('shadows')
        if 'border-radius' in content:
            features.append('rounded_corners')
        
        return features
    
    def _extract_js_features(self, content: str) -> List[str]:
        """Extract notable JavaScript features"""
        features = []
        
        if 'forceSimulation' in content:
            features.append('force_simulation')
        if 'd3.drag' in content:
            features.append('drag_nodes')
        if 'd3.zoom' in content:
            features.append('zoom_pan')
        if 'mouseover' in content:
            features.append('hover_events')
        if 'click' in content:
            features.append('click_events')
        if 'addEventListener' in content or '.on(' in content:
            features.append('event_handlers')
        if 'transition()' in content:
            features.append('animations')
        if 'scaleOrdinal' in content or 'scaleSequential' in content:
            features.append('color_scales')
        
        return features
    
    def _analyze_data_structure(self, nodes: List, edges: List) -> Dict[str, Any]:
        """Analyze the structure of the data"""
        structure = {
            'node_properties': [],
            'edge_properties': [],
            'data_complexity': 'unknown'
        }
        
        if nodes and isinstance(nodes[0], dict):
            structure['node_properties'] = list(nodes[0].keys())
        
        if edges and isinstance(edges[0], dict):
            structure['edge_properties'] = list(edges[0].keys())
        
        # Determine complexity
        if len(nodes) <= 10 and len(edges) <= 10:
            structure['data_complexity'] = 'simple'
        elif len(nodes) <= 50 and len(edges) <= 50:
            structure['data_complexity'] = 'medium'
        else:
            structure['data_complexity'] = 'complex'
        
        return structure
    
    def _print_file_summary(self, analysis: FileAnalysis):
        """Print summary for a single file"""
        if not analysis.exists:
            print(f"❌ {analysis.filename} - FILE NOT FOUND")
            return
        
        print(f"✅ {analysis.filename}")
        print(f"   Size: {analysis.file_size:,} bytes")
        print(f"   D3 Version: {analysis.d3_version}")
        print(f"   Data: {analysis.node_count} nodes, {analysis.edge_count} edges")
        print(f"   Features: sidebar={analysis.has_sidebar}, controls={analysis.has_controls}, zoom={analysis.has_zoom}")
        print(f"   CSS Features: {', '.join(analysis.css_features)}")
        print(f"   JS Features: {', '.join(analysis.js_features)}")
    
    def _print_comparison(self, results: Dict[str, FileAnalysis]):
        """Print comparison table"""
        print("\n📊 COMPARISON TABLE")
        print("=" * 80)
        print(f"{'Feature':<20} {'Basic':<15} {'Enhanced':<15} {'Corrected':<15}")
        print("-" * 80)
        
        # Get analyses
        basic = results.get('network_d3.html')
        enhanced = results.get('real_network_d3.html')
        corrected = results.get('corrected_network_d3.html')
        
        analyses = [basic, enhanced, corrected]
        
        # Compare features
        features = [
            ('File Size', lambda a: f"{a.file_size:,}B" if a and a.exists else "N/A"),
            ('Nodes', lambda a: str(a.node_count) if a and a.exists else "N/A"),
            ('Edges', lambda a: str(a.edge_count) if a and a.exists else "N/A"),
            ('Sidebar', lambda a: "✅" if a and a.exists and a.has_sidebar else "❌"),
            ('Controls', lambda a: "✅" if a and a.exists and a.has_controls else "❌"),
            ('Zoom/Pan', lambda a: "✅" if a and a.exists and a.has_zoom else "❌"),
            ('Tooltips', lambda a: "✅" if a and a.exists and a.has_tooltips else "❌"),
        ]
        
        for feature_name, getter in features:
            values = [getter(a) for a in analyses]
            print(f"{feature_name:<20} {values[0]:<15} {values[1]:<15} {values[2]:<15}")
        
        # Recommendation
        print("\n🎯 AUTOMATED RECOMMENDATION")
        print("-" * 30)
        
        scores = {}
        for filename, analysis in results.items():
            if not analysis.exists:
                continue
            
            score = 0
            score += analysis.node_count  # More nodes = better
            score += analysis.edge_count * 2  # Edges are more important
            score += 10 if analysis.has_sidebar else 0
            score += 10 if analysis.has_controls else 0
            score += 5 if analysis.has_zoom else 0
            score += 5 if analysis.has_tooltips else 0
            score += len(analysis.css_features) * 2
            score += len(analysis.js_features) * 2
            
            scores[filename] = score
        
        if scores:
            best_file = max(scores.items(), key=lambda x: x[1])
            print(f"Best file: {best_file[0]} (score: {best_file[1]})")
            
            print("\nAll scores:")
            for filename, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                print(f"  {filename}: {score}")
    
    def _save_analysis(self, results: Dict[str, FileAnalysis]):
        """Save analysis results to JSON file"""
        output_dir = self.project_root / "tests_phase_1_1_1"
        output_dir.mkdir(exist_ok=True)
        
        # Convert to serializable format
        serializable_results = {}
        for filename, analysis in results.items():
            serializable_results[filename] = {
                'filename': analysis.filename,
                'exists': analysis.exists,
                'file_size': analysis.file_size,
                'd3_version': analysis.d3_version,
                'node_count': analysis.node_count,
                'edge_count': analysis.edge_count,
                'has_sidebar': analysis.has_sidebar,
                'has_controls': analysis.has_controls,
                'has_zoom': analysis.has_zoom,
                'has_tooltips': analysis.has_tooltips,
                'data_structure': analysis.data_structure,
                'css_features': analysis.css_features,
                'js_features': analysis.js_features
            }
        
        output_file = output_dir / "automated_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Analysis saved to: {output_file}")


def main():
    """Run automated structure test"""
    test = AutomatedStructureTest()
    results = test.run_analysis()
    
    print(f"\n✅ Automated analysis complete!")
    print(f"📊 Analyzed {len(results)} files")
    print(f"📁 Results saved to tests_phase_1_1_1/automated_analysis.json")


if __name__ == "__main__":
    main()