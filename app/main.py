    
import asyncio
from typing import List
from bleak import BleakScanner , BLEDevice

def sum(a, b):
    return a + b

class StationInfo:
    
    def __init__(self,ip,name,is_master=False):
        self.name = name
        self.ip = ip
        self.is_master = is_master
        self.neighbors = self.scan_devices()
        
    def scan_devices(self) -> List[BLEDevice]:
        return asyncio.run(BleakScanner.discover(timeout=10))
        
    def __str__(self):
        return f"StationInfo(name={self.name},ip={self.ip},is_master={self.is_master},neighbors={[str(n) for n in self.neighbors if n.name is not None]})"
def main():
    
    among = StationInfo("sus","imposter",True)
    print(str(among))
    
    # if detect master flood info to neighbors 
    
    # if have master then send tables
    
    # if im master then compute topology and send to the boys
    
    # if master check all versions and then uppdate the boys

if __name__ == "__main__":
    main()