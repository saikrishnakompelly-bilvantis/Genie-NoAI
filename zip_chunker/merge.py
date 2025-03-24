import os

def merge_files(output_file, input_files):
    with open(output_file, 'wb') as f:
        for file in input_files:
            with open(file, 'rb') as chunk_file:
                f.write(chunk_file.read())

if __name__ == "__main__":
    output_file = r"C:\Users\kesava.kondepudi\Desktop\test\Genie-NoAI\Genie-Secrets.zip"
    input_files = [r"C:\Users\kesava.kondepudi\Desktop\test\Genie-NoAI\dist\Genie-Secrets.zip.part0",
r"C:\Users\kesava.kondepudi\Desktop\test\Genie-NoAI\dist\Genie-Secrets.zip.part1",
r"C:\Users\kesava.kondepudi\Desktop\test\Genie-NoAI\dist\Genie-Secrets.zip.part2",
r"C:\Users\kesava.kondepudi\Desktop\test\Genie-NoAI\dist\Genie-Secrets.zip.part3"]
    merge_files(output_file, input_files)