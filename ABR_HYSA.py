import sys
# import tensorflow as tf
#NN_MODEL = "./submit/results/nn_model_ep_18200.ckpt" # model path settings, if using ML-based method

class Algorithm:
     def __init__(self):
     # fill your self params
        # same value
        self.BITRATE = [500.0, 850.0, 1200.0, 1850.0]
        self.frame_time_len = 0.04
        self.SKIP_PENALTY = 0.5
        self.BITRATE_LEVEL = 4
        self.segment_length = 50

        # variable value
        self.prev_rate = 0
        self.prev_cdn_newest_id = 0
        self.prev_R_hat = [0] * self.BITRATE_LEVEL  # (self.BITRATE_LEVEL, )

        # value need to tune
        self.LAMBDA = 2.8
        self.RESEVOIR = 0.9
        self.CUSHION = 0.7
        self.l_min = 2.0
        self.l_max = 30.0
        self.N_WMA = 5
        self.N_1 = 5
        self.beta = 1
        self.buffer_threshold = 1.4

        # calculated value
        self.R_history = [[0] * self.N_1 for _ in range(self.BITRATE_LEVEL)] # (self.BITRATE_LEVEL, self.N_1)
        self.C_denominator = self.N_WMA * (self.N_WMA + 1) / 2
        self.SC_slowest = 2/(self.l_max + 1)
        self.SC_fastest = 2/(self.l_min + 1) 
    
     # Initail
     def Initial(self, lmin, lmax, Bth):
     # Initail your session or something
        self.l_min = lmin
        self.l_max = lmax
        self.buffer_threshold = Bth

     # Define your algo
     def run(self, time, S_time_interval, S_send_data_size, S_chunk_len, S_rebuf, S_buffer_size, 
     S_play_time_len,S_end_delay, S_decision_flag, S_buffer_flag, S_cdn_flag, S_skip_time, 
     end_of_video, cdn_newest_id, download_id, cdn_has_frame, IntialVars):
        #  print(f"S_send_data_size : {S_send_data_size}")
        #  print(f"S_send_data_size : {S_send_data_size}, S_chunk_len : {S_chunk_len}, cdn_has_frame : {cdn_has_frame}")
         # If you choose the marchine learning
         '''
         V_nm is coding bitrate
         R_nm is actual bitrate
         R^hat is predicted actual bitrate, use n to predict n+1
         SC   is smoothing factor 
         ER   is efficient ratio
         N_1  is # of samples used to calculate ER
         D    is estimated latency(need to minimize)
         d    is segment length (50*frame_time_len ?)
         T    is downloading time of next segment
         C    is throughput estimate by weighted moving average
         N_WMA   # of sample used to estimated C
         B    is estimated buffer occupancy
         v       estimated frame accumulation speed in CDN

         '''
         buf_now = S_buffer_size[-1]
         bit_rate = 0

         # bitrate control

         # estimate c (throughput) using weighted moving average (bps)
         C_numerator = 0
         for i in range(self.N_WMA):
             if S_time_interval[-i-1] != 0:
                C_numerator += (self.N_WMA - i) * (S_send_data_size[-i-1] / S_time_interval[-i-1])
         estimated_C = C_numerator / self.C_denominator

         ## estimate R_hat for every bitrate using KAMA
         ## R : bps
         min_estimate_latency = sys.maxsize
         prev_R = S_send_data_size[-1] / self.frame_time_len
         for b in range(self.BITRATE_LEVEL):
            self.R_history[b].append(prev_R * (self.BITRATE[b] / self.BITRATE[self.prev_rate]))
            
            # calculate ER =  change / volatility
            change = abs(self.R_history[b][-1] - self.R_history[b][0])
            volatility = 0
            for i in range(self.N_1):
                volatility += abs(self.R_history[b][i] - self.R_history[b][i+1])
            ER = change / volatility
            
            self.R_history[b].pop(0)

            # calculate SC
            SC = (ER*(self.SC_fastest - self.SC_slowest) + self.SC_slowest) ** 2

            # R_hat = R_n+1_m
            R_hat = (1 - SC) * self.prev_R_hat[b] + SC * self.R_history[b][-1]

            # calculate T
            T = R_hat * self.frame_time_len*self.segment_length / estimated_C

            # calculate B
            if buf_now < 0.5:
                gamma = 0.95
            elif buf_now > 1.0:
                gamma = 1.05
            else:
                gamma = 1
            B = max(buf_now + self.frame_time_len*self.segment_length - gamma * T, 0)

            # calculate 
            v = self.beta * (cdn_newest_id - self.prev_cdn_newest_id) * self.frame_time_len / sum(S_time_interval[-50:])
            # latency caused by accumulated video at CDN after next downloading interval
            D_cdn = max((cdn_newest_id - download_id)*self.frame_time_len + v*T - self.frame_time_len*self.segment_length, 0)

            if min_estimate_latency > B + D_cdn and B > self.buffer_threshold:
                min_estimate_latency = B + D_cdn
                bit_rate = b

            # for next segment
            self.prev_R_hat[b] = R_hat

         # naive buffer based (default  code)
        #  reservoir = 0.3
        #  cushion = 1.2
        #  if buf_now < reservoir:
        #      bit_rate = 0
        #  elif buf_now >= reservoir and buf_now < cushion/2:
        #      bit_rate = 1
        #  elif buf_now >= cushion/2 and buf_now < cushion:
        #      bit_rate = 2
        #  else:
        #      bit_rate = 3

         # determine target buffer by buffer size
         # if in [B^0_min, B^0_max), target_buffer = 1
         # otherwise, target_buffer = 0
         buf_now = S_buffer_size[-1]
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

         # for next iteration
         self.prev_rate = bit_rate
         self.prev_cdn_newest_id = cdn_newest_id

         return bit_rate, target_buffer, latency_limit

         
     
     def get_params(self):
     # get your params
        your_params = []
        return your_params
