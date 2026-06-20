


class PLC_IO_Control(object):

   def __init__(self,
                redis_site,
                qs,
                generate_irrigation_control ):
       self.filter_queue = [0,0,0,0,0]
       self.current_filter = {}   # A4: per-channel median-of-3 rings, keyed by status_key
       self.generate_irrigation_control = generate_irrigation_control
       self.redis_site = redis_site
       self.qs         = qs
       self.hash_update = self.generate_irrigation_control(redis_site,qs)
       self.construct_plc_elements(redis_site,qs)
       self.construct_plc_flow_measurements(redis_site,qs) 
       self.construct_plc_slave_current_measurements(redis_site,qs) 
       self.construct_plc_irrigation_measurements(redis_site,qs) 
       self.generate_data_handlers(redis_site,qs)

       self.log_data()        

   def wait_new_minute(self):
        time_stamp = datetime.datetime.today()
        old_minute = time_stamp.minute
        while 1:
              time.sleep(.5)
              time_stamp = datetime.datetime.today()
              minute = time_stamp.minute
              if old_minute != minute:
                 return
             
             
   def log_data(self):
    
       while 1:
           self.wait_new_minute()
           self.minute_measurement = {}
           return_value = {}
           print("\n\n\n\n\n log data \n\n\n\n")
           self.measure_flow_meters(return_value)
           self.measure_irrigation_current(return_value)
           self.measure_slave_current(return_value)
           print("\n\n\n\n\nreturn_value  ############################################",return_value)
           self.ds_handlers["PLC_MEASUREMENTS_STREAM"].push(return_value)
           
               
              

   def measure_flow_meters(self,return_value):
       
       for i in self.plc_flow_meas:
           return_value[i["name"]] = self.make_flow_measurement(return_value,i,"PLC_FLOW_METER")
       

   def measure_irrigation_current(self,return_value):
       for i in self.plc_irrigation_current_meas:
          # single read per channel (was two reads: one for the print, one for the value)
          value = self.make_current_measurement(i,"PLC_IRRIGATION_CURRENT")
          print("irrigation",value)
          return_value[i["name"]] = value

   def measure_slave_current(self,return_value):
       for i in self.plc_slave_current_meas:
           # single read per channel (was two reads: one for the print, one for the value)
           value = self.make_current_measurement(i,"PLC_EQUIPMENT_CURRENT")
           print("equipment",value)
           return_value[i["name"]] = value

           
   def make_current_measurement(self,i,status_key): 
       controller     = i["remote"]
       rpc_queue   =    self.plc_table[controller]["rpc_queue"]
       type   =    self.plc_table[controller]["type"]
       action_class   = self.construct_access_class.find_class( type,rpc_queue )
       
       conversion = i["conversion"]
       register        = i["register"]
       print("register",register)
       print("conversion",conversion)
       current_value =  action_class.measure_analog(  self.plc_table[controller]["modbus_address"], [register, conversion ] )
       #if register == "DF2":
          #print("irrigation raw",current_value)
       current_value = current_value-2.52
       current_value = current_value/.185
          #print("corrected current",current_value)
       # A4: median-of-3 per channel rejects a single garbage frame (Modbus desync)
       # while still passing a sustained (>=2 consecutive) real overcurrent through to KB1.
       ring = self.current_filter.setdefault(status_key, [current_value]*3)
       ring.append(current_value)
       ring.pop(0)
       current_value = sorted(ring)[1]
       if i["main"] == True:
           
           print("update irrigation table current",status_key,current_value)
           self.hash_update.hset(status_key,current_value) 
       return current_value
       
       
   def make_flow_measurement(self,return_value,i,status_key):    
       controller     = i["remote"]
       rpc_queue   =    self.plc_table[controller]["rpc_queue"]
       type   =    self.plc_table[controller]["type"]
       action_class   = self.construct_access_class.find_class( type,rpc_queue )
      
       conversion_rate = i["io_setup"]["conversion_factor"]
       flow_array =  action_class.measure_counter( self.plc_table[controller]["modbus_address"], i["io_setup"] )
       flow_value = flow_array[0]*conversion_rate
       print("i",i)
       if i["main"] == True:
           print("update irrigation table  flow",status_key,flow_value)
           self.hash_update.hset(status_key,flow_value) 
           print("flow_array",flow_array)
           hunter_valve = flow_array[1]
           print("flow_array 1",flow_array[1],flow_array[2])
           if flow_array[2] < flow_array[1]:
                 print("made it here")
                 hunter_valve = flow_array[2]
           #hunter_valve = ( flow_array[1]+flow_array[2])/2.
           print("hunter valve ",hunter_valve)
           self.hash_update.hset("HUNTER_VALVE",hunter_valve)
           return_value["HUNTER_VALVE"] = hunter_valve
           return_value["HUNTER_HIRES_VALVE"] = (flow_array[1]+flow_array[2])/2
           
           self.filter_queue.append(hunter_valve)
           self.filter_queue.pop(0)
           filtered_hunter_valve = (self.filter_queue[0]+self.filter_queue[1]+self.filter_queue[2]+self.filter_queue[3]+self.filter_queue[4])/5.0
           self.hash_update.hset("FILTERED_HUNTER_VALVE",filtered_hunter_valve )
           self.hash_update.hset("HUNTER_HIRES_VALVE",return_value["HUNTER_HIRES_VALVE"] )
           return_value["FILTERED_HUNTER_VALVE"] = filtered_hunter_valve
           
       return flow_value
       
       
       

   def construct_plc_flow_measurements(self,redis_site,qs): 
       self.plc_flow_meas = []
       query_list = []   
       query_list = qs.add_match_relationship( query_list,relationship="SITE",label=redis_site["site"] )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_MEASUREMENTS" )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_FLOW_METERS")
       query_list = qs.add_match_terminal( query_list, 
                                           relationship = "FLOW_METER")
                                                 
       sensor_sets, sensor_nodes = qs.match_list(query_list)

       for i in sensor_nodes:
          self.plc_flow_meas.append(i)
          
       
   def construct_plc_slave_current_measurements(self,redis_site,qs):
       self.plc_slave_current_meas = []
       query_list = []   
       query_list = qs.add_match_relationship( query_list,relationship="SITE",label=redis_site["site"] )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_MEASUREMENTS" )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_SLAVE_CURRENTS" )
       query_list = qs.add_match_terminal( query_list, 
                                           relationship = "CURRENT_DEVICE")
                                                 
       sensor_sets, sensor_nodes = qs.match_list(query_list)
       
       for i in sensor_nodes:
          self.plc_slave_current_meas.append(i)
          
       
   def construct_plc_irrigation_measurements(self,redis_site,qs):
       self.plc_irrigation_current_meas = []
       query_list = []   
       query_list = qs.add_match_relationship( query_list,relationship="SITE",label=redis_site["site"] )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_MEASUREMENTS" )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_IRRIGATION_CURRENTS" )
       query_list = qs.add_match_terminal( query_list, 
                                           relationship = "CURRENT_DEVICE")
                                                 
       sensor_sets, sensor_nodes = qs.match_list(query_list)
       
       for i in sensor_nodes:
          self.plc_irrigation_current_meas.append(i)
   
                
                
   def generate_data_handlers(self,redis_site,qs):
       query_list = []   
       query_list = qs.add_match_relationship( query_list,relationship="SITE",label=redis_site["site"] )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_MEASUREMENTS" )
       query_list = qs.add_match_terminal( query_list, 
                                           relationship = "PACKAGE", 
                                           property_mask={"name":"PLC_MEASUREMENTS_PACKAGE"} )
                                           
       package_sets, package_sources = qs.match_list(query_list)
       
       package = package_sources[0]       
   
        
       data_structures = package["data_structures"]
       generate_handlers = Generate_Handlers(package,qs)
       self.ds_handlers = {}
       self.ds_handlers["PLC_MEASUREMENTS_STREAM"] = generate_handlers.construct_redis_stream_writer(data_structures["PLC_MEASUREMENTS_STREAM"])                
       self.construct_access_class =   Construct_Access_Classes(generate_handlers)


   def construct_plc_elements(self,redis_site,qs):
       self.plc_table = {}  # indexed by logical name
       query_list = []
       query_list = qs.add_match_relationship( query_list,relationship="SITE",label=redis_site["site"] )
       query_list = qs.add_match_terminal( query_list,relationship="PLC_SERVER" )
       plc_server_field, plc_server_nodes = qs.match_list(query_list)
       for i in plc_server_nodes:
           rpc_queue = self.generate_rpc_client_queue(qs,redis_site,i["name"])
           query_list = []
           query_list = qs.add_match_relationship( query_list,relationship="SITE",label=redis_site["site"] )
           query_list = qs.add_match_relationship( query_list,relationship="PLC_SERVER",label=i["name"] )
           query_list = qs.add_match_terminal( query_list,relationship="REMOTE_UNIT" )
           plc_field, plc_nodes = qs.match_list(query_list)
           for j in plc_nodes:
               j["rpc_queue"]         = rpc_queue
               self.plc_table[j["name"]] = j
       
               
    
       
   def generate_rpc_client_queue(self,qs,redis_site,name): 
       query_list = []   
       query_list = qs.add_match_relationship( query_list,relationship="SITE",label=redis_site["site"] )
       query_list = qs.add_match_relationship( query_list,relationship="PLC_SERVER",label=name )
       query_list = qs.add_match_terminal( query_list, 
                                           relationship = "PACKAGE", 
                                           property_mask={"name":"PLC_SERVER_DATA"} )
                                           
       package_sets, package_sources = qs.match_list(query_list)
       
       package = package_sources[0]    
       data_structures = package["data_structures"]
       
       queue = data_structures["PLC_RPC_SERVER"]["queue"]
       return queue
       



           

        




                   
if __name__ == "__main__":


    import datetime
    import os
    import copy
    import msgpack
    import base64
    import redis
    import time
    import datetime
    import json
    from redis_support_py3.graph_query_support_py3 import  Query_Support
    from redis_support_py3.construct_data_handlers_py3 import Generate_Handlers
    from   plc_control_py3.construct_classes_py3 import Construct_Access_Classes
    from core_libraries.irrigation_hash_control_py3 import generate_irrigation_control    

    from py_cf_new_py3.chain_flow_py3 import CF_Base_Interpreter

    #
    #
    # Read Boot File
    # expand json file
    # 
    file_handle = open("system_data_files/redis_server.json",'r')
    data = file_handle.read()
    file_handle.close()
    redis_site = json.loads(data)
     
    qs = Query_Support( redis_site )
    PLC_IO_Control(redis_site,qs,generate_irrigation_control)
