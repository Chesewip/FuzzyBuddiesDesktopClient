import os
import paramiko
import time
import requests
import threading
import select

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


    #def __del__(self):
     #   self.stopFuzzyBuddies()

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

# -----------------------------------------------------------------------------------------

    def pollForResult(self, interval=2):
        while True:
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
                #if self.getOpenSSHStatus() is False:
                 #   break
                #self.closeSSHConnection();    
                #break  # or re-raise the exception if you want the thread to terminate

    def getVoiceResults(self, zip_files):
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)

        for zip_file in zip_files:
            remote_file_path = os.path.join(self.remoteDir, zip_file)

            # Check the file size
            file_stat = self.sftp.stat(remote_file_path)
#            if file_stat.st_size < 1000000:  # less than 1000 KB
 #               print(f"Deleting small file: {zip_file}")
  #              self.sftp.remove(remote_file_path)
   #             continue  # skip the current iteration

            local_file_path = os.path.join(self.outputDir, zip_file)
            self.sftp.get(remote_file_path, local_file_path)
            self.sftp.remove(remote_file_path)

# -----------------------------------------------------------------------------------------

    def start(self):
        self.should_run_fuzzy_buddies = True
        self.should_poll_ec2 = True
        # Run the command in a new thread to avoid freezing the GUI
        threading.Thread(target=self._start_thread).start()
    

    def stopFuzzyBuddies(self):
        # Kill the gradio web interface
        try:
            _, stdout, stderr = self.ssh.exec_command('pgrep -f "python3 /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2/GPTConvoEC2/Main.py"')
            pid = stdout.read().decode().strip()

            _, stdout, stderr = self.ssh.exec_command(f'kill -USR1 {pid}')
            self.should_run_fuzzy_buddies = False
            return stdout.read().decode(), stderr.read().decode()
        except:
            return "Could not shutdown fuzzy buddies. Maybe its alive."

    def restartFuzzyBuddies(self):
        if self.isFuzzyBuddiesRunning():
            self.stopFuzzyBuddies()
            time.sleep(10)  # Wait for a few seconds to ensure the process is terminated

        self.start()

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
        _, stdout, stderr = self.ssh.exec_command('source /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2/GPTConvoEC2/venv/bin/activate && python3 /home/ubuntu/gptconvo/gptconvo/GPTConvoEC2/GPTConvoEC2/Main.py', get_pty=True)
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

    def openSSHConnection(self, retries = 0):

        if retries < 0:
            print("Couldn't connect to EC2")
            self.ec2ConnectionStatus = False;
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
