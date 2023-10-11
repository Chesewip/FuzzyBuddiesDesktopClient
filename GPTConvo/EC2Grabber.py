import os
import paramiko
import time
import requests
import threading
import select

class StatusPacket:
    def __init__(self, ec2Status, connectionStatus, fuzzyBuddiesStatus, voiceCloner1Status,voiceCloner2Status):
        self.ec2Status = ec2Status
        self.connectionStatus = connectionStatus
        self.fuzzyBuddiesStatus = fuzzyBuddiesStatus
        self.voiceCloner1Status = voiceCloner1Status
        self.voiceCloner2Status = voiceCloner2Status


class EC2Grabber:

    def __init__(self, keyFile, remoteDir, outputDir, output_callback= None):
        self.output_callback = output_callback
        self.remoteDir = remoteDir
        self.outputDir = outputDir
        self.ec2Adress = self.get_ec2_public_dns("https://4w5a7ay9j4.execute-api.us-west-1.amazonaws.com/prod/ec2address")
        self.keyFile = keyFile
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.openSSHConnection(0)
        self.should_run_fuzzy_buddies = False
        self.should_poll_ec2 = False
        self.current_ports = [8000,8001]
        self.waiting_for_restart = False;
        self.auto_running = False;
        self.refresh_time = 15;

        # Getting the status of all the system/processes
        self.update_status_packet();

    def __del__(self):
        self.stopFuzzyBuddies()

# -----------------------------------------------------------------------------------------

    def start_auto_run(self):
        self.auto_running = True;
        self.stopFuzzyBuddies();
        self.status_thread = threading.Thread(target=self.auto_refresh_status, daemon=True)
        self.status_thread.start()
        

    def stop_auto_run(self):
        self.auto_running = False;

# -----------------------------------------------------------------------------------------

    def get_ec2_public_dns(self, api_endpoint):
        response = requests.get(api_endpoint)
        response.raise_for_status()  # Raise an exception if the request failed
        data = response.json()  # Parse the JSON response
        return data['message']  # Extract the 'message' field

    def get_ec2_running_status(self):
        response = requests.get("https://4w5a7ay9j4.execute-api.us-west-1.amazonaws.com/prod/ec2status")
        data = response.json() 
        try:
            status = data['status']
            return status
        except:
            return "Server error or no connection"

    def startEC2(self):
        url = "https://4w5a7ay9j4.execute-api.us-west-1.amazonaws.com/prod/ec2Start"
        payload = {
            "action": "start"
        }
        response = requests.post(url, json = payload)
        data = response.json()  # Parse the JSON response
        message = data['message']

        if (message == "Success"):
            self.ec2Adress = self.get_ec2_public_dns("https://4w5a7ay9j4.execute-api.us-west-1.amazonaws.com/prod/ec2address")
            return "Successfully Started EC2"

        return message

    def stopEC2(self):
        self.stopFuzzyBuddies();
        self.closeSSHConnection();
        url = "https://4w5a7ay9j4.execute-api.us-west-1.amazonaws.com/prod/ec2Start"
        payload = {
            "action": "stop"
        }
        response = requests.post(url, json = payload)
        data = response.json()  # Parse the JSON response
        message = data['message']
        if message == "Success":
            return "Successfully Stopped EC2"
        return message;

    def restart_ec2(self):
        self.stopEC2();
        

    #def _poll_for_stopped_status():



# -----------------------------------------------------------------------------------------

    def start_polling(self):
        poll_thread = threading.Thread(target=self.pollForResult, kwargs={'interval' : 1}, daemon=True)
        self.should_poll_ec2 = True;
        poll_thread.start()

    def stop_polling(self):
        self.should_poll_ec2 = False;

    def pollForResult(self, interval=2):
        while self.should_poll_ec2:
            try:
                file_list = self.sftp.listdir(self.remoteDir)
                zip_files = [file for file in file_list if file.endswith('.zip')]

                if zip_files:
                    print('Zip files are ready, fetching...')
                    self.getVoiceResults(zip_files)
                else:
                    print('.')
                    time.sleep(interval)
            except Exception as e:
                print(f"Error occurred: {e}")
                time.sleep(interval * 2)

    def getVoiceResults(self, zip_files):
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)

        for zip_file in zip_files:
            remote_file_path = os.path.join(self.remoteDir, zip_file)

            # Check the file size
            file_stat = self.sftp.stat(remote_file_path)
            if file_stat.st_size < 1000000:  # less than 1000 KB
                print(f"Deleting small file: {zip_file}")
                self.sftp.remove(remote_file_path)
                continue  # skip the current iteration

            local_file_path = os.path.join(self.outputDir, zip_file)
            self.sftp.get(remote_file_path, local_file_path)
            self.sftp.remove(remote_file_path)

