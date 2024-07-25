import re
import sys

def analyze_log_file(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        log_entries = []
        last_completed_index = 0

        for index, line in enumerate(file):
            log_entries.append(line.strip())

            # Check for timeouts longer than 1 second in Completed log entries
            completed_match = re.search(r'(Completed.*) (\d+)ms', line)
            if completed_match:
                duration_ms = int(completed_match.group(2))
                if duration_ms > 1000:
                    print(f"\033[91mTIMEOUT FOUND:\033[0m {line.strip()}")
                    print("Log entries leading to the timeout:")
                    print("-" * 80)
                    
                    max_duration = 0.0
                    cause_of_timeout = ""
                    
                    for entry in log_entries[last_completed_index+1:-1]:
                        entry_match = re.search(r'\(\d+\.\d+ms\)', entry)
                        if entry_match:
                            entry_duration_str = entry_match.group(0).strip('()ms')
                            entry_duration = float(entry_duration_str)
                            if entry_duration > max_duration:
                                max_duration = entry_duration
                                cause_of_timeout = entry
                        print(entry) #----> if u want to see more than just a single cause 

                    print("-" * 80)
                    print(f"\033[91mCause of Timeout:\033[0m {cause_of_timeout}")
                    print("=" * 80)
                    log_entries = log_entries[last_completed_index + 1:]  # Retain entries after the detected timeout
                else:
                    last_completed_index = len(log_entries) - 1  # Update to the current completed log index

def main():
    if len(sys.argv) != 2:
        print("Usage: python script_name.py path/to/your/logfile.log")
        sys.exit(1)

    log_file_path = sys.argv[1]
    analyze_log_file(log_file_path)

if __name__ == "__main__":
    main()
