import paramiko
import re
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define SSH connection parameters
hostname = '34.68.7.98'
port = 22
username = 'np-mrd'
password = ''  # or use a private key for better security

# Path to the log file on the remote server
log_file_path = '~/project/shared/log/production.log'

# Email content
from_email = "Karan02sidhu@gmail.com"
to_email = "Karan02sidhu@gmail.com"
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_password = "xxxxxxxxxxx"  # Hard-coded Gmail password or app-specific password

def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(from_email, email_password)  # Login to the email account
        server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()
        print("Disconnected from the SMTP server")

def analyze_errors(log_entries):
    error_patterns = [
        re.compile(r'Rendering 404 due to exception:'),
        re.compile(r'FATAL')  # Exception pattern
    ]

    previous_line = ""
    for line in log_entries:
        if any(pattern.search(line) for pattern in error_patterns):
            email_body = f"Error detected:\nPrevious line: {previous_line.strip()}\nError line: {line.strip()}\n"
            print(previous_line.strip())  # Print the previous line
            print(line.strip())
            empty_line_found = False
            for next_line in log_entries[log_entries.index(line)+1:]:
                email_body += f"{next_line.strip()}\n"
                print(next_line.strip())
                if next_line.strip() == "":
                    if empty_line_found:
                        break
                    empty_line_found = True
            send_email("Log Error Detected", email_body)
        previous_line = line

def analyze_timeouts(log_entries):
    last_completed_index = 0

    for index, line in enumerate(log_entries):
        completed_match = re.search(r'(Completed.*) (\d+)ms', line)
        if completed_match:
            duration_ms = int(completed_match.group(2))
            if duration_ms > 1000:
                email_body = f"Timeout detected:\nTimeout line: {line.strip()}\n"
                print(f"\033[91mTIMEOUT FOUND:\033[0m {line.strip()}")
                print("-" * 80)
                
                max_duration = 0.0
                cause_of_timeout = ""
                
                for entry in log_entries[last_completed_index+1:index]:
                    entry_match = re.search(r'\(\d+\.\d+ms\)', entry)
                    if entry_match:
                        entry_duration_str = entry_match.group(0).strip('()ms')
                        entry_duration = float(entry_duration_str)
                        if entry_duration > max_duration:
                            max_duration = entry_duration
                            cause_of_timeout = entry
                    #email_body += f"{entry}\n"

                email_body += f"Cause of Timeout: {cause_of_timeout}\n"
                print("-" * 80)
                print(f"\033[91mCause of Timeout:\033[0m {cause_of_timeout}")
                print("=" * 80)
                send_email("Timeout Detected", email_body)
                last_completed_index = index  # Update to the current completed log index

def analyze_log_file(log_entries):
    analyze_errors(log_entries)
    analyze_timeouts(log_entries)

# Function to read the latest logs from the remote server
def read_latest_logs(hostname, port, username, password, log_file_path, last_position, initial_read):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
   
    try:
        ssh.connect(hostname, port=port, username=username, password=password)
        print('Connected')

        if initial_read:
            command = f'tail -n 1000 {log_file_path}'
        else:
            command = f'tail -c +{last_position} {log_file_path}'
        
        stdin, stdout, stderr = ssh.exec_command(command)
        lines = stdout.readlines()
        
        if lines:
            if initial_read:
                new_last_position = sum(len(line) for line in lines)
            else:
                new_last_position = last_position + sum(len(line) for line in lines)
            analyze_log_file(lines)
            return new_last_position

    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()
    
    return last_position

def monitor_log_file():
    last_position = 0
    initial_read = True
    while True:
        last_position = read_latest_logs(hostname, port, username, password, log_file_path, last_position, initial_read)
        initial_read = False
        time.sleep(60)  # Check for new content every 60 seconds

if __name__ == "__main__":
    monitor_log_file()
