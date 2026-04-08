import random

class QueueManager:
    """
    Manages the playback queue, including history, shuffle state, and repeat modes.
    Expects generic track objects (like dicts, URLs, or data classes).
    """
    def __init__(self):
        self.base_queue = []     # The original, un-shuffled sequence of tracks
        self.queue = []          # The pending queue of tracks to be played next
        self.prev_history = []   # Buffer of up to 100 previous tracks
        self.current_track = None
        
        self.repeat_mode = "off" # Available modes: "off", "all", "one"
        self.shuffle = False

    def load_queue(self, tracks: list):
        """
        Load a distinct list of tracks, clearing the existing queue and history.
        """
        self.base_queue = list(tracks)
        self.queue = list(tracks)
        if self.shuffle:
            random.shuffle(self.queue)
        self.current_track = None
        self.prev_history.clear()

    def add_track(self, track):
        """
        Append a track to the current queue.
        If shuffling is enabled, it randomly inserts into the pending queue.
        """
        self.base_queue.append(track)
        if self.shuffle:
            if not self.queue:
                self.queue.append(track)
            else:
                insert_pos = random.randint(0, len(self.queue))
                self.queue.insert(insert_pos, track)
        else:
            self.queue.append(track)

    def insert_next(self, track):
        """
        Inserts a track immediately into the next playback sequence position.
        """
        if self.current_track and self.current_track in self.base_queue:
            idx = self.base_queue.index(self.current_track)
            self.base_queue.insert(idx + 1, track)
        else:
            self.base_queue.insert(0, track)
        self.queue.insert(0, track)

    def next_track(self, manual_skip=False):
        """
        Advances the queue and returns the next track.
        
        Args:
            manual_skip (bool): If True, forces skipping to the next track even if 
                                repeat_mode == "one".
        """
        if self.current_track:
            # Handle repeat "one" unless the user explicitly hit skip
            if self.repeat_mode == "one" and not manual_skip:
                return self.current_track

            # Push current to history before moving forward
            self.prev_history.append(self.current_track)
            if len(self.prev_history) > 100:
                self.prev_history.pop(0)

        # Handle reaching the end of the queue
        if not self.queue:
            if self.repeat_mode == "all" and self.base_queue:
                self.queue = list(self.base_queue)
                if self.shuffle:
                    random.shuffle(self.queue)
            else:
                self.current_track = None
                return None

        self.current_track = self.queue.pop(0)
        return self.current_track

    def previous_track(self):
        """
        Goes back to the previous track in the history buffer.
        Saves the currently playing track by putting it back at the front of the next_queue.
        Returns None if history is empty.
        """
        if not self.prev_history:
            return None

        # The current track goes back to the top of the queue
        if self.current_track:
            self.queue.insert(0, self.current_track)

        self.current_track = self.prev_history.pop()
        return self.current_track

    def set_repeat_mode(self, mode: str):
        """
        Set repeat mode block (off, all, or one).
        """
        mode = str(mode).lower()
        if mode in ["off", "all", "one"]:
            self.repeat_mode = mode

    def set_shuffle(self, state: bool):
        """
        Toggles shuffle. Reorganizes the pending queue to respect the new state.
        """
        self.shuffle = bool(state)
        
        if self.shuffle:
            random.shuffle(self.queue)
        else:
            # Try to restore the original un-shuffled order for upcoming tracks.
            if self.current_track and self.current_track in self.base_queue:
                # Find current track index in base_queue and restore the rest
                idx = self.base_queue.index(self.current_track)
                self.queue = self.base_queue[idx+1:]
            else:
                self.queue = list(self.base_queue)

    def clear(self):
        """
        Empties the queue manager.
        """
        self.base_queue.clear()
        self.queue.clear()
        self.prev_history.clear()
        self.current_track = None
