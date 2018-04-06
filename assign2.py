import json
import networkx as nx
import random
from operator import itemgetter
import time
import datetime

def getTimeStamp():
	ts = time.time()
	return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

def createGraphs():
	fileName = "dblp_coauthorship.json"

	print("Opening json file...")
	data = json.load(open(fileName))

	dblp2005 = nx.Graph()
	dblp2006 = nx.Graph()
	dblp2005w = nx.Graph()

	print("Creating graphs...")
	for tupledata in data:

		u = tupledata[0]
		v = tupledata[1]
		year = tupledata[2]

		if year == 2005:
			dblp2005.add_edge(u, v)

			if dblp2005w.has_edge(u, v):			#adding 1 to the edge weight since the edge already exists
				dblp2005w[u][v]['weight'] += 1
			else:
				dblp2005w.add_edge(u, v, weight=1)	#initializing the number of coauthorships to 1

		elif year == 2006:
			dblp2006.add_edge(u, v)

	return createSCC(dblp2005, dblp2005w, dblp2006)

def createSCC(G2005, G2005w, G2006):
	print("Creating giant component for graphs...")
	scc_dblp2005 = max(nx.connected_component_subgraphs(G2005), key=len)			#A last part
	scc_dblp2006 = max(nx.connected_component_subgraphs(G2006), key=len)
	scc_dblp2005w = max(nx.connected_component_subgraphs(G2005w), key=len)
	return scc_dblp2005, scc_dblp2005w, scc_dblp2006

def saveGraph(G, fileName):
	#storing the edge list of the generated graph for later use
	with open(fileName, 'wb+') as f:
		nx.write_edgelist(G, f, delimiter='*')

def loadGraph(fileName):
	with open(fileName, 'rb') as f:
		return nx.read_edgelist(f, delimiter='*')

#B part i
def calculatePageRank(G, fileName):
	fh = open(fileName + ".pagerank", "w+")
	top50_pr_dblp2005 = sorted(nx.pagerank(G).items(), key=lambda x:-x[1])[:50]
	
	for x in list(top50_pr_dblp2005):
		fh.write(str(x))
		fh.write('\n')

	fh.close()

#B part ii
def calculateBetweenness(G, fileName):					
	with open(fileName + ".between", "w+") as f:
		print(getTimeStamp(), "Starting betweenness calculation for",fileName,"...")
		top20_between = sorted(nx.edge_betweenness_centrality(G, k=10000).items(), key=lambda x:-x[1])[:20]
		print(getTimeStamp(), "Finished betweenness calculation for",fileName,"...")
		for x in list(top20_between):
			f.write(str(x))
			f.write('\n')


#A
def numberOfEdgesAndNodes(G, fileName):
	fh = open(fileName + ".numbers", "w+")
	fh.write(fileName + "\n")
	edges = "Edges: " + str(G.number_of_edges())
	nodes = " Nodes: " + str(G.number_of_nodes())
	fh.write(edges)
	fh.write(nodes)
	fh.close()

#C part i, ii
#returns the core graph of G defined as the nodes with degree >= 3
def createCoreGraph(G):
	degree = G.degree()
	#print(len(degree))
	nodes_to_keep = [n for n,v in dict(degree).items() if v >= 3]			#find nodes with degree >= 3
	return G.subgraph(nodes_to_keep)								#create a subgraph with only those nodes

#C part iii
def findFoF(G):
	FOF = nx.Graph()
	#with open('FOF.txt', 'w+') as fp:
	for u in G.nodes():
		for v in G.neighbors(u):		#v = friends of u
			for w in G.neighbors(v): 
				if w != u and w != v and w not in G.neighbors(u):	#w = friends of v = friends of friends of u
					FOF.add_edge(u,w)

	with open('FOF.edgelist', 'wb+') as fp:
		nx.write_edgelist(FOF, fp, delimiter='*')


#C part iv
def findTEdges(G2005, G2006):
	G = nx.Graph()
	for e in G2006.edges():
		if not G2005.has_edge(*e):				#e does not exist in G2005 but exists in G2006
			#edges.append(e)
			G.add_edge(*e)

	with open('T.edgelist', 'wb+') as fp:
		nx.write_weighted_edgelist(G, fp, delimiter='*')

#len(T) = 252968

#C part v.a: picks 252968 edges from FOF randomly to predict
def randomEdges():
	with open('FOF.edgelist', 'rb') as f:
		G = nx.read_edgelist(f, delimiter='*')
		G_rand = nx.Graph()

		edges = list(G.edges())
		for i in range(252968):								#
			chosen_edge = random.choice(edges)
			G_rand.add_edge(*chosen_edge)

	with open('random.edgelist', 'wb+') as fp:
		nx.write_edgelist(G_rand, fp, delimiter='*')


#C part v.b
def commonNeighbors():
	G_pred = nx.Graph()
	G2005 = loadGraph('core2005.edgelist')
	with open('FOF.edgelist', 'rb') as f:
		G = nx.read_edgelist(f, delimiter='*')
		for e in G.edges():
			G_pred.add_edge(*e, score=sum(1 for _ in nx.common_neighbors(G2005, *e)))		#counting the number of elements in the common_neighbors iterator

	with open('common_neighbors.edgelist', 'wb+') as fp:
		nx.write_edgelist(G_pred, fp, delimiter='*')

#C part v.c
def jaccard():
	G_pred = nx.Graph()
	G2005 = loadGraph('core2005.edgelist')
	with open('FOF.edgelist', 'rb') as f:
		G = nx.read_edgelist(f, delimiter='*')
		preds = nx.jaccard_coefficient(G2005, ebunch=G.edges())

	with open('jaccard.edgelist', 'wb+') as fp:
		for u, v, p in preds:
			G_pred.add_edge(u, v, score=p)
		nx.write_edgelist(G_pred, fp, delimiter='*')

