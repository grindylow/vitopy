#!/usr/bin/env python3

# optoexceptions.py

class TimeoutWhileReadingPayloadException(BaseException):
    pass

class ChecksumMismatchException(BaseException):
    pass

class CannotInterpretOddNumberOfBytesAsArrayOfIntegersException(BaseException):
    pass

class ReceivedUnexpectedByteValueException(BaseException):
    pass

class CannotInterpretNonDivisibleByFourNumberOfBytesAsArrayOf32BitIntegersException(BaseException):
    pass

if __name__ == "__main__":
    print("Not meant to be executed. May implement demo features here in the future.")
    