# -----------------------------------------------------------------------------------------

    def startFuzzyBuddies(self):
        try:
            gitcommand = 'cd /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2 && git pull origin master'
            _, stdout, stderr = self.ssh.exec_command(gitcommand, get_pty=True)

            self.should_run_fuzzy_buddies = True
            self.should_poll_ec2 = True
            # Run the command in a new thread to avoid freezing the GUI
            threading.Thread(target=self._start_thread).start()
        except:
            "Could not start fuzzy buddies"
    

    def stopFuzzyBuddies(self):
        # Kill the gradio web interface
        try:
            _, stdout, stderr = self.ssh.exec_command('pgrep -f "python3 /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2/GPTConvoEC2/Main.py"', get_pty = True)
            pid = stdout.read().decode().strip()

            _, stdout, stderr = self.ssh.exec_command(f'kill -USR1 {pid}')
            self.should_run_fuzzy_buddies = False
            print(stdout.read().decode())
            self.output_callback(stdout.read().decode())
            self.increase_current_ports();

            return stdout.read().decode(), stderr.read().decode()
        except:
            return "Could not shutdown fuzzy buddies. Maybe its alive."

    def restartFuzzyBuddies(self):
        if self.isFuzzyBuddiesRunning():
            output, errorText = self.stopFuzzyBuddies()
            self.output_callback(output)
        else:
            self.increase_current_ports();
            
        time.sleep(5)  # Wait for a few seconds to ensure the process is terminated
        self.startFuzzyBuddies()

    def isFuzzyBuddiesRunning(self):
        try:
            # Find the PID of the running script
            _, stdout, stderr = self.ssh.exec_command('pgrep -f "python3 /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2/GPTConvoEC2/Main.py"')
            pid = stdout.read().decode().strip()

            # If a PID is returned, then the script is running
            if pid:
                return True
            else:
                return False
        except:
            # If there's an exception (e.g. SSH connection issue), assume the script isn't running
            return False


    def _start_thread(self):
        port1 = self.current_ports[0]
        port2 = self.current_ports[1]
        _, stdout, stderr = self.ssh.exec_command(f'source /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2/GPTConvoEC2/venv/bin/activate && python3 /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2/GPTConvoEC2/Main.py {port1} {port2}', get_pty=True)
        while self.should_run_fuzzy_buddies:
            try:
                for line in iter(stdout.readline, ""):
                    print(line, end="")

                    if self.output_callback:
                        self.output_callback(line)
                        if (line.startswith("torch.cuda.OutOfMemoryError")):
                            self.restartFuzzyBuddies()
                time.sleep(1)
            except Exception as ex:
                print(ex)

# -----------------------------------------------------------------------------------------

    def getVoiceClonerStatus(self, port):

        try:
            url = f"http://127.0.0.1:{port}"
            cmd = f'''
echo '
import requests

def is_gradio_alive(url):
    try:
        response = requests.get(url)
        return response.status_code == 200
    except:
        return False

print(is_gradio_alive("{url}"))
' | python3
'''
            _, stdout, stderr = self.ssh.exec_command(cmd, get_pty=True)
            response = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()
        
            if error:
                # Handle or log the error appropriately.
                print(f"Error executing remote script: {error}")
                return None
        
            return response == "True"
        except:
            return False


# -----------------------------------------------------------------------------------------

    def openSSHConnection(self, retries = 0, restart_ec2_on_failure = False):

        if retries < 0:
            print("Couldn't connect to EC2")
            self.ec2ConnectionStatus = False;

            #If the EC2 is running, and after several retries we still couldn't connect, restart the ec2
            if self.status_packet.ec2Status == "running" and self.auto_running:
                self.stopEC2();

            return "Couldn't connect to EC2"

        try:
            self.ec2Adress = self.get_ec2_public_dns("https://4w5a7ay9j4.execute-api.us-west-1.amazonaws.com/prod/ec2address")
            self.ssh.connect(self.ec2Adress, username='ubuntu', key_filename= self.keyFile)
            self.sftp = self.ssh.open_sftp()
            print("Successfully Connected To EC2")
            self.ec2ConnectionStatus = True;
            return "Successfully Connected To EC2"
        except Exception as ex:
            print(ex)
            time.sleep(3);
            self.openSSHConnection(retries-1)

    def closeSSHConnection(self):
        try:
            self.ssh.close();
            self.ec2ConnectionStatus = False;
            return "Successfully Closed EC2 Connection."
        except:
            return "Could not properly close EC2 Connection."

    def getOpenSSHStatus(self):
        if self.ssh.get_transport() and self.ssh.get_transport().is_active():
            self.ec2ConnectionStatus = True
        else:
            self.ec2ConnectionStatus = False
        return self.ec2ConnectionStatus

    # ------------------------------------------------------------------------------

    def update_status_packet(self):
        self.status_packet = StatusPacket( 
            ec2Status = self.get_ec2_running_status(),
            connectionStatus = self.getOpenSSHStatus(),
            fuzzyBuddiesStatus = self.isFuzzyBuddiesRunning(),
            voiceCloner1Status = self.getVoiceClonerStatus(self.current_ports[0]),
            voiceCloner2Status = self.getVoiceClonerStatus(self.current_ports[1]),
        )

    def auto_refresh_status(self):
        while self.auto_running:
            self.update_status_packet();
            self._handle_status_update(self.status_packet)
            time.sleep(10)

    def _handle_status_update(self, status_packet):
        if status_packet.ec2Status == "stopped" :
            self.startEC2();
            return;
        
        if status_packet.ec2Status != "running" : # Make sure EC2 is running before doing anything else
            return

        if status_packet.connectionStatus == False:
            self.closeSSHConnection();
            self.openSSHConnection(5, True);

        else: # We are connected

            if status_packet.fuzzyBuddiesStatus == False:
                self.restartFuzzyBuddies();


    def increase_current_ports(self):
        for i in range(len(self.current_ports)):
            self.current_ports[i] += 2
            if self.current_ports[i] > 8009:
                self.current_ports[i] -= 9
