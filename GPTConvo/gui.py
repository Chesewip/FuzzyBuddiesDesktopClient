from cmath import e
import tkinter as tk
from tkinter import scrolledtext
from EC2Grabber import *
from pathlib import Path
from tkinter import ttk
import threading
import queue


pem_path = Path('Documents/GPT/wizPassword.pem')
local_dir = Path('Documents/AI INPUTS/Scripts')



class App:
    def __init__(self, root):
        self.ec2 = EC2Grabber(
                            str(Path.home() / pem_path),  # where the password file is
                            '/home/ubuntu/gptconvo/ScriptsDropoff/',
                            str(Path.home() / local_dir),  #where to put script files when we grab them from EC2
                            output_callback= self.update_output
                            )
        self.root = root
        self.root.geometry('960x640')  # Set the window size

        self.root.after(1000, self.check_queue)
        self.queue = queue.Queue()

        # Create a Frame that will contain the buttons
        self.autoRunFrame = tk.Frame(root, bg = "#ff0000",)
        self.ec2frame = tk.Frame(root, bg = "#ff0000",)
        self.frame = tk.Frame(root, bg = "#ff0000",)

        # Create frames for each button
        self.frame8 = tk.Frame(self.autoRunFrame, height=60, bg = "#282a36")
        self.frame8.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.frame9 = tk.Frame(self.autoRunFrame, height=60, bg = "#282a36")
        self.frame9.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.frame1 = tk.Frame(self.frame, height=60, bg = "#282a36")
        self.frame1.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.frame2 = tk.Frame(self.frame, height=60, bg = "#282a36")
        self.frame2.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.frame7 = tk.Frame(self.frame, height=60, bg = "#282a36")
        self.frame7.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.frame3 = tk.Frame(self.ec2frame, height=60, bg = "#282a36")
        self.frame3.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.frame4 = tk.Frame(self.ec2frame, height=60, bg = "#282a36")
        self.frame4.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.frame5 = tk.Frame(self.ec2frame, height=60, bg = "#282a36")
        self.frame5.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.frame6 = tk.Frame(self.ec2frame, height=60, bg = "#282a36")
        self.frame6.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Add some padding around each button and make them fill their grid cell
        self.start_auto_run_button = tk.Button(self.frame8, text="Start Auto Run", command=self.start_auto_run, bg='#383a46', fg='white')
        self.stop_auto_run_button = tk.Button(self.frame9, text="Stop Auto Run", command=self.stop_auto_run, bg='#383a46', fg='white', state = 'disabled')

        self.start_button = tk.Button(self.frame1, text="Start Fuzzy Buddies", command=self.start, bg='#383a46', fg='white')
        self.restart_button = tk.Button(self.frame7, text="Restart Fuzzy Buddies", command=self.restart_fuzzy_buddies, bg='#383a46', fg='white')
        self.stop_button = tk.Button(self.frame2, text="Stop Fuzzy Buddies", command=self.stop_fuzzy_buddies, bg='#383a46', fg='white',state = 'disabled')
        
        self.start_ec2_button = tk.Button(self.frame3, text="Start EC2", command=self.start_ec2, bg='#383a46', fg='white')
        self.stop_ec2_button = tk.Button(self.frame4, text="Stop EC2", command=self.stop_ec2, bg='#383a46', fg='white')
        self.connect_ec2_button = tk.Button(self.frame5, text="Connect to EC2", command=self.try_connect_to_ec2, bg='#383a46', fg='white')
        self.disconnect_ec2_button = tk.Button(self.frame6, text="Disconnect from EC2", command=self.disconnect_from_ec2, bg='#383a46', fg='white')

        # The buttons will automatically fill the Frame because we set fill=tk.BOTH in the pack method call for the Frame
        self.start_auto_run_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.stop_auto_run_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.start_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.restart_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.stop_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.start_ec2_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.stop_ec2_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.connect_ec2_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.disconnect_ec2_button.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Prevent the frames from shrinking
        self.frame1.pack_propagate(False)
        self.frame7.pack_propagate(False)
        self.frame2.pack_propagate(False)
        self.frame3.pack_propagate(False)
        self.frame4.pack_propagate(False)
        self.frame5.pack_propagate(False)
        self.frame6.pack_propagate(False)
        self.frame8.pack_propagate(False)
        self.frame9.pack_propagate(False)


        def create_status_indicator(self, parent, text):
            # Add a canvas for the circle 'light'
            light = tk.Canvas(parent, bg="#282a36", width=self.light_diameter, height=self.light_diameter, highlightthickness=0, bd=0)
            light.pack(side=tk.LEFT, padx=5)
            light.create_oval(2, 2, self.light_diameter-2, self.light_diameter-2, fill="gray", tag="light")
    
            # Add a label for the status
            label = tk.Label(parent, text=text, bg="#282a36", fg="white")
            label.pack(side=tk.LEFT, padx=5)

            return light, label


        self.light_diameter = 15

        self.status_bar_frame = tk.Frame(root, bg="#282a36", height=25)
        self.status_light, self.status_label = create_status_indicator(self, self.status_bar_frame, "EC2 Status: Unknown")
        self.refresh_button = tk.Button(self.status_bar_frame, text="Refresh", command=self.force_refresh,bg='#383a46', fg='white') 
        self.refresh_button.pack(side=tk.RIGHT)
        self.status_bar_frame.pack_propagate(False)

        self.connection_status_frame = tk.Frame(root, bg="#282a36", height=25)
        self.connection_light, self.connection_label = create_status_indicator(self, self.connection_status_frame, "EC2 Connection: ")
        self.connection_status_frame.pack_propagate(False)

        self.vc_status_frame = tk.Frame(root, bg="#282a36", height=25)
        self.vc_light, self.vc_label = create_status_indicator(self, self.vc_status_frame, "Voice cloner status : ")
        self.vc_status_frame.pack_propagate(False)

        self.fb_status_frame = tk.Frame(root, bg="#282a36", height=25)
        self.fb_light, self.fb_label = create_status_indicator(self, self.fb_status_frame, "Fuzzy Buddies Status")
        self.fb_status_frame.pack_propagate(False)


        self.fb_status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.vc_status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.connection_status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.status_bar_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.ec2frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10)
        self.frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10)
        self.autoRunFrame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

        # Create a ScrolledText widget for output
        self.output = scrolledtext.ScrolledText(root, bg='#282a36', fg='white')
        self.output.pack(fill=tk.BOTH, expand=True)


        root.protocol('WM_DELETE_WINDOW', self.on_close)

        self.buttons = [
            self.start_button,
            self.restart_button,
            self.stop_button,
            self.start_ec2_button,
            self.stop_ec2_button,
            self.connect_ec2_button,
            self.disconnect_ec2_button,
            self.refresh_button  # And any other buttons you might have.
        ]

        self.refresh_thread_running = True
        self.refresh_thread = threading.Thread(target=self.auto_refresh_status, daemon=True)
        self.refresh_thread.start()

        self.ec2.start_polling();
        self.refresh_status();

    # ----------------------------------------------------------------------------------------------
    def start_auto_run(self):
        self.start_auto_run_button.config(state = 'disabled')
        self.stop_auto_run_button.config(state = 'normal')
        self.disable_all_buttons();
        self.ec2.start_auto_run()

    def stop_auto_run(self):
        self.start_auto_run_button.config(state = 'normal')
        self.stop_auto_run_button.config(state = 'disabled')
        self.ec2.stop_auto_run()
        self.enable_all_buttons();
        self.force_refresh();

    def disable_all_buttons(self):
        for button in self.buttons:
            button.config(state='disabled')

    def enable_all_buttons(self):
        for button in self.buttons:
            button.config(state='normal')


    # ----------------------------------------------------------------------------------------------

    def start(self):
        print("Starting")
        self.ec2.startFuzzyBuddies()

        self.start_button.config(state='disabled')  # Disable the start button

    def stop_fuzzy_buddies(self):
        print("Stopping")
        self.ec2.stopFuzzyBuddies()
        self.start_button.config(state='normal')  # Enable the start button

    def restart_fuzzy_buddies(self):
        print("Restarting")
        self.ec2.restartFuzzyBuddies()
        self.start_button.config(state='normal')  # Enable the start button

    def start_ec2(self):
        print("Attempting to start")
        startResult = self.ec2.startEC2()
        self.update_output(startResult, True);
        self.update_output("Attempting To Connect to EC2", True);
        self.try_connect_to_ec2();
        self.refresh_status();

    def stop_ec2(self):
        print("Attempting to shutdown")
        self.update_output(self.ec2.closeSSHConnection(), True);
        stopResult = self.ec2.stopEC2()
        self.update_output(stopResult, True);
        self.try_connect_to_ec2();
        self.refresh_status()
        

    def on_close(self):
        self.refresh_thread_running = False
        # Perform hard reset before closing the window
        self.ec2.stopFuzzyBuddies()
        self.root.destroy()

    def update_output(self, line, includeNewLine = False):
        try:
            # Append the new output line to the ScrolledText widget
            if includeNewLine:
                self.output.insert(tk.END, line + "\n")
            else:
                self.output.insert(tk.END, line)
            self.output.see(tk.END)  # Scroll the widget to show the new line
        except:
            pass

