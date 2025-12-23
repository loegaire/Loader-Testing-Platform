import socket
import logging

class C2Listener:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.logger = logging.getLogger("C2")
        self.success = False

    def listen(self, timeout=30):
        self.success = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.bind((self.ip, self.port))
            s.listen(1)
            self.logger.info(f"Listening on {self.ip}:{self.port}...")
            conn, addr = s.accept()
            self.logger.info(f"Connection Received from {addr}!")
            self.success = True
            conn.close()
        except socket.timeout:
            self.logger.warning("Listener timed out. No callback received.")
        except Exception as e:
            self.logger.error(f"Listener error: {e}")
        finally:
            s.close()