import sys
import math
from nintaco_API import nintaco

STRING = "FITNESS: 000000"
WALKED = "FITNESS: "
STRING_1 = "Gen: 1 Mutation: A"
WALKED_VAL = 0
	
SPRITE_ID = 123
SPRITE_SIZE = 32
	
marioX = 0
marioY = 0
screenX = 0
screenY = 0

nintaco.initRemoteAPI("localhost", 9999)
api = nintaco.getAPI()

def getPositions():
	marioX = api.readCPU(0x6D) * 0x100 + api.readCPU(0x86)
	marioY = api.readCPU(0x03B8) + 16

	screenX = api.readCPU(0x03AD)
	screenY = api.readCPU(0x03B8)

def getTile(dx, dy):
	x = marioX + dx + 8
	y = marioY + dy - 16
	page = math.floor(x / 256) % 2
	subx = math.floor((x%256)/16)
	suby = math.floor((y - 32)/16)
	addr = 0x500 + page * 13 * 16 + suby * 16 + subx
	if suby >= 13 or suby < 0:
		return 0
	if api.readCPU(addr) != 0:
		return 1
	else:
		return 0

def getSprites():
	sprites = {}
	for slot in range(0,5):
		enemy = api.readCPU(0xF + slot)
		if enemy != 0:
			ex = api.readCPU(0x6E + slot) * 0x100 + api.readCPU(0x87 + slot)
			ey = api.readCPU(0xCF + slot) + 24
			sprites[len(sprites) + 1] = {"x": ex, "y": ey}
	return sprites


	
def launch():
	api.addFrameListener(renderFinished)
	api.addStatusListener(statusChanged)
	api.addActivateListener(apiEnabled)
	api.addDeactivateListener(apiDisabled)
	api.addStopListener(dispose)
	api.run()
	
def apiEnabled():
	global strWidth
	global strWidth1
	global strX
	global strY
	global strX1
	global strY1
	
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
	strWidth1 = api.getStringWidth(STRING_1, False)
	strX = (256 - strWidth) / 2 - 50
	strY = 10
	strX1 = (256 - strWidth) / 2 + 50
	strY1 = 10
	
def apiDisabled():
	print("API disabled")
	
def dispose():
	print("API stopped")
	
def statusChanged(message):
	print("Status message: %s" % message)
	
def renderFinished():
	WALKED_VAL = api.readCPU(0x6D) * 0x100 + api.readCPU(0x86)
	STRING = WALKED + str(WALKED_VAL)
	api.setColor(nintaco.DARK_BLUE)
	api.fillRect(strX - 1, strY - 1, strWidth + 2, 9)
	api.setColor(nintaco.BLUE)
	api.drawRect(strX - 2, strY - 2, strWidth + 3, 10)
	api.setColor(nintaco.DARK_BLUE)
	api.fillRect(strX1 - 1, strY1 - 1, strWidth1 + 2, 9)
	api.setColor(nintaco.BLUE)
	api.drawRect(strX1 - 2, strY1 - 2, strWidth1 + 3, 10)
	api.setColor(nintaco.WHITE)
	api.drawString(STRING, strX, strY, False)
	api.drawString(STRING_1, strX1, strY1, False)
	
if __name__ == "__main__":
	launch()
