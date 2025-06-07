# pxl.py
import sys
import argparse
from collections import Counter

# --- PXL Format Constants ---
MAGIC_NUMBER = b"PXL"
RLE_MARKER_BYTE = 0xFF
NO_SUB_BYTE = 0x00

#==============================================================================
# COMPRESSION LOGIC
#==============================================================================

def find_best_pair(data):
    # (This function is the same as before)
    if len(data) < 2: return None
    pairs = Counter((data[i], data[i+1]) for i in range(len(data) - 1))
    if not pairs: return None
    most_common_pair, count = pairs.most_common(1)[0]
    return most_common_pair if count > 1 else None

def find_substitution_byte(data, pair_to_replace):
    # (This function is the same as before)
    used_bytes = set(data)
    if pair_to_replace:
        used_bytes.add(pair_to_replace[0])
        used_bytes.add(pair_to_replace[1])
    for byte_val in range(128, 255):
        if byte_val not in used_bytes: return byte_val
    return None

def compress(input_file, output_file):
    """Compresses a file using the Sub-RLE PXL algorithm."""
    print(f"Reading '{input_file}'...")
    try:
        with open(input_file, 'rb') as f:
            original_data = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    # (The rest of the compression logic is the same as before)
    # ... analysis, substitution, RLE, writing file ...
    if not original_data:
        print("Warning: Input file is empty. Creating an empty .pxl file.")
        with open(output_file, 'wb') as f:
            f.write(MAGIC_NUMBER)
            f.write(bytes([NO_SUB_BYTE, 0, 0, RLE_MARKER_BYTE]))
        return

    best_pair = find_best_pair(original_data)
    sub_byte, processed_data = None, original_data
    if best_pair: sub_byte = find_substitution_byte(original_data, best_pair)

    if sub_byte:
        print(f"Found best pair to substitute: {best_pair} with byte {sub_byte}")
        processed_data = original_data.replace(bytes(best_pair), bytes([sub_byte]))
    else:
        print("No beneficial substitution found. Skipping substitution step.")
        
    compressed_data = bytearray()
    i = 0
    while i < len(processed_data):
        current_byte, run_count = processed_data[i], 1
        while (i + run_count < len(processed_data) and 
               processed_data[i + run_count] == current_byte and run_count < 255):
            run_count += 1
        if run_count > 3 or current_byte == RLE_MARKER_BYTE:
            compressed_data.extend([RLE_MARKER_BYTE, run_count, current_byte])
            i += run_count
        else:
            compressed_data.extend(processed_data[i:i+run_count])
            i += run_count

    print(f"Writing compressed data to '{output_file}'...")
    with open(output_file, 'wb') as f:
        f.write(MAGIC_NUMBER)
        if sub_byte:
            f.write(bytes([sub_byte, best_pair[0], best_pair[1], RLE_MARKER_BYTE]))
        else:
            f.write(bytes([NO_SUB_BYTE, 0, 0, RLE_MARKER_BYTE]))
        f.write(compressed_data)

    original_size = len(original_data)
    compressed_size = len(compressed_data) + 7
    ratio = compressed_size / original_size if original_size > 0 else 0
    print("\n--- Compression Summary ---")
    print(f"Original size: {original_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")
    print(f"Compression ratio: {ratio:.2%}\nDone.")

#==============================================================================
# DECOMPRESSION LOGIC
#==============================================================================

def decompress(input_file, output_file):
    """Decompresses a .pxl file."""
    print(f"Reading '{input_file}'...")
    try:
        with open(input_file, 'rb') as f:
            compressed_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    # (The rest of the decompression logic is the same as before)
    # ... read header, expand RLE, expand substitution, write file ...
    if not compressed_content.startswith(MAGIC_NUMBER):
        print("Error: This is not a valid .pxl file (missing magic number).")
        return
        
    header = compressed_content[3:7]
    sub_byte, orig_byte1, orig_byte2, rle_marker_byte = header
    compressed_data = compressed_content[7:]
    
    rle_expanded_data = bytearray()
    i = 0
    while i < len(compressed_data):
        byte = compressed_data[i]
        if byte == rle_marker_byte:
            if i + 2 >= len(compressed_data):
                print("Error: Corrupted RLE sequence at end of file."); return
            run_count, run_byte = compressed_data[i+1], compressed_data[i+2]
            rle_expanded_data.extend([run_byte] * run_count)
            i += 3
        else:
            rle_expanded_data.append(byte)
            i += 1
            
    if sub_byte != NO_SUB_BYTE:
        print(f"Found substitution rule: byte {sub_byte} -> pair ({orig_byte1}, {orig_byte2})")
        final_data = rle_expanded_data.replace(bytes([sub_byte]), bytes([orig_byte1, orig_byte2]))
    else:
        print("No substitution was used during compression.")
        final_data = rle_expanded_data
        
    print(f"Writing decompressed data to '{output_file}'...")
    with open(output_file, 'wb') as f:
        f.write(final_data)

    print("\n--- Decompression Summary ---")
    print(f"Compressed size: {len(compressed_content)} bytes")
    print(f"Decompressed size: {len(final_data)} bytes\nDone.")

#==============================================================================
# MAIN APPLICATION LOGIC
#==============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="PXL Compressor: A custom file compression tool.")
    
    # Add arguments
    parser.add_argument('input_file', help="The input file to process.")
    parser.add_argument('output_file', help="The name for the output file.")
    parser.add_argument('-d', '--decompress', action='store_true', help="Decompress mode. Default is compress.")
    
    args = parser.parse_args()
    
    if args.decompress:
        # Decompression Mode
        print("Mode: Decompression")
        decompress(args.input_file, args.output_file)
    else:
        # Compression Mode (Default)
        print("Mode: Compression")
        compress(args.input_file, args.output_file)
