# ABR.py
# import tensorflow as tf
#NN_MODEL = "./submit/results/nn_model_ep_18200.ckpt" # model path settings, if using ML-based method

class Algorithm:
     def __init__(self):
     # fill your self params
        # same value
        self.BITRATE = [500.0, 850.0, 1200.0, 1850.0]
        self.RMIN = self.BITRATE[0]
        self.RMAX = self.BITRATE[-1]
        self.frame_time_len = 0.04
        self.SKIP_PENALTY = 0.5

        # variable value
        self.prev_rate = 0

        # value need to tune
        self.LAMBDA = 1.0
        self.CUSHION = 0.7
        self.RESEVOIR = 0.9
    
     # Initail
     def Initial(self, res, cus, lam):
     # Initail your session or something
        self.RESEVOIR = res
        self.CUSHION = cus
        self.LAMBDA = lam

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

        #  print(S_chunk_len[-1], S_time_interval[-1], time, S_send_data_size[-1])
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
         # if in [B^0_min, B^0_max), target_buffer = 1
         # otherwise, target_buffer = 0
         if 0.3 <= buf_now and buf_now < 1.0:
             target_buffer = 1
         else:
             target_buffer = 0

         # QoE based latency limit
         # LAMBDA may need tuning (?) 
         LATENCY_PENALTY = 0.005
         if S_end_delay[-1] <=1.0:
            LATENCY_PENALTY = 0.005
         else:
            LATENCY_PENALTY = 0.01

         latency_limit = self.frame_time_len * (self.BITRATE[bit_rate]/1000.0 + self.SKIP_PENALTY) / (LATENCY_PENALTY * self.LAMBDA)
        #  latency_limit = 3.2
        #  print(S_skip_time[-1],S_end_delay[-1], latency_limit)

         # for next iteration
         self.prev_rate = bit_rate

         return bit_rate, target_buffer, latency_limit

         # If you choose other
         #......
     
     def get_params(self):
     # get your params
        your_params = []
        return your_params
