#   Pong AI to play in ESC180's pong tournament
#   Authors: Arya Ranadive and Chandresh Balakrishnan, 2024
#   Emails: arya.ranadive at mail.utoronto.ca, chandresh.balakrishnan at mail.utoronto.ca

prev_ball_center = None
count = 0
away = None
actual_away = None
import time, math # Time used for testing purposes
def predict_hit (ball_center, table_size, paddle_pos, other_paddle_pos, prev_velocity, recursion, time_to_other_side):
    global prev_ball_center, count, away, actual_away

    if not recursion:
       count = 0
    else:
       count += 1

    if count >= 30: # Recursion limit
       return [False, ball_center, 35]  # Return no prediction
    
    if paddle_pos[0] == 415:  # Used to get ball's relative velocity to our paddle
       side_flipped = False
    elif paddle_pos[0] == 15:
       side_flipped = True

    if not recursion:
      if prev_ball_center != None:
          v = [ball_center[0] - prev_ball_center[0],
              ball_center[1] - prev_ball_center[1]] # Velocity of ball per frame
          
          if (not side_flipped and v[0] < 0) or (side_flipped and v[0] > 0):
            away = True # Determine if ball is travelling towards or away from paddle
            actual_away = True
          else:
            away = False
            actual_away = False
      else:
          v = [0,0] # Overwrite "v = None" in edge cases

      prev_ball_center = ball_center
      prev_velocity = v

    else:
       v = prev_velocity # When in recursion take the last velocity as the current one, since it does not change unless there is a collision

    if v[0] != 0 and v[1] != 0:
      if v[0] > 0:
        time_x = (420 - (ball_center[0] + 7.5)) / v[0] # Time to reach edge of either paddle
      else:
        time_x = (30 - (ball_center[0] - 7.5)) / v[0]

      if v[1] > 0:
        time_y = (table_size[1]-ball_center[1]) / v[1] # Time to reach either top or bottom
      else:
        time_y = -ball_center[1] / v[1]

      if time_x < time_y:
        pred_position = [ball_center[0] + time_x * v[0], ball_center[1] + time_x * v[1]] # Guess y position at paddle
        if not away:
          hit_theta_top = math.atan((ball_center[1])/(table_size[0] - (paddle_pos[0] + 10)))
          hit_theta_bottom = math.atan((table_size[1]-ball_center[1])/(table_size[0] - (paddle_pos[0] + 10)))
          where_to_hit_top = None
          where_to_hit_bottom = None
          if hit_theta_top < 22.5*(math.pi/180):
            where_to_hit_top = hit_theta_top/((math.pi/180)*22.5/35)
          elif hit_theta_bottom > -22.5*(math.pi/180):
            where_to_hit_bottom = hit_theta_bottom/((math.pi/180)*22.5/35)
          if table_size[1] - other_paddle_pos[1] > other_paddle_pos[1]:
             where_to_hit = where_to_hit_bottom
          else:
             where_to_hit = where_to_hit_top
          if where_to_hit == None:
             where_to_hit = 35
          print (where_to_hit)
          return [True, pred_position, where_to_hit] # If ball is coming toward paddle, return the prediction
        else:
          time_to_other_side += time_x
          paddle_coverage = 0

          if pred_position[1] + 7.5 < other_paddle_pos[1] + 35:
             possible_paddle_pos = max (35, other_paddle_pos[1] + 35 - 1*time_to_other_side)
             paddle_coverage = min (max (0, possible_paddle_pos - pred_position[1]), 42.5) 
            
          elif pred_position[1] - 7.5 > (other_paddle_pos[1] + 35):
            possible_paddle_pos = min (245, other_paddle_pos[1] + 35 + 1*time_to_other_side)
            paddle_coverage = max (min (0, possible_paddle_pos - pred_position[1]), -42.5)        
          # Paddle coverage ranges from -42.5 to 42.5 and determines the possible angle
          if paddle_coverage > 0:
            avg_hit_pos = (paddle_coverage + 42.5)*0.5
          elif paddle_coverage < 0:
             avg_hit_pos = (paddle_coverage - 42.5)*0.5
          else:
             avg_hit_pos = 0

          theta = ((math.pi/180)*22.5/42.5)*avg_hit_pos

          v = [math.cos(theta)*v[0]-math.sin(theta)*v[1],
                math.sin(theta)*v[0]+math.cos(theta)*v[1]]
          v[0] = -v[0]
          v = [math.cos(-theta)*v[0]-math.sin(-theta)*v[1],
                math.cos(-theta)*v[1]+math.sin(-theta)*v[0]]

          paddle_speed_factor = 1.2 # Acceleration of ball upon hitting paddle
          v = [prev_velocity[0]*paddle_speed_factor, prev_velocity[1]*paddle_speed_factor] # Guess velocity after colision with enemy paddle
          away = not away

          outcome = predict_hit (pred_position, table_size, paddle_pos, other_paddle_pos, v, True, time_to_other_side) # predict where it hits paddle
          return outcome
      else:
        time_to_other_side += time_y
        pred_position = [ball_center[0] + time_y * v[0], ball_center[1] + time_y * v[1]] # Same logic for edges
        edge_speed_factor = 1
        v = [prev_velocity[0]*edge_speed_factor, -prev_velocity[1]*edge_speed_factor]
        outcome = predict_hit (pred_position, table_size, paddle_pos, other_paddle_pos, v, True, time_to_other_side)
        return outcome       
    return [False, ball_center, 35] # Return no prediction in edge cases

def pong_ai(paddle_frect, other_paddle_frect, ball_frect, table_size):
    ball_center = [ball_frect.pos[0] + 0.5*ball_frect.size[0], ball_frect.pos[1] + 0.5*ball_frect.size[1]]
    outcome = predict_hit (ball_center, table_size, paddle_frect.pos, other_paddle_frect.pos, None, False, 0) # Obtain prediction
    where_to_hit = outcome[2] # Change where the paddle hits the ball from. 0 is aggressive, 35 is passive

    if actual_away and paddle_frect.pos[1] + 0.5*paddle_frect.size[1] < 0.5*table_size[1]:
       return "down"
    elif actual_away and paddle_frect.pos[1] + 0.5*paddle_frect.size[1] > 0.5*table_size[1]:
       return "up"
    else:
        if outcome[0]: # If prediction exists, position paddle there
            if paddle_frect.pos[1] + 0.5*paddle_frect.size[1] - where_to_hit  < outcome[1][1]:
                    return "down"
            
            else:
                    return "up"
            
        else: # If no prediction, resort to ball-chasing
            if paddle_frect.pos[1] + 0.5*paddle_frect.size[1] - where_to_hit < ball_center[1]: # If not aligned, try to align with ball position first
                    return "down"
            else:
                    return "up"