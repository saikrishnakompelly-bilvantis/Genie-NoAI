import os

def merge_files(output_file, input_files):
    with open(output_file, 'wb') as f:
        for file in input_files:
            with open(file, 'rb') as chunk_file:
                f.write(chunk_file.read())

if __name__ == "__main__":
    output_file = 'path/to/merged.zip'
    input_files = [
        'path/to/large.zip.part0',
        'path/to/large.zip.part1',
        # Add all parts here
    ]
    merge_files(output_file, input_files)