# ABR.py
# import tensorflow as tf
#NN_MODEL = "./submit/results/nn_model_ep_18200.ckpt" # model path settings, if using ML-based method

class Algorithm:
     def __init__(self):
     # fill your self params
        self.prev_rate = 0
        self.BITRATE = [500.0, 850.0, 1200.0, 1850.0] 
        self.RMIN = self.BITRATE[0]
        self.RMAX = self.BITRATE[-1]

        self.CUSHION = 1.3
        self.RESEVOIR = 0.5
    
     # Initail
     def Initial(self, res, cus):
     # Initail your session or something
        self.some_param = 0

     def f_buf(self, x):
         return ((x - self.RESEVOIR) * (self.RMAX - self.RMIN) / self.CUSHION) + self.RMIN


     # Define your algo
     def run(self, time, S_time_interval, S_send_data_size, S_chunk_len, S_rebuf, S_buffer_size, 
     S_play_time_len,S_end_delay, S_decision_flag, S_buffer_flag, S_cdn_flag, S_skip_time, 
     end_of_video, cdn_newest_id, download_id, cdn_has_frame, IntialVars):
        #  print(f"S_send_data_size : {S_send_data_size}")
        #  print(f"S_send_data_size : {S_send_data_size}, S_chunk_len : {S_chunk_len}, cdn_has_frame : {cdn_has_frame}")
         # If you choose the marchine learning
         '''state = []

         state[0] = ...
         state[1] = ...
         state[2] = ...
         state[3] = ...
         state[4] = ...

         decision = actor.predict(state).argmax()
         bit_rate, target_buffer = decison//4, decison % 4 .....
         return bit_rate, target_buffer'''

         # If you choose BBA-0
         RESEVOIR = self.RESEVOIR
         CUSHION =  self.CUSHION
         
         buf_now = S_buffer_size[-1]

         # determine rate+ rate- (kb/s)
         if self.prev_rate == 3:
             rate_plus = self.BITRATE[3]
         else:
             rate_plus = self.BITRATE[self.prev_rate + 1]

         if self.prev_rate == 0:
             rate_minus = self.BITRATE[0]
         else:
             rate_minus = self.BITRATE[self.prev_rate - 1]

         # determine next bit rate
         catched_f_buf = self.f_buf(buf_now)
         if buf_now < RESEVOIR:
             bit_rate = 0    
         elif buf_now >= RESEVOIR + CUSHION:
             bit_rate = 3
         elif catched_f_buf >= rate_plus:
             for i, r in enumerate(self.BITRATE[::-1]):
                 if(r < catched_f_buf):
                     bit_rate = 3-i
                     break
         elif catched_f_buf <= rate_minus:
             for i, r in enumerate(self.BITRATE):
                 if(r > catched_f_buf):
                     bit_rate = i
                     break
         else:
             bit_rate = self.prev_rate

         # determine target buffer by buffer size
         if buf_now < RESEVOIR:
             target_buffer = 0
         else:
             target_buffer = 1

         # testing about latency limit 
         latency_limit = 4

         # for next iteration
         self.prev_rate = bit_rate

         return bit_rate, target_buffer, latency_limit

         # If you choose other
         #......
     
     def get_params(self):
     # get your params
        your_params = []
        return your_params
