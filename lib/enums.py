import enum

class Prediction(enum.Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SKIP = "SKIP"

class Interval(enum.Enum):
    MIN_1 = "1min"
    MIN_5 = "5min"

class Position(enum.Enum):
    LONG = 'long'
    SHORT = 'short'
    OUT = 'out'