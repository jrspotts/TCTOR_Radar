#This module contains custom exceptions 

class StopProcessingException(Exception):
            
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
        return
                
class RadarNotFoundError(Exception):
        
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
        return
                
class NoReferenceClusterFoundException(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
        return
        
class NoModelDataFound(Exception):

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        
        return        