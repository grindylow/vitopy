#!/usr/bin/env python3

# optoexceptions.py

class TimeoutWhileReadingPayloadException(Exception):
    pass

class ChecksumMismatchException(Exception):
    pass

class CannotInterpretOddNumberOfBytesAsArrayOfIntegersException(Exception):
    pass

class ReceivedUnexpectedByteValueException(Exception):
    pass

class CannotInterpretNonDivisibleByFourNumberOfBytesAsArrayOf32BitIntegersException(Exception):
    pass

if __name__ == "__main__":
    print("Not meant to be executed. May implement demo features here in the future.")
    
