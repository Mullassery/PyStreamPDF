"""Dashboard daemon - runs in background, restarts on close"""

import subprocess
import time
import signal
import sys
from pathlib import Path

class DashboardDaemon:
    def __init__(self, package_name: str, dashboard_cmd: str):
        self.package_name = package_name
        self.dashboard_cmd = dashboard_cmd
        self.process = None
        self.running = True
        
    def start(self):
        """Start dashboard daemon - restarts if closed"""
        signal.signal(signal.SIGINT, self._handle_interrupt)
        
        while self.running:
            try:
                print(f"\n📊 Starting {self.package_name} dashboard daemon...")
                print(f"   (Press Ctrl+C to close, use keyboard shortcuts to restore)\n")
                
                self.process = subprocess.Popen(
                    self.dashboard_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Wait for process to complete
                self.process.wait()
                
                if self.running:
                    print(f"\n⚠️  Dashboard closed. Restarting in 2s... (Ctrl+C to stop)")
                    time.sleep(2)
                    
            except KeyboardInterrupt:
                print("\n✅ Dashboard daemon stopped.")
                self.running = False
            except Exception as e:
                print(f"❌ Error: {e}")
                if self.running:
                    time.sleep(2)
    
    def _handle_interrupt(self, signum, frame):
        self.running = False
        if self.process:
            self.process.terminate()
        sys.exit(0)

def start_persistent_dashboard(package_name: str, cmd: str = None):
    """Start dashboard that persists across terminal sessions"""
    if cmd is None:
        cmd = f"{package_name.lower()} dashboard"
    
    daemon = DashboardDaemon(package_name, cmd)
    daemon.start()
