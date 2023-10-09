
from EC2Grabber import *
import threading
from pathlib import Path
from gui import *
import time
from concurrent.futures import ThreadPoolExecutor


#=======================================================================

root = tk.Tk()
root.title("EC2 Controller")
root.configure(bg='#282a36')
# Create the app
app = App(root)

# Start the Tkinter event loop
root.mainloop()



