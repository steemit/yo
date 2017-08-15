import argparse
import pprint
import os
import sys

from jsonrpcclient import http_client

class YoClient:
   """ A simple client for testing yo
   """
   def __init__(self,endpoint_url='http://localhost:8080'):
       self.client = http_client.HTTPClient(endpoint_url)
  
   def invoke_method(self,method_name,*args,**kwargs):
       retval = None
       try:
          response = self.client.request(method_name,*args,**kwargs)
          retval   = response
       except Exception as e:
          print('Exception occurred in RMI: %s' % e)
          retval   = None
       return retval 

   def create_user(self,username,email,first_name,last_name,phone):
       user_obj = {'name'      :username,
                   'email'     :email,
                   'first_name':first_name,
                   'last_name' :last_name,
                   'phone'     :phone}
       return self.invoke_method('yo.create_user',user=user_obj)

if __name__=='__main__':
   parser = argparse.ArgumentParser(description="yo notification server")
   parser.add_argument('-s','--server_url', type=str, default='http://localhost:8080')
   parser.add_argument('-m','--method',     type=str, default='yo.test')
   parser.add_argument('-p','--params',     nargs='+', help='Method arguments to pass to the server')
   args = parser.parse_args(sys.argv[1:])

   yo = YoClient(args.server_url)

   try:
      if args.method in dir(yo): # we have a method to locally massage the data
         response = getattr(yo,args.method)(*args.params)
      else:
         response = yo.invoke_method(args.method,args=args.params,kwargs={})
      if response == None:
         print('Method returned no response')
      else:
         pprint.pprint(response)
   except Exception as e:
      print(e)
