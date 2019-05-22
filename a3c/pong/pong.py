import os
import numpy as np

FRAME_X = [7, 152]
FRAME_Y = [31, 194]

default_conf = {
  'max_step': 10000,
  'lifes': 5,
  'ball_pos': [100, 40],
  'ball_speed': [5, 3],
  'ball_color': 143,
  'ball_size': [5, 2],
  'paddle_width': 15,
  'paddle_color': 143,
  'paddle_1_speed': 2,
  'paddle_2_speed': 2,
  'bricks_rows': 6,
  'bricks_color': [200, 180, 160, 140, 120, 100],
  'bricks_reward': [6, 5, 4, 3, 2, 1],
  'reward': 1,
  'catch_reward': 0
}

# Collision detection
def aabb(bb1, bb2):
  if bb1[0] < bb2[0]:
    return bb1[0] < bb2[1] and bb1[1] > bb2[0] and bb1[2] < bb2[3] and bb1[3] > bb2[2]
  else:
    return bb2[0] < bb1[1] and bb2[1] > bb1[0] and bb2[2] < bb1[3] and bb2[3] > bb1[2]
    

class GameObject(object):
  def __init__(self, pos, size, color=143, reward=0):
    self.pos = list(pos)
    self.size = list(size)
    self.color = color
    self.reward = reward

  def translate(self, translate):
    self.pos[0] += translate[0]
    self.pos[1] += translate[1]

  @property
  def boundingbox(self):
    # BB = (y1, y2, x1, x2)
    return [self.pos[0], self.pos[0] + self.size[0], self.pos[1], self.pos[1] + self.size[1]]

  @property
  def center(self):
    x = self.pos[1] + self.size[1]/2.0
    y = self.pos[0] + self.size[0]/2.0
    return (y, x)

# A warpper of all bricks GameObject
class Bricks(object):
  def __init__(self, rows, cols, brick_size, brick_colors, brick_rewards):
    assert (len(brick_colors) == len(brick_rewards) == rows)
    self.bricks_pos = [57, 8]
    self.rows = rows
    self.cols = cols
    self.brick_size = list(brick_size)
    self.brick_colors = list(brick_colors)
    self.brick_rewards = list(brick_rewards)
    self.bricks = []

    for r in range(self.rows):
      y = self.bricks_pos[0] + r*self.brick_size[0]
      x = self.bricks_pos[1]
      row_bricks = self.__create_rows([y, x], 200 - 20*r, self.rows - r)
      self.bricks += row_bricks
      
  def __create_rows(self, pos, c, r):
    rows = [GameObject([pos[0], pos[1] + p*self.brick_size[1]], self.brick_size, c, r) for p in range(self.cols)]
    return rows

  @property
  def outer_boundingbox(self):
    return [
      self.bricks_pos[0], 
      self.bricks_pos[0] + self.brick_size[0]*self.rows, 
      self.bricks_pos[1], 
      self.bricks_pos[1] + self.brick_size[1]*self.cols
    ]


