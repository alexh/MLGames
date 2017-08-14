# pylint: disable-msg=C0103
# pylint: disable-msg=C0111

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

# My Globals

pool = {}

# Global Vars

Filename = "SMB1-1.state"
ButtonNames = [
	   "A",
	   "B",
	   "Up",
	   "Down",
	   "Left",
	   "Right",
]

BoxRadius = 6
InputSize = (BoxRadius*2+1)*(BoxRadius*2+1)

Inputs = InputSize+1
Outputs = len(ButtonNames)

Population = 300
DeltaDisjoint = 2.0
DeltaWeights = 0.4
DeltaThreshold = 1.0

StaleSpecies = 15

MutateConnectionsChance = 0.25
PerturbChance = 0.90
CrossoverChance = 0.75
LinkMutationChance = 2.0
NodeMutationChance = 0.50
BiasMutationChance = 0.40
StepSize = 0.1
DisableMutationChance = 0.4
EnableMutationChance = 0.2

TimeoutConstant = 20

MaxNodes = 1000000

nintaco.initRemoteAPI("localhost", 9999)
api = nintaco.getAPI()

def getPositions():
	global marioX
	global marioY
	marioX = api.readCPU(0x6D) * 0x100 + api.readCPU(0x86)
	marioY = api.readCPU(0x03B8) + 16

	global screenX
	global screenY

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
	return 0

def getSprites():
	sprites = {}
	for slot in range(0, 5):
		enemy = api.readCPU(0xF + slot)
		if enemy != 0:
			ex = api.readCPU(0x6E + slot) * 0x100 + api.readCPU(0x87 + slot)
			ey = api.readCPU(0xCF + slot) + 24
			sprites[len(sprites)] = {"x": ex, "y": ey}
	return sprites

def getInputs():
	getPositions()
	sprites = getSprites()
	inputs = []
	for dy in range(-BoxRadius*16, BoxRadius*16 + 1, 16):
		for dx in range(-BoxRadius*16, BoxRadius*16 + 1, 16):
			inputs[len(inputs)] = 0
			tile = getTile(dx, dy)
			if tile == 1 and marioY + dy < 0x1B0:
				inputs[len(inputs)] = 1
			for i in range(0, len(sprites)):
				distx = abs(sprites[i]["x"] - (marioX+dx))
				disty = abs(sprites[i]["y"] - (marioY+dy))
				if distx <= 8 and disty <= 8:
					inputs[len(inputs)] = -1
	return inputs

def sigmoid(x):
	return 2/(1+math.exp(-4.9*x))-1

def newInnovation():
	global pool
	pool["innovation"] = pool["innovation"] + 1
	return pool["innovation"]

def newPool():
	nPool = {}
	nPool["species"] = {}
	nPool["generation"] = 0
	nPool["innovation"] = Outputs
	nPool["currentSpecies"] = 1
	nPool["currentGenome"] = 1
	nPool["currentFrame"] = 0
	nPool["maxFitness"] = 0
	return nPool

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
	return genome

def copyGenome(genome):
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
	for i in range(0, Inputs):
		network["neurons"][i] = newNeuron()
	for o in range(0, Outputs):
		network["neurons"][MaxNodes + o] = newNeuron()
	genome["genes"].sort(key=lambda g: g["out"])
	for i in range(0, len(genome["genes"])):
		gene = genome["genes"][i]
		if gene["enabled"]:
			if gene["out"] not in network["neurons"]:
				network["neurons"][gene["out"]] = newNeuron()
			neuron = network["neurons"][gene["out"]]
			neuron["incoming"].append(gene)
			if gene["into"] not in network["neurons"]:
				network["neurons"][gene["into"]] = newNeuron()
	genome["network"] = network

def evaluateNetwork(network, inputs):
	inputs.append(1)
	if len(inputs) != Inputs:
		print "Incorrect number of neural network inputs"
		return {}
	for i in (0, Inputs):
		network["neurons"][i]["value"] = inputs[i]
	for neuron in network["neurons"]:
		sum1 = 0
		for j in range(0, len(neuron["incoming"])):
			incoming = neuron["incoming"][j]
			other = network["neurons"][incoming["into"]]
			sum1 = sum1 + incoming["weight"] * other["value"]

		isIncoming = len(neuron["incoming"]) > 0
		if isIncoming:
			neuron["value"] = sigmoid(sum1)
	outputs = {}
	for o in range(0, Outputs):
		button = "P1 " + ButtonNames[o]
		outputs[button] = network["neurons"][MaxNodes + 0]["value"] > 0
		# if network["neurons"][MaxNodes + 0]["value"] > 0:
		# 	outputs[button] = True
		# else:
		# 	outputs[button] = False
	return outputs

