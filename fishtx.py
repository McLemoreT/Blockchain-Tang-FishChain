from enum import Enum
import uuid

class Species(Enum):
    UNDEFINED = 0
    TROUT = 1
    CATFISH = 2
    TUNA = 3

class Consumption(Enum):
    MINTED = 0
    FISHED = 1
    SOLD = 2
    CONSUMED = 3

class FishTxn:
    def __init__(self, guid=str(uuid.uuid4()), speciesId=0, caughtLat=0, caughtLong=0, consumption=0):
        """
        Initializies a fish txn
        """
        self.guid = guid
        self.speciesId = speciesId
        self.caughtLat = caughtLat
        self.caughtLong = caughtLong
        self.consumption = consumption
