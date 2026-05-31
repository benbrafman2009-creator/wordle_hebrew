
import threading
import queue

# Update your AsyncMessages class with these methods
# This should be in your AsyncMessages.py file

class AsyncMessages:
    def __init__(self):
        self.sock_by_user = {}  # {username: socket}
        self.message_queues = {}  # {socket: queue.Queue()}

    def add_new_socket(self, sock):
        """Add a new socket to track"""
        self.message_queues[sock] = queue.Queue()

    def delete_socket(self, sock):
        """Remove socket when client disconnects"""
        if sock in self.message_queues:
            del self.message_queues[sock]

    def queue_message_for_user(self, username, message):
        """Queue a message to be sent to a specific user"""
        if username in self.sock_by_user:
            sock = self.sock_by_user[username]
            if sock in self.message_queues:
                self.message_queues[sock].put(message)
                print(f"[QUEUE] Message queued for {username}: {message[:50]}")
                return True
        print(f"[QUEUE] Could not queue message for {username} - not online")
        return False

    def get_async_messages_to_send(self, sock):
        """Get all queued messages for a socket"""
        messages = []
        if sock in self.message_queues:
            try:
                while True:
                    msg = self.message_queues[sock].get_nowait()
                    messages.append(msg)
            except queue.Empty:
                pass
        return messages

    def broadcast_message(self, message, exclude_sock=None):
        """Broadcast a message to all connected users"""
        for sock in self.message_queues:
            if exclude_sock and sock == exclude_sock:
                continue
            self.message_queues[sock].put(message)


