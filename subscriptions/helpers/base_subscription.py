from abc import ABC,abstractmethod



class BaseClient(ABC):
    @abstractmethod
    def create_subscription(self,user):
        pass

    @abstractmethod
    def excute_subscription(self,request):
        pass

    @abstractmethod
    def cancel_subscription(self,user):
        pass
   
    
   
 