#C part v.d
def preferentialAttachment():
	G_pred = nx.Graph()
	G2005 = loadGraph('core2005.edgelist')
	with open('FOF.edgelist', 'rb') as f:
		G = nx.read_edgelist(f, delimiter='*')
		preds = nx.preferential_attachment(G2005, ebunch=G.edges())

	with open('pref.edgelist', 'wb+') as fp:
		for u, v, p in preds:
			G_pred.add_edge(u, v, score=p)
		nx.write_edgelist(G_pred, fp, delimiter='*')

#C part v.e
def adamicAdar():
	G_pred = nx.Graph()
	G2005 = loadGraph('core2005.edgelist')
	with open('FOF.edgelist', 'rb') as f:
		G = nx.read_edgelist(f, delimiter='*')
		preds = nx.adamic_adar_index(G2005, ebunch=G.edges())

	with open('adamic_adar.edgelist', 'wb+') as fp:
		for u, v, p in preds:
			G_pred.add_edge(u, v, score=p)
		nx.write_edgelist(G_pred, fp, delimiter='*')


def evaluatePrecision(filename, k=10):
	with open(filename, 'rb') as f:
		G = nx.read_edgelist(f, delimiter='*')
		edges = nx.get_edge_attributes(G, 'score')
		topk = sorted(nx.get_edge_attributes(G, 'score').items(), key=lambda x:-x[1])[:k]

		'''for x in topk:
			print(x[0])
'''
	with open('T.edgelist', 'rb') as ft:
		T = nx.read_edgelist(ft, delimiter='*')

		predictedInT = 0
		for x in topk:
			if T.has_edge(*x[0]):
				predictedInT += 1
				#print(x[0])

		print(filename,": precision at ",k,"=",predictedInT/k)





#dblp2005, dblp2005w, dblp2006 = createGraphs()
#saveGraph(dblp2005, 'dblp2005.edgelist')
#saveGraph(dblp2005w, 'dblp2005w.edgelist')
#saveGraph(dblp2006, 'dblp2006.edgelist')

#numberOfEdgesAndNodes(dblp2005, "dblp2005")									#A (a)
#numberOfEdgesAndNodes(dblp2006, "dblp2006")									#A (b)
#numberOfEdgesAndNodes(dblp2005w, "dblp2005w")									#A (c)


#print("Calculating pagerank for each graph")
'''
calculatePageRank(scc_dblp2005, "dblp2005")										#B part i
calculatePageRank(scc_dblp2006, "dblp2006")	
calculatePageRank(scc_dblp2005w, "dblp2005w")
'''

calculateBetweenness(loadGraph('dblp2005.edgelist'), 'dblp2005')
calculateBetweenness(loadGraph('dblp2005w.edgelist'), 'dblp2005w')
calculateBetweenness(loadGraph('dblp2006.edgelist'), 'dblp2006')

'''
print("Creating core 2005 graph...")
core2005 = createCoreGraph(dblp2005)											#C part i
saveGraph(core2005, 'core2005.edgelist')
print("Creating core 2006 graph...")
core2006 = createCoreGraph(dblp2006)											#C part ii
saveGraph(core2006, 'core2006.edgelist')

numberOfEdgesAndNodes(core2005, "core2005")										
numberOfEdgesAndNodes(core2006, "core2006")									

#print("Finding friends of friends...")
#findFoF(core2005)																#C part iii

print("Finding target edges (T)...")
findTEdges(core2005, core2006)													#C part iv
'''
'''
randomEdges()																	#C part v.a	
commonNeighbors()																#C part v.b
jaccard()																		#C part v.c
preferentialAttachment()														#C part v.d
adamicAdar()																	#C part v.e


																				#C part vi
with open('T.edgelist', 'rb') as f:
	G = nx.read_edgelist(f, delimiter='*')
	numEdgesT = len(G.edges())


evaluatePrecision('random.edgelist', k=10)
evaluatePrecision('random.edgelist', k=20)
evaluatePrecision('random.edgelist', k=50)
evaluatePrecision('random.edgelist', k=100)
evaluatePrecision('random.edgelist', k=numEdgesT)

evaluatePrecision('common_neighbors.edgelist', k=10)
evaluatePrecision('common_neighbors.edgelist', k=20)
evaluatePrecision('common_neighbors.edgelist', k=50)
evaluatePrecision('common_neighbors.edgelist', k=100)
evaluatePrecision('common_neighbors.edgelist', k=numEdgesT)

evaluatePrecision('jaccard.edgelist', k=10)
evaluatePrecision('jaccard.edgelist', k=20)
evaluatePrecision('jaccard.edgelist', k=50)
evaluatePrecision('jaccard.edgelist', k=100)
evaluatePrecision('jaccard.edgelist', k=numEdgesT)

evaluatePrecision('pref.edgelist', k=10)
evaluatePrecision('pref.edgelist', k=20)
evaluatePrecision('pref.edgelist', k=50)
evaluatePrecision('pref.edgelist', k=100)
evaluatePrecision('pref.edgelist', k=numEdgesT)

evaluatePrecision('adamic_adar.edgelist', k=10)
evaluatePrecision('adamic_adar.edgelist', k=20)
evaluatePrecision('adamic_adar.edgelist', k=50)
evaluatePrecision('adamic_adar.edgelist', k=100)
evaluatePrecision('adamic_adar.edgelist', k=numEdgesT)
'''