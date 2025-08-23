#!/usr/bin/env python3
"""
MP4 Recovery Script
Attempts to repair MP4 files with missing moov atoms by using a reference file
from the same device with similar characteristics.
"""

import struct
import sys
import os
from pathlib import Path

def read_atoms(file_path, max_atoms=50):
    """Read and parse MP4 atoms from a file."""
    atoms = []
    with open(file_path, 'rb') as f:
        while len(atoms) < max_atoms:
            try:
                size_bytes = f.read(4)
                if len(size_bytes) < 4:
                    break
                
                atom_type = f.read(4)
                if len(atom_type) < 4:
                    break
                
                size = struct.unpack('>I', size_bytes)[0]
                
                if size < 8:
                    break
                
                atoms.append({
                    'type': atom_type.decode('ascii', errors='ignore'),
                    'size': size,
                    'offset': f.tell() - 8
                })
                
                # Skip to next atom
                if size > 8:
                    f.seek(f.tell() + size - 8)
                    
            except (struct.error, UnicodeDecodeError, OSError):
                break
                
    return atoms

def extract_moov_atom(reference_file):
    """Extract the moov atom from a working reference file."""
    atoms = read_atoms(reference_file)
    
    with open(reference_file, 'rb') as f:
        for atom in atoms:
            if atom['type'] == 'moov':
                f.seek(atom['offset'])
                moov_data = f.read(atom['size'])
                return moov_data
    
    return None

def find_mdat_atom(corrupted_file):
    """Find the mdat atom in the corrupted file."""
    atoms = read_atoms(corrupted_file)
    
    for atom in atoms:
        if atom['type'] == 'mdat':
            return atom
    
    return None

def repair_mp4(corrupted_file, reference_file, output_file):
    """Attempt to repair corrupted MP4 by inserting moov atom from reference."""
    print(f"Analyzing corrupted file: {corrupted_file}")
    print(f"Using reference file: {reference_file}")
    
    # Extract moov atom from reference
    moov_data = extract_moov_atom(reference_file)
    if not moov_data:
        print("ERROR: Could not find moov atom in reference file")
        return False
    
    print(f"Extracted moov atom: {len(moov_data)} bytes")
    
    # Find mdat atom in corrupted file
    mdat_atom = find_mdat_atom(corrupted_file)
    if not mdat_atom:
        print("ERROR: Could not find mdat atom in corrupted file")
        return False
    
    print(f"Found mdat atom at offset: {mdat_atom['offset']}, size: {mdat_atom['size']}")
    
    # Read the beginning of corrupted file (up to mdat)
    with open(corrupted_file, 'rb') as f:
        header_data = f.read(mdat_atom['offset'])
    
    # Read the mdat atom and remaining data
    with open(corrupted_file, 'rb') as f:
        f.seek(mdat_atom['offset'])
        mdat_and_remainder = f.read()
    
    # Write repaired file
    print(f"Writing repaired file: {output_file}")
    with open(output_file, 'wb') as f:
        # Write original header
        f.write(header_data)
        
        # Write moov atom from reference
        f.write(moov_data)
        
        # Write mdat and remainder
        f.write(mdat_and_remainder)
    
    print("Repair attempt completed!")
    return True

def main():
    corrupted_file = "/Volumes/External/2025/May/26th/video-001-2025-05-26.mp4"
    reference_file = "/Volumes/External/2025/May/26th/video-002-2025-05-26.mp4"
    output_file = "/Volumes/External/2025/May/26th/video-001-2025-05-26-repaired.mp4"
    
    if not os.path.exists(corrupted_file):
        print(f"ERROR: Corrupted file not found: {corrupted_file}")
        return 1
        
    if not os.path.exists(reference_file):
        print(f"ERROR: Reference file not found: {reference_file}")
        return 1
    
    success = repair_mp4(corrupted_file, reference_file, output_file)
    
    if success:
        print(f"\nRepair completed! Testing the repaired file...")
        # Test the repaired file
        test_result = os.system(f'ffprobe -v quiet -show_format "{output_file}" > /dev/null 2>&1')
        if test_result == 0:
            print("✅ SUCCESS: Repaired file appears to be valid!")
        else:
            print("⚠️  WARNING: Repaired file may still have issues")
    else:
        print("❌ FAILED: Could not repair the file")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())