import sys

def hex_to_string(input_file, output_file):
    hex_strings = None
    dic = {}
    with open(input_file, 'r') as f:
        hex_strings = f.readlines()

    with open(output_file, 'w', encoding='utf-8') as file:
        for hex_string in hex_strings:
            if(dic.get(hex_string)!=None):
                continue
            dic[hex_string] = 1
            try:
                plain_string = bytearray.fromhex(hex_string).decode('utf-8')
                file.write(f"{hex_string}: {plain_string}\n")
            except UnicodeDecodeError as e:
                try:
                    plain_string = bytearray.fromhex(hex_string).decode('latin-1')
                    file.write(f"{hex_string}: {plain_string}\n")
                except UnicodeDecodeError as e:
                    file.write(f"Latin-1 decoding error: {e}\n")
                    return
            reencoded_hex = "".join([hex(ord(x))[2:].zfill(2) for x in plain_string])
            file.write(f"Re-encoded hex: {reencoded_hex}\n")
            file.write(f"--------------------------------------------------------------------------------------------\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    hex_to_string(input_file, output_file)