def crossover(g1, g2):
	if g2["fitness"] > g1["fitness"]:
		tempg = g1
		g1 = g2
		g2 = tempg
	child = newGenome()
	innovations2 = {}
	for i in (0, len(g2["genes"])):
		gene = g2["genes"][i]
		innovations2[gene["innovation"]] = gene
	for i in (0, len(g1["genes"])):
		gene1 = g1["genes"][i]
		if gene1["innovation"] in innovations2:
			gene2 = innovations2[gene1["innovation"]]
			if random.randrange(1, 3) == 1 and gene2["enabled"]:
				child["genes"].append(copyGene(gene2))
			else:
				child["genes"].append(copyGene(gene1))
		else:
			child["genes"].append(copyGene(gene1))
	child["maxneuron"] = max(g1["maxneuron"], g2["maxneuron"])
	# for mutation, rate in g1["mutationRates"].items():
	# 	child["mutationRates"][mutation] = rate
	child["mutationRates"] = dict(g1["mutationRates"])
	return child

def randomNeuron(genes, nonInput):
	neurons = {}
	if not nonInput:
		for i in range(0, Inputs):
			neurons[i] = True
	for o in range(0, Outputs):
		neurons[MaxNodes + o] = True
	for i in range(0, len(genes)):
		if (not nonInput) or genes[i]["into"] > Inputs:
			neurons[genes[i]["into"]] = True
		if (not nonInput) or genes[i]["out"] > Inputs:
			neurons[genes[i]["out"]] = True
	count = len(neurons)
	n = random.randrange(0, count)
	for k, _ in neurons.items():
		n = n - 1
		if n == 0:
			return k
	return 0

def containsLink(genes, link):
	for i in range(0, len(genes)):
		gene = genes[i]
		if gene["into"] == link["into"] and gene["out"] == link["out"]:
			return True

def pointMutate(genome):
	step = genome["mutationRates"]["step"]
	for i in range(0, len(genome["genes"])):
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
	isLenOne = len(genome["genes"]) == 0
	if isLenOne:
		return
	genome["maxneuron"] = genome["maxneuron"] + 1
	gene = genome["genes"][random.randrange(0, len(genome["genes"]))]
	if not gene["enabled"]:
		return
	gene["enabled"] = False

	gene1 = copyGene(gene)
	gene1["out"] = genome["maxneuron"]
	gene1["weight"] = 1.0
	gene1["innovation"] = newInnovation()
	gene1["enabled"] = True
	genome["genes"].append(gene1)

	gene2 = copyGene(gene)
	gene2["into"] = genome["maxneuron"]
	gene2["innovation"] = newInnovation()
	gene2["enabled"] = True
	genome["genes"].append(gene2)

def enableDisableMutate(genome, enable):
	candidates = []
	for gene in genome["genes"]:
		if gene["enabled"] != enable:
			candidates.append(gene)
	isLenOne = len(candidates) == 0
	if isLenOne:
		return
	gene = candidates[random.randrange(0, len(candidates))]
	gene["enabled"] = not gene["enabled"]

def mutate(genome):
	for mutation, rate in genome["mutationRates"].items():
		if random.randrange(1, 3) == 1:
			genome["mutationRates"][mutation] = .95 * rate
		else:
			genome["mutationRates"][mutation] = 1.05263 * rate

	if random.random() < genome["mutationRates"]["connections"]:
		pointMutate(genome)

	p = genome["mutationRates"]["link"]
	while p > 0:
		if random.random() < p:
			linkMutate(genome, False)
		p = p - 1

	p = genome["mutationRates"]["bias"]
	while p > 0:
		if random.random() < p:
			linkMutate(genome, True)
		p = p - 1

	p = genome["mutationRates"]["node"]
	while p > 0:
		if random.random() < p:
			nodeMutate(genome)
		p = p - 1

	p = genome["mutationRates"]["enable"]
	while p > 0:
		if random.random() < p:
			enableDisableMutate(genome, True)
		p = p - 1

	p = genome["mutationRates"]["disable"]
	while p > 0:
		if random.random() < p:
			enableDisableMutate(genome, False)
		p = p - 1

