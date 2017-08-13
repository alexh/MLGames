import sys
from nintaco_API import nintaco

STRING = "Hello, World!"
  
SPRITE_ID = 123
SPRITE_SIZE = 32
  
spriteX = 0
spriteY = 8
spriteVx = 1
spriteVy = 1

nintaco.initRemoteAPI("localhost", 9999)
api = nintaco.getAPI()
  
def launch():
  api.addFrameListener(renderFinished)
  api.addStatusListener(statusChanged)
  api.addActivateListener(apiEnabled)
  api.addDeactivateListener(apiDisabled)
  api.addStopListener(dispose)
  api.run()
  
def apiEnabled():
  global strWidth
  global strX
  global strY
  
  print("API enabled")

  sprite = [0 for i in range(SPRITE_SIZE * SPRITE_SIZE)]
  for y in range(SPRITE_SIZE):
    Y = y - SPRITE_SIZE / 2 + 0.5
    for x in range(SPRITE_SIZE):
      X = x - SPRITE_SIZE / 2 + 0.5
      sprite[SPRITE_SIZE * y + x] = nintaco.ORANGE if (X * X + Y * Y 
          <= SPRITE_SIZE * SPRITE_SIZE / 4) else -1
  api.createSprite(SPRITE_ID, SPRITE_SIZE, SPRITE_SIZE, sprite)
  strWidth = api.getStringWidth(STRING, False)
  strX = (256 - strWidth) / 2
  strY = (240 - 8) / 2
  
def apiDisabled():
  print("API disabled")
  
def dispose():
  print("API stopped")
  
def statusChanged(message):
  print("Status message: %s" % message)
  
def renderFinished():
  global spriteX
  global spriteY
  global spriteVx
  global spriteVy

  api.drawSprite(SPRITE_ID, spriteX, spriteY)
  if spriteX + SPRITE_SIZE == 255:
    spriteVx = -1
  elif spriteX == 0:
    spriteVx = 1
  if spriteY + SPRITE_SIZE == 231:
    spriteVy = -1
  elif spriteY == 8:
    spriteVy = 1
  spriteX += spriteVx
  spriteY += spriteVy

  api.setColor(nintaco.DARK_BLUE)
  api.fillRect(strX - 1, strY - 1, strWidth + 2, 9)
  api.setColor(nintaco.BLUE)
  api.drawRect(strX - 2, strY - 2, strWidth + 3, 10)
  api.setColor(nintaco.WHITE)
  api.drawString(STRING, strX, strY, False)
  
if __name__ == "__main__":
  launch()
