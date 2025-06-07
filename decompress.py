# decompress.py
import sys

# Define constants for our PXL format
MAGIC_NUMBER = b"PXL"
NO_SUB_BYTE = 0x00

def decompress(input_file, output_file):
    """Decompresses a .pxl file."""
    print(f"Reading '{input_file}'...")
    try:
        with open(input_file, 'rb') as f:
            compressed_content = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return
        
    # --- 1. Read Header ---
    if not compressed_content.startswith(MAGIC_NUMBER):
        print("Error: This is not a valid .pxl file (missing magic number).")
        return
        
    header = compressed_content[3:7]
    data_start_index = 7

    sub_byte, orig_byte1, orig_byte2, rle_marker_byte = header
    
    compressed_data = compressed_content[data_start_index:]
    
    # --- 2. Expand Run-Length Encoding ---
    rle_expanded_data = bytearray()
    i = 0
    while i < len(compressed_data):
        byte = compressed_data[i]
        if byte == rle_marker_byte:
            # This is an RLE sequence: MARKER, COUNT, BYTE
            if i + 2 >= len(compressed_data):
                print("Error: Corrupted RLE sequence at end of file.")
                return
            run_count = compressed_data[i+1]
            run_byte = compressed_data[i+2]
            rle_expanded_data.extend([run_byte] * run_count)
            i += 3
        else:
            rle_expanded_data.append(byte)
            i += 1
            
    # --- 3. Expand Substitution ---
    if sub_byte != NO_SUB_BYTE:
        print(f"Found substitution rule: byte {sub_byte} -> pair ({orig_byte1}, {orig_byte2})")
        byte_pair_to_restore = bytes([orig_byte1, orig_byte2])
        # Use bytearray's replace method.
        # It's not the most efficient for huge files, but clear and simple.
        final_data = rle_expanded_data.replace(bytes([sub_byte]), byte_pair_to_restore)
    else:
        print("No substitution was used during compression.")
        final_data = rle_expanded_data
        
    # --- 4. Write final data ---
    print(f"Writing decompressed data to '{output_file}'...")
    with open(output_file, 'wb') as f:
        f.write(final_data)

    print("\n--- Decompression Summary ---")
    print(f"Compressed size: {len(compressed_content)} bytes")
    print(f"Decompressed size: {len(final_data)} bytes")
    print("Done.")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python decompress.py <input_file.pxl> <output_file>")
        sys.exit(1)

    decompress(sys.argv[1], sys.argv[2])
