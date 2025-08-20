import os

path = "/tmp/mypipe"

# Creates the named pipe if it doesn’t already exist
os.mkfifo(path) if not os.path.exists(path) else None

# os.fork creates a new process (child) by
# duplicating the current process (parent)
if os.fork() == 0:  # Child process (Reader)
    with open(path, 'r') as fifo:
        print(f"Reader received: {fifo.read()}")
        
else:  # Parent process (Writer)
    with open(path, 'w') as fifo:
        fifo.write("Hello from parent!")
    os.remove(path)
