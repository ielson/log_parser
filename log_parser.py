import re
from datetime import datetime


class LogParser:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def parse(self, file_path):
        pattern = re.compile(r"\[(.*?)\]\[(.*?)\]\[(.*?)\] (.*)")
        messages = []
        try:
            with open(file_path, "r") as file:
                current_message = None
                for idx, line in enumerate(file):
                    match = pattern.match(line.strip())
                    if match:
                        # If a new log entry starts, save the previous one
                        if current_message:
                                messages.append(current_message)
                        timestamp, level, module, message = match.groups()
                        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                        current_message = {
                            "id": idx,  # Unique ID for the message
                            "timestamp": dt.timestamp(),
                            # "timestamp_str": timestamp_str,  # Keep original string for display
                            # "time_only_str": dt.strftime("%H:%M:%S.%f")[
                            #     :-3
                            # ],  # Time with milliseconds
                            "level": level,
                            "module": module,
                            "message": message,
                        }
                    else:
                        if current_message:
                            current_message["message"] += " " + line

                # append the last msg
                if current_message:
                    messages.append(current_message)
                return messages

            if not self.messages:
                # messagebox.showinfo(
                #     "No messages", "No valid log messages found in the file."
                # )
                return

        except Exception as e:
            print(f"Failed to read log file: {e}")  # Print error to terminal
            # messagebox.showerror("Error", f"Failed to read log file: {e}")

    def get_time_range(self, messages):
        timestamps = [msg["timestamp"] for msg in messages]
        return min(timestamps), max(timestamps)

    def set_start_time(self, start_time):
        self.start_time = start_time

    def set_end_time(self, end_time):
        self.end_time = end_time
