import re
import sys

def main(log_file_path):
    # Define the error patterns
    error_patterns = [
         re.compile(r'Rendering 404 due to exception:'),
        re.compile(r'FATAL')                                             # the reason fatal prints 406 from code and keyword search shows 416 is because some hex code has jfatal
    ]

    try:
        with open(log_file_path, 'r', encoding="utf-8") as file:
            i = 0
            for line in file:
                # Check if the line matches any of the error patterns
                if any(pattern.search(line) for pattern in error_patterns):
                    i += 1
                    print(line.strip())
                    # Print following lines until an empty line is encountered
                    empty_line_found = False
                    for next_line in file:
                        print(next_line.strip())
                        if next_line.strip() == "":
                            if empty_line_found:
                                break  # Stop if we find a second empty line
                            empty_line_found = True 
    except FileNotFoundError:
        print(f"The file {log_file_path} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    print(i)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python log_parser.py <log_file_path>")
    else:
        main(sys.argv[1])
