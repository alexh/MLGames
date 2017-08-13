import sys
import math
import random
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

def getInputs():
	getPositions()
	sprites = getSprites()
	inputs = {}
	for dy in range(-BoxRadius*16, BoxRadius*16 + 1, 16):
		for dx in range(-BoxRadius*16, BoxRadius*16 + 1, 16):
			inputs[len(inputs) + 1] = 0
			tile = getTile(dx, dy)
			if tile == 1 and marioY + dy < 0x1B0:
				inputs[len(inputs)] = 1
			for i in range(1, len(sprites) + 1):
				distx = math.abs(sprites[i]["x"] - (marioX+dx))
				disty = math.abs(sprites[i]["y"] - (marioY+dy))
				if distx <= 8 and disty <= 8:
					inputs[len(inputs)] = -1
	return inputs

def sigmoid():
	return 2/(1+math.exp(-4.9*x))-1

def newInnovation():
	pool["innovation"] = pool["innovation"] + 1
	return pool["innovation"]

def newPool():
	pool = {}
	pool["species"] = {}
	pool["generation"] = 0
	pool["innovation"] = Outputs
	pool["currentSpecies"] = 1
	pool["currentGenome"] = 1
	pool["currentFrame"] = 0
	pool["maxFitness"] = 0
	return pool

def newSpecies():
	species = {}
	species["topFitness"] = 0
	species["staleness"] = 0
	species["genomes"] = {}
	species["averageFitness"] = 0
	return species

def newGenome():
	genome = {}
	genome["genes"] = []
	genome["fitness"] = 0
	genome["adjustedFitness"] = 0
	genome["network"] = {}
	genome["maxneuron"] = 0
	genome["globalRank"] = 0
	genome["mutationRates"] = {}
	genome["mutationRates"]["connections"] = MutateConnectionsChance
	genome["mutationRates"]["link"] = LinkMutationChance
	genome["mutationRates"]["bias"] = BiasMutationChance
	genome["mutationRates"]["node"] = NodeMutationChance
	genome["mutationRates"]["enable"] = EnableMutationChance
	genome["mutationRates"]["disable"] = DisableMutationChance
	genome["mutationRates"]["step"] = StepSize
	return genome;

def copyGenome():
	genome2 = dict(genome)
	genome2["genes"] = list(genome["genes"])
	genome2["mutationRates"] = dict(genome["mutationRates"])
	# genome2 = newGenome()
	# for g in range(1, len(genome["genes"]) + 1):
	# 	genome2[len(genome2)] = copyGene(genome["genes"][g])
	# genome2["maxneuron"] = genome["maxneuron"]
	# genome2["mutationRates"]["connections"] = genome["mutationRates"]["connections"]
	# genome2["mutationRates"]["link"] = genome["mutationRates"]["link"]
	# genome2["mutationRates"]["bias"] = genome["mutationRates"]["bias"]
	# genome2["mutationRates"]["node"] = genome["mutationRates"]["node"]
	# genome2["mutationRates"]["enable"] = genome["mutationRates"]["enable"]
	# genome2["mutationRates"]["disable"] = genome["mutationRates"]["disable"]
	return genome2

def basicGenome():
	genome = newGenome()
	innovation = 1
	genome["maxneuron"] = Inputs
	mutate(genome)
	return genome

def newGene():
	gene = {}
	gene["into"] = 0
	gene["out"] = 0
	gene["weight"] = 0.0
	gene["enabled"] = True
	gene["innovation"] = 0
	return gene


def copyGene(gene):
	gene2 = dict(gene)
	return gene2

def newNeuron():
	neuron = {}
	neuron["incoming"] = []
	neuron["value"] = 0.0
	return neuron

def generateNetwork(genome):
	network = {}
	network["neurons"] = {}
	for i in range(1, Inputs + 1):
		network["neurons"][i] = newNeuron()
	for o in range(1, Outputs + 1):
		network["neurons"][MaxNodes + o] = newNeuron()
	genome["genes"].sort(key= lamda g: g["out"])
	for i in range(1, len(genome["genes"]) + 1):
		gene = genome["genes"][i]
		if gene["enabled"]:
			if gene["out"] not in network["neurons"]:
				network["neurons"][gene["out"]] = newNeuron()
			neuron = network["neurons"][gene["out"]]
			neuron["incoming"].append(gene)
			if gene["into"] not in network["neurons"]:
				network["neurons"][gene["into"]] = newNeuron()
	genome["network"] = network