# -----------------------------------------------------------------------------------

    def try_connect_to_ec2(self):
        self.update_output(self.ec2.openSSHConnection(0), True);
        self.refresh_status();

    def disconnect_from_ec2(self):
        self.update_output(self.ec2.closeSSHConnection(), True);
        self.refresh_status();

# -----------------------------------------------------------------------------------

    def refresh_status(self):
        self.update_ec2_status(self.ec2.status_packet);
        self.update_ec2_connection_status(self.ec2.status_packet);
        self.update_voice_cloner_status(self.ec2.status_packet);
        self.update_fuzzy_buddies_status(self.ec2.status_packet);

        if self.ec2.auto_running:
            self.disable_all_buttons();

    def update_ec2_status(self, status_packet):
        status = status_packet.ec2Status;
        self.status_label.config(text="EC2 Status: " + status)
        if status == "running":
            self.status_light.itemconfig("light", fill="green")
            self.stop_ec2_button.config(state='normal')
            self.start_ec2_button.config(state='disabled')
        elif status == "stopping":
            self.status_light.itemconfig("light", fill="yellow")
            self.stop_ec2_button.config(state='disabled')
            self.start_ec2_button.config(state='disabled')
        elif status == "stopped":
            self.status_light.itemconfig("light", fill="gray")
            self.stop_ec2_button.config(state='disabled')
            self.start_ec2_button.config(state='normal')
        else:
            self.status_light.itemconfig("light", fill="red")
            self.stop_ec2_button.config(state='normal')
            self.start_ec2_button.config(state='disabled')

    def update_ec2_connection_status(self, status_packet):
        connectionStatus = status_packet.connectionStatus;
        if connectionStatus == True:
            self.connection_label.config(text = "EC2 Connection: Connected")
            self.connection_light.itemconfig("light", fill= "green")
            self.connect_ec2_button.config(state = "disabled")
            self.disconnect_ec2_button.config(state = "normal")
        if connectionStatus == False:
            self.connection_label.config(text = "EC2 Connection:  NOT Connected")
            self.connection_light.itemconfig("light", fill= "red")
            self.connect_ec2_button.config(state = "normal")
            self.disconnect_ec2_button.config(state = "disabled")

        ec2Status = status_packet.ec2Status
        if ec2Status != "running":
            self.connect_ec2_button.config(state = "disabled")
            self.disconnect_ec2_button.config(state = "disabled")

    def update_voice_cloner_status(self, status_packet):
        vc1Status = status_packet.voiceCloner1Status;
        vc2Status = status_packet.voiceCloner2Status;
        vc1String = "VC1 : ALIVE" if vc1Status else "VC1 : DEAD"
        vc2String = "VC2 : ALIVE" if vc2Status else "VC2 : DEAD"
        self.vc_label.config(text=f"Voice cloner status : {vc1String} , {vc2String}")
        if not vc1Status and not vc2Status:
            self.vc_light.itemconfig("light", fill="red")
        elif not vc1Status or not vc2Status:
            self.vc_light.itemconfig("light", fill="yellow")
        else:
            self.vc_light.itemconfig("light", fill="green")

    def update_fuzzy_buddies_status(self, status_packet):
        connectionStatus = status_packet.connectionStatus
        if not connectionStatus:
            self.fb_light.itemconfig("light", fill = "gray")
            self.fb_label.config(text = "Fuzzy Buddies Status : No connection, not sure.")
            return;
        
        fuzzyBuddiesStatus = status_packet.fuzzyBuddiesStatus
        if fuzzyBuddiesStatus:
            self.fb_light.itemconfig("light", fill = "green")
            self.fb_label.config(text = "Fuzzy Buddies Stats : Running")
            self.stop_button.config(state = 'normal')
            self.start_button.config(state = 'disabled')
        else:
            self.fb_light.itemconfig("light", fill = "red")
            self.fb_label.config(text = "Fuzzy Buddies Stats : Not Running")
            self.stop_button.config(state = 'disabled')
            self.start_button.config(state = 'normal')


    def check_queue(self):
        while not self.queue.empty():

            if not self.ec2.auto_running:
                self.ec2.update_status_packet();

            self.refresh_status()
            self.queue.get()
        self.root.after(1000, self.check_queue)  # Reschedule the check every second


    def auto_refresh_status(self):
        while self.refresh_thread_running:
            self.queue.put(True)  # Indicate that a refresh is required
            time.sleep(15)

    def force_refresh(self):
        self.queue.put(True)  # Indicate that a refresh is required