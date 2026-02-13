#!/usr/bin/env python3
"""
Paper Analysis Tool for DEVSIM TCAD Research
Extracts and analyzes academic papers with focus on semiconductor device simulation
"""

import sys
import re
from pathlib import Path

class PaperAnalyzer:
    """Analyze academic papers for TCAD device simulation content"""
    
    def __init__(self, text_content):
        self.text = text_content
        self.sections = {}
        self.metadata = {}
        self._parse_structure()
    
    def _parse_structure(self):
        """Parse paper structure into sections"""
        # Common section headers
        section_patterns = [
            (r'Abstract', 'abstract'),
            (r'Introduction', 'introduction'),
            (r'(?:Methods?|Methodology|Experimental|Simulation Setup)', 'methods'),
            (r'Results?(?:\s+and\s+Discussion)?', 'results'),
            (r'Discussion', 'discussion'),
            (r'Conclusion', 'conclusion'),
            (r'References', 'references')
        ]
        
        lines = self.text.split('\n')
        current_section = 'header'
        current_content = []
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check for section headers
            found_section = False
            for pattern, section_name in section_patterns:
                if re.match(rf'^\s*{pattern}\s*$', line_stripped, re.IGNORECASE):
                    if current_content:
                        self.sections[current_section] = '\n'.join(current_content)
                    current_section = section_name
                    current_content = []
                    found_section = True
                    break
            
            if not found_section:
                current_content.append(line)
        
        # Save last section
        if current_content:
            self.sections[current_section] = '\n'.join(current_content)
    
    def extract_metadata(self):
        """Extract paper metadata"""
        lines = self.text.split('\n')[:50]  # Check first 50 lines
        text_block = '\n'.join(lines)
        
        # Extract title (usually after "Title:" or in first few lines)
        title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', text_block, re.IGNORECASE)
        if not title_match:
            # Try first non-empty line that looks like a title
            for line in lines:
                if len(line.strip()) > 20 and not line.strip().startswith('---'):
                    self.metadata['title'] = line.strip()
                    break
        else:
            self.metadata['title'] = title_match.group(1).strip()
        
        # Extract DOI
        doi_match = re.search(r'doi[.:]\s*(10\.\d{4,}/\S+)', text_block, re.IGNORECASE)
        if doi_match:
            self.metadata['doi'] = doi_match.group(1)
        
        # Extract authors (look for email patterns or author list)
        author_pattern = r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*·|\n|et\s+al|University|Institute'
        authors = re.findall(author_pattern, text_block)
        if authors:
            self.metadata['authors'] = list(set(authors))[:5]  # Top 5 authors
        
        return self.metadata
    
    def extract_device_structure(self):
        """Extract device layer structure from TCAD papers"""
        structure = []
        
        # Look for tables with layer information
        table_pattern = r'(Layer|Material|Thickness|Doping|Bandgap).*\n[\s\S]*?(?=\n\n|\Z)'
        tables = re.findall(table_pattern, self.text, re.IGNORECASE)
        
        # Look for layer descriptions
        layer_patterns = [
            r'(\w+)\s+(?:layer|absorber|barrier|contact).*?(\d+(?:\.\d+)?)\s*(?:µm|nm|um)',
            r'(\w+)[/\s]+(\w+)\s+(?:superlattice|alloy)',
            r'(?:doped|doping).*?(\d+(?:\.\d+)?)\s*[×x]\s*10\^?(\d+)'
        ]
        
        for pattern in layer_patterns:
            matches = re.findall(pattern, self.text, re.IGNORECASE)
            structure.extend(matches)
        
        return structure
    
    def extract_equations(self):
        """Extract key equations"""
        equations = []
        
        # Look for equation references
        eq_patterns = [
            r'Poisson[\'\s]?s?\s+equation',
            r'drift-diffusion',
            r'continuity\s+equation',
            r'Fermi[\-\s]?Dirac',
            r'SRH\s+recombination',
            r'Auger\s+(?:1|7)'
        ]
        
        for pattern in eq_patterns:
            if re.search(pattern, self.text, re.IGNORECASE):
                equations.append(pattern.replace('\\', ''))
        
        return equations
    
    def extract_simulation_parameters(self):
        """Extract simulation parameters"""
        params = {}
        
        # Temperature
        temp_match = re.findall(r'(\d+)\s*K(?:\s|$|\.|,)', self.text)
        if temp_match:
            params['temperatures'] = list(set(temp_match))
        
        # Wavelength/Cutoff
        cutoff_match = re.findall(r'(\d+(?:\.\d+)?)\s*µm', self.text)
        if cutoff_match:
            params['cutoff_wavelengths'] = cutoff_match[:5]  # First 5
        
        # Bandgap
        bandgap_match = re.findall(r'(\d+(?:\.\d+)?)\s*(?:meV|eV)', self.text)
        if bandgap_match:
            params['bandgaps'] = bandgap_match[:5]
        
        # Doping concentrations
        doping_pattern = r'(\d+(?:\.\d+)?)\s*[×x]\s*10\^?(\d+)\s*(?:cm\^-3|/cm3)'
        doping_matches = re.findall(doping_pattern, self.text)
        if doping_matches:
            params['doping_concentrations'] = doping_matches[:5]
        
        return params
    
    def generate_summary(self):
        """Generate comprehensive summary"""
        self.extract_metadata()
        
        summary = []
        summary.append("=" * 70)
        summary.append("PAPER ANALYSIS SUMMARY")
        summary.append("=" * 70)
        
        # Metadata
        summary.append("\n[METADATA]")
        for key, value in self.metadata.items():
            if isinstance(value, list):
                summary.append(f"  {key.capitalize()}: {', '.join(value)}")
            else:
                summary.append(f"  {key.capitalize()}: {value}")
        
        # Abstract
        if 'abstract' in self.sections:
            summary.append("\n[ABSTRACT] ABSTRACT:")
            abstract = self.sections['abstract'][:500] + "..." if len(self.sections['abstract']) > 500 else self.sections['abstract']
            summary.append(f"  {abstract}")
        
        # Device Structure
        structure = self.extract_device_structure()
        if structure:
            summary.append("\n[DEVICE STRUCTURE] DEVICE STRUCTURE:")
            for item in structure[:10]:  # Limit output
                summary.append(f"  • {item}")
        
        # Equations
        equations = self.extract_equations()
        if equations:
            summary.append("\n[EQUATIONS] EQUATIONS/MODELS:")
            for eq in equations:
                summary.append(f"  • {eq}")
        
        # Parameters
        params = self.extract_simulation_parameters()
        if params:
            summary.append("\n[SIMULATION PARAMETERS]  SIMULATION PARAMETERS:")
            for key, values in params.items():
                summary.append(f"  • {key}: {values}")
        
        # Methods section summary
        if 'methods' in self.sections:
            summary.append("\n[METHODOLOGY] METHODOLOGY:")
            methods = self.sections['methods'][:800] + "..." if len(self.sections['methods']) > 800 else self.sections['methods']
            # Split into bullet points
            sentences = re.split(r'(?<=[.!?])\s+', methods)
            for sent in sentences[:5]:
                if len(sent.strip()) > 20:
                    summary.append(f"  • {sent.strip()}")
        
        # Key results
        if 'results' in self.sections:
            summary.append("\n[KEY RESULTS] KEY RESULTS:")
            results = self.sections['results'][:800] + "..." if len(self.sections['results']) > 800 else self.sections['results']
            sentences = re.split(r'(?<=[.!?])\s+', results)
            for sent in sentences[:5]:
                if len(sent.strip()) > 20:
                    summary.append(f"  • {sent.strip()}")
        
        summary.append("\n" + "=" * 70)
        
        return '\n'.join(summary)
    
    def compare_with_devsim_examples(self):
        """Compare paper content with DEVSIM examples"""
        comparisons = []
        
        text_lower = self.text.lower()
        
        # Check for relevant DEVSIM examples
        example_mappings = {
            'capacitor': ['cap2', 'capacitance', 'cap1d', 'cap2d'],
            'diode': ['diode', 'pn junction', 'heterojunction'],
            'mosfet': ['mos', 'mos_2d'],
            'transient': ['transient', 'time-dependent'],
            'circuit': ['circuit', 'rc', 'resistor'],
            'quantum': ['quantum', 'tunneling', 'superlattice']
        }
        
        for example_type, keywords in example_mappings.items():
            for keyword in keywords:
                if keyword in text_lower:
                    comparisons.append(f"  • {example_type.capitalize()} examples: testing/{example_type}*.py")
                    break
        
        return comparisons


def main():
    """Main function for command-line usage"""
    if len(sys.argv) < 2:
        print("Usage: python paper_analyzer.py <paper_text_file>")
        print("Example: python paper_analyzer.py papers/JEM2025_extracted.txt")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    analyzer = PaperAnalyzer(content)
    
    # Generate summary and save to file
    summary = analyzer.generate_summary()
    
    # Save to output file
    output_file = file_path.replace('.txt', '_analysis.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(summary)
        f.write("\n\n[RELEVANT DEVSIM EXAMPLES]:\n")
        examples = analyzer.compare_with_devsim_examples()
        if examples:
            for ex in examples:
                f.write(ex + "\n")
        else:
            f.write("  - Check testing/ directory for similar device structures\n")
            f.write("  - Look at examples/diode/ for drift-diffusion models\n")
        f.write("\n[DONE] Analysis complete!\n")
    
    print(f"Analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
