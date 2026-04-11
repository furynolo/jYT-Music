import pytest
from utils.queue_manager import QueueManager

@pytest.fixture
def qm():
    return QueueManager()

def test_load_queue(qm):
    tracks = ["Song A", "Song B", "Song C"]
    qm.load_queue(tracks)
    assert qm.base_queue == tracks
    assert qm.queue == tracks
    assert qm.current_track is None

def test_next_track_advances(qm):
    tracks = ["A", "B"]
    qm.load_queue(tracks)
    
    # First track
    next_t = qm.next_track()
    assert next_t == "A"
    assert qm.current_track == "A"
    assert len(qm.queue) == 1
    
    # Second track
    next_t = qm.next_track()
    assert next_t == "B"
    assert len(qm.queue) == 0
    
    # End of queue
    next_t = qm.next_track()
    assert next_t is None

def test_repeat_one(qm):
    qm.load_queue(["A", "B"])
    qm.set_repeat_mode("one")
    
    qm.next_track() # Load A
    assert qm.current_track == "A"
    
    # Normal advance should stay on A
    assert qm.next_track() == "A"
    
    # Manual skip should move to B
    assert qm.next_track(manual_skip=True) == "B"

def test_previous_track(qm):
    qm.load_queue(["A", "B", "C"])
    qm.next_track() # A
    qm.next_track() # B
    
    prev = qm.previous_track()
    assert prev == "A"
    assert qm.current_track == "A"
    # B should be pushed back to the front of the queue
    assert qm.queue[0] == "B"

def test_shuffle_toggle(qm):
    tracks = [str(i) for i in range(100)]
    qm.load_queue(tracks)
    qm.set_shuffle(True)
    
    # It's statistically nearly impossible that it didn't shuffle
    assert qm.queue != tracks
    
    qm.set_shuffle(False)
    # Turning shuffle off should restore base order for the *pending* items
    assert qm.queue == tracks
