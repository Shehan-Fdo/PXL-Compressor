# compress.py
import sys
from collections import Counter

# Define constants for our PXL format
MAGIC_NUMBER = b"PXL"
# We'll use a high-value byte as our RLE marker, assuming it's less common.
RLE_MARKER_BYTE = 0xFF 
# A byte to indicate no substitution was made
NO_SUB_BYTE = 0x00

def find_best_pair(data):
    """Finds the most frequent pair of adjacent bytes in the data."""
    if len(data) < 2:
        return None
    
    pairs = Counter()
    for i in range(len(data) - 1):
        pair = (data[i], data[i+1])
        pairs[pair] += 1
        
    if not pairs:
        return None

    # Find the most common pair, but only if it's worth compressing
    most_common_pair, count = pairs.most_common(1)[0]
    if count > 1:
        return most_common_pair
    return None

def find_substitution_byte(data, pair_to_replace):
    """Finds a byte value (128-254) that is not in the data."""
    used_bytes = set(data)
    if pair_to_replace:
        used_bytes.add(pair_to_replace[0])
        used_bytes.add(pair_to_replace[1])

    # Search for an unused byte code in the extended ASCII range
    # We avoid 0xFF because it's our RLE marker
    for byte_val in range(128, 255):
        if byte_val not in used_bytes:
            return byte_val
    return None # No available byte for substitution

def compress(input_file, output_file):
    """Compresses a file using the Sub-RLE PXL algorithm."""
    print(f"Reading '{input_file}'...")
    try:
        with open(input_file, 'rb') as f:
            original_data = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return

    if not original_data:
        print("Warning: Input file is empty. Creating an empty .pxl file.")
        with open(output_file, 'wb') as f:
            # Write a minimal header for an empty file
            f.write(MAGIC_NUMBER)
            f.write(bytes([NO_SUB_BYTE, 0, 0, RLE_MARKER_BYTE]))
        return

    # --- 1. Analysis and Substitution ---
    best_pair = find_best_pair(original_data)
    sub_byte = None
    processed_data = original_data
    
    if best_pair:
        sub_byte = find_substitution_byte(original_data, best_pair)

    if sub_byte:
        print(f"Found best pair to substitute: {best_pair} with byte {sub_byte}")
        # Create a new byte array by replacing the pair
        processed_data = original_data.replace(bytes(best_pair), bytes([sub_byte]))
    else:
        print("No beneficial substitution found. Skipping substitution step.")
        
    # --- 2. Run-Length Encoding ---
    compressed_data = bytearray()
    i = 0
    while i < len(processed_data):
        current_byte = processed_data[i]
        run_count = 1
        # Find how long the run is
        while (i + run_count < len(processed_data) and 
               processed_data[i + run_count] == current_byte and
               run_count < 255): # Max run count is 255
            run_count += 1
        
        # If a run is found and is worth encoding (length > 3)
        # or if the byte to be encoded is the RLE marker itself
        if run_count > 3 or current_byte == RLE_MARKER_BYTE:
            compressed_data.append(RLE_MARKER_BYTE)
            compressed_data.append(run_count)
            compressed_data.append(current_byte)
            i += run_count
        else:
            # Otherwise, just write the byte(s) as is
            compressed_data.extend(processed_data[i:i+run_count])
            i += run_count

    # --- 3. Write PXL file ---
    print(f"Writing compressed data to '{output_file}'...")
    with open(output_file, 'wb') as f:
        # Write Header
        f.write(MAGIC_NUMBER)
        if sub_byte:
            f.write(bytes([sub_byte, best_pair[0], best_pair[1], RLE_MARKER_BYTE]))
        else:
            # Write a header indicating no substitution
            f.write(bytes([NO_SUB_BYTE, 0, 0, RLE_MARKER_BYTE]))
        
        # Write Data
        f.write(compressed_data)

    original_size = len(original_data)
    compressed_size = len(compressed_data) + 7 # 7 bytes for the header
    ratio = compressed_size / original_size if original_size > 0 else 0
    print("\n--- Compression Summary ---")
    print(f"Original size: {original_size} bytes")
    print(f"Compressed size: {compressed_size} bytes")
    print(f"Compression ratio: {ratio:.2%}")
    print("Done.")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python compress.py <input_file> <output_file.pxl>")
        sys.exit(1)
    
    compress(sys.argv[1], sys.argv[2])