class Pong(object):
  def __init__(self, config={}):
    self.conf = default_conf.copy()
    self.conf.update(config)
    self.step_count = 0
    self.shape = (210, 160)
    self.actions = 4
    self.actions_meaning = ['NOOP', 'FIRE', 'RIGHT_1', 'LEFT_1']
    self.obs_base = np.load(os.path.join(os.path.dirname(__file__), 'assets', 'base.npy'))
    self.digits = [np.load(os.path.join(os.path.dirname(__file__), 'assets', '{}.npy'.format(i))) for i in range(10)]
    self.render_bb = {
      'scores': [[5, 15, 36, 48], [5, 15, 52, 64], [5, 15, 68, 80]],
      'lifes': [5, 15, 100, 112],
      'level': [5, 15, 128, 140]
    }
  
  def step(self, action):
    if self.terminal:
      raise RuntimeError('Take action after game terminated.')
    if not 0 <= action < self.actions:
      raise IndexError('Selected action out of range.')

    act = self.actions_meaning[action]

    if act == 'RIGHT_1' and self.paddle_1.boundingbox[3] + self.paddle_1_v[1] < FRAME_X[1]:
      self.paddle_1.translate(self.paddle_1_v)
    if act == 'LEFT_1' and self.paddle_1.boundingbox[2] - self.paddle_1_v[1] > FRAME_X[0]:
      self.paddle_1.translate([-x for x in self.paddle_1_v])
      
     #self.ball.center
     #paddle_2.center

    if self.paddle_2.center[1] < self.ball.center[1] and self.paddle_2.boundingbox[3] + self.paddle_2_v[1] < FRAME_X[1]:
      self.paddle_2.translate(self.paddle_2_v)
    if self.paddle_2.center[1] >= self.ball.center[1] and self.paddle_2.boundingbox[2] - self.paddle_2_v[1] > FRAME_X[0]:
      self.paddle_2.translate([-x for x in self.paddle_2_v])


    if self.started:
      self.ball.translate(self.ball_v)
      
      # Check collision
      self.reward  = self.__edge_collision()
      self.__paddle_1_collision()
      self.__paddle_2_collision()
      self.score += self.reward

    # Check is FIRE
    if self.actions_meaning[action] == 'FIRE':
      self.started = True
    
    self.step_count += 1
    if self.step_count >= self.max_step:
      self.terminal = True

    # (obs, reward, done, info)
    return self.render(), self.reward, self.terminal, None

  def render(self):
    obs = np.copy(self.obs_base)

    # Draw paddle
    paddle_1_bb = self.paddle_1.boundingbox
    obs[paddle_1_bb[0]:paddle_1_bb[1], paddle_1_bb[2]:paddle_1_bb[3]] = self.paddle_1.color
    
    paddle_2_bb = self.paddle_2.boundingbox
    obs[paddle_2_bb[0]:paddle_2_bb[1], paddle_2_bb[2]:paddle_2_bb[3]] = self.paddle_2.color

    # Draw bricks
    #for brick in self.bricks.bricks:
    #  bb = brick.boundingbox
    #  obs[bb[0]:bb[1], bb[2]:bb[3]] = brick.color

    # Draw ball
    if self.started:
      ball_bb = self.ball.boundingbox
      obs[ball_bb[0]:ball_bb[1], ball_bb[2]:ball_bb[3]] = self.ball.color

    # Draw info (score, lifes)
    life_bb = self.render_bb['lifes']
    obs[life_bb[0]:life_bb[1], life_bb[2]:life_bb[3]] = self.digits[self.lifes]

    scores_bb = self.render_bb['scores']
    scores = [(self.score // 10**i) % 10 for i in range(2, -1, -1)]
    for idx, bb in enumerate(scores_bb):
      obs[bb[0]:bb[1], bb[2]:bb[3]] = self.digits[scores[idx]]

    return obs

  def reset(self):
    self.score = 0
    self.reward = 0
    self.step_count = 0
    self.lifes = self.conf['lifes']
    self.max_step = self.conf['max_step']
    self.terminal = False
    self.started = False
    self.ball = GameObject(self.conf['ball_pos'], self.conf['ball_size'], self.conf['ball_color'])
    self.ball_v = list(self.conf['ball_speed'])
    self.paddle_1 = GameObject([189, 70], [4, self.conf['paddle_width']], self.conf['paddle_color'], self.conf['catch_reward'])
    self.paddle_1_v = [0, self.conf['paddle_1_speed']]
    
    self.paddle_2 = GameObject([73, 70], [4, self.conf['paddle_width']], self.conf['paddle_color'], self.conf['catch_reward'])
    self.paddle_2_v = [0, self.conf['paddle_2_speed']]
    self.bricks = Bricks(self.conf['bricks_rows'], 18, [6, 8], self.conf['bricks_color'], self.conf['bricks_reward'])
    return self.render()

  def __edge_collision(self):
    bb1 = self.ball.boundingbox
    if aabb(bb1, [0, 999, 0, FRAME_X[0]]): # Left edge
      self.ball_v = [self.ball_v[0], -self.ball_v[1]]
      self.ball.translate([0, 2*self.ball_v[1]])
    elif aabb(bb1, [0, 999, FRAME_X[1], 999]): # Right edge
      self.ball_v = [self.ball_v[0], -self.ball_v[1]]
      self.ball.translate([0, 2*self.ball_v[1]])
    elif aabb(bb1, [0, FRAME_Y[0], 0, 999]): # Top edge
      self.terminal = self.started and self.lifes == 0
      self.ball = GameObject(self.conf['ball_pos'], self.conf['ball_size'], self.conf['ball_color'])
      self.ball_v = self.conf['ball_speed']
      self.reward += self.conf['reward']
      #self.reward += 10
      return self.reward
    elif aabb(bb1, [FRAME_Y[1], 999, 0, 999]): # Bottom edge
      self.lifes -= 1
      self.terminal = self.started and self.lifes == 0
      self.ball = GameObject(self.conf['ball_pos'], self.conf['ball_size'], self.conf['ball_color'])
      self.ball_v = self.conf['ball_speed']
    
    return 0

  def __paddle_1_collision(self):
    bb1 = self.ball.boundingbox
    if aabb(bb1, self.paddle_1.boundingbox):
      self.ball_v = [-self.ball_v[0], self.ball_v[1]]
      self.ball.translate([2*self.ball_v[0], 0])

      return self.paddle_1.reward
    return 0
    
  def __paddle_2_collision(self):
    bb1 = self.ball.boundingbox
    if aabb(bb1, self.paddle_2.boundingbox):
      self.ball_v = [-self.ball_v[0], self.ball_v[1]]
      self.ball.translate([2*self.ball_v[0], 0])

      return self.paddle_2.reward
    return 0


