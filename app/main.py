    
from master_node import MasterNode
from station_node import StationNode
from mqtt_config import BROKER_ADDRESS, BROKER_PORT, IM_MASTER

def sum(a, b):
    return a + b


def main():
    myself = StationNode(BROKER_ADDRESS + ":" + str(BROKER_PORT), IM_MASTER)
    myself.start()
    if IM_MASTER:
        master = MasterNode()
        master.start()
    else:
        print("This node is not a master. It will only run as a station node.")

if __name__ == "__main__":
    main()