def evaluateNetwork():
	inputs.append(1)
	if (len(inputs) != Inputs):
		print("Incorrect number of neural network inputs")
		return {}
	for i in (1, Inputs + 1):
		network["neurons"][i]["value"] = inputs[i]
	for neuron in network["neurons"]:
		sum = 0
		for j in range(1, len(neuron["incoming"]) + 1):
			incoming = neuron["incoming"][j]
			other = network["neurons"][incoming["into"]]
			sum = sum + incoming["weight"] * other["value"]
		if (len(neuron["incoming"]) > 0):
			neuron["value"] = sigmoid(sum)
	outputs = {}
	for o in range(1, Outputs + 1):
		button = "P1 " + ButtonNames[o]
		if network["neurons"][MaxNodes + 0]["value"] > 0:
			outputs[button] = True
		else:
			outputs[button] = False
	return outputs

def crossover(g1, g2):
	if g2["fitness"] > g1["fitness"]:
		tempg = g1
		g1 = g2
		g2 = tempg
	child = newGenome()
	innovations2 = {}
	for i in (1, len(g2["genes"]) + 1):
		gene = g2["genes"][i]
		innovations2[gene["innovation"]] = gene
	for i in (1, len(g1["genes"]) + 1):
		gene1 = g1["genes"][i]
		if gene1["innovation"] in innovations2:
			gene2 = innovations2[gene1["innovation"]]
			if random.randrange(1,3) == 1 and gene2["enabled"]:
				child["genes"].append(copyGene(gene2))
			else:
				child["genes"].append(copyGene(gene1))
		else:
			child["genes"].append(copyGene(gene1))
	child["maxneuron"] = math.max(g1["maxneuron"], g2["maxneuron"])
	# for mutation, rate in g1["mutationRates"].items():
	# 	child["mutationRates"][mutation] = rate
	child["mutationRates"] = dict(g1[mutationRates])
	return child

def randomNeuron(genes, nonInput):
	neurons = {}
	if not nonInput:
		for i in range(1, Inputs + 1):
			neurons[i] = True
	for o in range(1, Outputs + 1):
		neurons[MaxNodes + o] = True
	for i in range(1, len(genes) + 1):
		if (not nonInput) or genes[i]["into"] > Inputs:
			neurons[genes[i]["into"]] = True
		if (not nonInput) or genes[i]["out"] > Inputs:
			neurons[genes[i]["out"]] = True
	count = len(neurons)
	n = random.randrange(1, count + 1)
	for k,v in neurons.items():
		n = n - 1
		if (n == 0):
			return k
	return 0

def containsLink(genes, link):
	for i in range(1, len(genes) + 1):
		gene = genes[i]
		if gene["into"] == link["into"] and gene["out"] == link["out"]:
			return True

def pointMutate(genome):
	step = genome["mutationRates"]["step"]
	for i in range(1, len(genome["genes"]) + 1):
		gene = genome["genes"][i]
		if random.random() < PerturbChance:
			gene["weight"] = gene["weight"] + random.random() * step*2 - step
		else:
			gene.weight = random.random()*4-2

def linkMutate(genome, forceBias):
	neuron1 = randomNeuron(genome["genes"], False)
	neuron2 = randomNeuron(genome["genes"], True)
	newLink = newGene()
	if neuron1 <= Inputs and neuron2 <= Inputs:
		return
	if neuron2 <= Inputs:
		temp = neuron1
		neuron1 = neuron2
		neuron2 = temp

	newLink["into"] = neuron1
	newLink["out"] = neuron2
	if forceBias:
		newLink["into"] = Inputs

	if containsLink(genome["genes"], newLink):
		return
	newLink["innovation"] = newInnovation()
	newLink["weight"] = random.random()*4 - 2
	genome["genes"].append(newLink)

def nodeMutate(genome):
	if len(genome["genes"]) == 0:
		return
	genome["maxneuron"] = genome["maxneuron"] + 1
	gene = genome["genes"][random.randrange(1, len(genome["genes"]) + 1)]
	if not gene["enabled"]:
		return
	gene["enabled"] = False

	gene1 = copyGene(gene)
	gene1["out"] = genome[maxneuron]
	gene1["weight"] = 1.0
	gene1["innovation"] = newInnovation()
	gene1["enabled"] = True
	genome["genes"].append(gene1)

	gene2 = copyGene(gene)
	gene2["into"] = genome["maxneuron"]
	gene2["innovation"] = newInnovation()
	gene2["enabled"] = True
	genome["genes"].append(gene2)


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