def disjoint(genes1, genes2):
	i1 = {}
	for i in range(0, len(genes1)):
		gene = genes1[i]
		i1[gene["innovation"]] = True

	i2 = {}
	for i in range(0, len(genes2)):
		gene = genes2[i]
		i2[gene["innovation"]] = True

	disjointGenes = 0
	for i in range(0, len(genes1)):
		gene = genes1[i]
		if not i2[gene["innovation"]]:
			disjointGenes = disjointGenes + 1

	for i in range(0, len(genes2)):
		gene = genes2[i]
		if not i1[gene["innovation"]]:
			disjointGenes = disjointGenes + 1

	n = max(len(genes1), len(genes2))

	return disjointGenes / n

def weights(genes1, genes2):
	i2 = {}
	for i in range(0, len(genes2)):
		gene = genes2[i]
		i2[gene["innovation"]] = gene

	sum1 = 0
	coincident = 0
	for i in range(0, len(genes1)):
		gene = genes1[i]
		if gene["innovation"] in i2:
			gene2 = i2[gene["innovation"]]
			sum1 = sum1 + abs(gene["weight"] - gene2["weight"])
			coincident = coincident + 1

	return sum / coincident

def sameSpecies(genome1, genome2):
	dd = DeltaDisjoint * disjoint(genome1["genes"], genome2["genes"])
	dw = DeltaWeights * weights(genome1["genes"], genome2["genes"])
	return dd + dw < DeltaThreshold

def rankGlobally():
	global pool
	glob = []
	for s in range(0, len(pool["species"])):
		species = pool["species"][s]
		for g in range(0, len(species["genomes"])):
			glob.append(species.genomes[g])
	glob.sort(key=lambda g: g["fitness"])

	for g in range(0, len(glob)):
		glob[g]["globalRank"] = g

def calculateAverageFitness(species):
	total = 0

	for g in range(0, len(species["genomes"])):
		genome = species["genomes"][g]
		total = total + genome["globalRank"]
	species["averageFitness"] = total / len(species["genomes"])

def totalAverageFitness():
	global pool
	total = 0
	for s in range(0, pool["species"]):
		species = pool["species"][s]
		total = total + species["averageFitness"]

	return total

def cullSpecies(cutToOne):
	global pool
	for s in range(0, len(pool["species"])):
		species = pool["species"][s]

		species["genomes"].sort(key=lambda g: g["fitness"], reverse=True)

		remaining = math.ceil(len(species["genomes"]) / 2)
		if cutToOne:
			remaining = 1

		while len(species["genomes"]) > remaining:
			del species["genomes"][-1]


def breedChild(species):
	child = {}
	if random.random() < CrossoverChance:
		g1 = species["genomes"][random.randrange(0, len(species["genomes"]))]
		g2 = species["genomes"][random.randrange(0, len(species["genomes"]))]
		child = crossover(g1, g2)
	else:
		g = species["genomes"][random.randrange(0, len(species["genomes"]))]
		child = copyGenome(g)

	mutate(child)
	return child

def removeStaleSpecies():
	global pool
	survived = []

	for s in range(0, len(pool["species"])):
		species = pool["species"][s]

		species["genomes"].sort(key=lambda g: g["fitness"], reverse=True)

		if species["genomes"][0]["fitness"] > species["topFitness"]:
			species["topFitness"] = species["genomes"][0]["fitness"]
			species["staleness"] = 0
		else:
			species["staleness"] = species["staleness"] + 1
		if species["staleness"] < StaleSpecies or species["topFitness"] >= pool["maxFitness"]:
			survived.append(species)

	pool["species"] = survived

def removedWeakSpecies():
	global pool
	survived = []
	sum1 = totalAverageFitness()
	for s in range(0, len(pool["species"])):
		species = pool["species"][s]
		breed = math.floor(((species["averageFitness"] * 1.0) / (sum1 * 1.0)) * Population)
		if breed >= 1:
			survived.append(species)

	pool["species"] = survived


def addToSpecies(child):
	global pool
	foundSpecies = False
	for s in range(0, len(pool["species"])):
		species = pool["species"][s]
		if not foundSpecies and sameSpecies(child, species["genomes"][0]):
			species["genomes"].append(child)
			foundSpecies = True

	if not foundSpecies:
		childSpecies = newSpecies()
		childSpecies["genomes"].append(child)
		pool["species"].append(childSpecies)


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
