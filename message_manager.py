import os
import ast

class MessageManager:
    def __init__(self, saved_messages_listbox):
        self.saved_messages_listbox = saved_messages_listbox
        self.saved_messages_file = "saved_messages.txt"
        self.saved_messages = []
        self.current_log_file = None

    def save_message(self, log_file, message_id, name, details):
        # Create a dictionary to represent the saved message
        saved_message = {
            "log_file": log_file,
            "message_id": message_id,
            "name": name,
            "details": details,
        }

        # Save the message to a file
        with open(self.saved_messages_file, "a") as f:
            f.write(f"{saved_message}\n")

        # Add to in-memory list and update the listbox
        self.saved_messages.append(saved_message)
        self.saved_messages_listbox.insert('end', f"{name}: {details[3]}")

    def load_saved_messages(self, log_file):
        self.saved_messages_listbox.delete(0, 'end')
        self.saved_messages.clear()
        self.current_log_file = log_file

        if not os.path.exists(self.saved_messages_file):
            return

        with open(self.saved_messages_file, "r") as f:
            for line in f:
                saved_message = ast.literal_eval(line.strip())
                if saved_message["log_file"] == log_file:
                    self.saved_messages.append(saved_message)
                    name = saved_message["name"]
                    message_text = saved_message["details"][3]
                    self.saved_messages_listbox.insert('end', f"{name}: {message_text}")

    def get_saved_message(self, index):
        if index < len(self.saved_messages):
            return self.saved_messages[index]
        return None
