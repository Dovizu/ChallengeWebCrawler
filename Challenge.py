"""
Name: Donny Chen Reynolds
UC Berkleley, Electrical Engineering and Computer Sciences
"""


from urllib import urlopen
import json

#Global vars
GOAL = 'GOAL'
DEADEND = 'DEADEND'

class Parser(object):
	"""Parses expressions to get to next page"""

	def __init__(self):
		super(Parser, self).__init__()

		self.left_delimiter = '('
		self.right_delimiter = ')'
		self.operand_delimiter = ','

		self.delimiters = ['(', ')', ',']
		self.operations = ['+', '-', '*', '@']

		self.op_dict = {'add':'+', 'subtract':'-', 'multiply':'*', 'abs':'@'}
		self.stack = []

	def isNumber(self, string):
		"""isDigit, but tests negative as well"""

		try:
			int(string)
			return True
		except ValueError:
			return False

	def tokenize(self, string):
		"""Convert a string into a list of tokens

		>>> parse = Parser()
	    >>> parse.tokenize('add(multiply(2,2), subtract(3,2))')
	    ['+', '(', '*', '(', '2', ',', '2', ')', ',', '-', '(', '3', ',', '2', ')', ')']
		"""

		if string == []:
			raise SyntaxError("Empty String")
		#Changes words into symbols
		for key, entry in self.op_dict.iteritems():
			string = string.replace(key, entry)
		#Insert space around delimiters
		for symbol in self.delimiters:
			string = string.replace(symbol, ' '+symbol+' ')

		return string.split() #return list version


	def evaluate(self, operator, op1, op2=None):
		"""Takes three or two strings, operator, operand1, operand2, 
		and evaluate them
		"""

		op1 = int(op1)
		if op2 != None: op2 = int(op2)
		return {
			'+': lambda x, y: x+y,
			'-': lambda x, y: x-y,
			'*': lambda x, y: x*y,
			'@': lambda x, y: abs(x)
		}[operator](op1, op2)

	def parse(self, tokens):
		"""Recursively parse a list of tokens

		>>> parser = Parser()
	    >>> tokens = parser.tokenize('abs(add(multiply(1,2), subtract(3,10)))')
	    >>> tokens
	    ['@', '(', '+', '(', '*', '(', '1', ',', '2', ')', ',', '-', '(', '3', ',', '10', ')', ')', ')']
	    >>> parser.parse(tokens)
	    5
	    >>> tokens = parser.tokenize('abs(add(add(155,subtract(42276,220)),add(17,multiply(-1,abs(3810)))))')
	    >>> parser.parse(tokens)
	    38418
		"""

		first = tokens.pop(0)
		if self.isNumber(first):
			return first
		if first in self.operations:
			self.stack.append(tokens.pop(0))
			op1 = self.parse(tokens)
			op2 = None
			if first != '@':
				#make sure we're moving to the second operand
				assert tokens.pop(0) == self.operand_delimiter
				op2 = self.parse(tokens)
			#extra make sure our parentheses match
			if self.stack.pop() == self.left_delimiter and tokens.pop(0) == self.right_delimiter:
				return self.evaluate(first,op1,op2)


class Crawler(object):
	"""Crawls the Crunchy Web"""
	def __init__(self, url_base):
		super(Crawler, self).__init__()
		self.url_base = url_base
		self.parser = Parser()
		self.graph = {}
		
	def list_of_expr_from_url(self, param):
		"""read a url and return a list of lines"""

		url = self.url_base+str(param)
		html_text = urlopen(url).read()
		return html_text.split()

	def crawl(self, vertex):
		"""uses depth-first search to construct a graph of the Crunchy Web"""

		#all edges of this vertex
		edges = self.list_of_expr_from_url(vertex)
		self.graph[vertex] = []

		#goal or deadends don't need to be tokenzied/parsed
		if GOAL in edges or DEADEND in edges:
			self.graph[vertex].append(edges.pop())
			return
		else:
			#parse and evaluate each edge into a numerical parameter
			for edge in edges:
				self.graph[vertex].append(self.parser.parse(self.parser.tokenize(edge)))

		#recursively search all the destinations
		for destination in self.graph[vertex]:
			if destination not in self.graph.keys():
				self.crawl(destination)

class Solution(object):
	"""Solution maker, make solution JSON by counting unique nodes, 
	calculating shortest path and number of directed cycle count"""

	def __init__(self, graph, start):
		super(Solution, self).__init__()

		self.graph = graph
		self.goal = 0
		self.node_count = 0
		self.shortest_path = []
		self.directed_cycle_count = 0
		self.cycles = []

		self.spanning_tree = {}
		self.spanning_tree[start] = None
		self.visited = set()

	def find_unique_nodes(self):
		self.node_count = len(self.graph.keys())

	def find_shortest_path(self, current, target, path):
		"""Uses Dijkstra algorithm to find shortest path, as well as
		unique cycles"""

		if self.graph[current][0] == target:
			self.goal = current
			self.shortest_path.append(list(path))
			return
		for destination in self.graph[current]:
			if destination not in path and destination != DEADEND:
				self.find_shortest_path(destination, target, path+[destination])

	def trace_ancestor(self, vertex, destination):
		"""Take a vertex, destination, and find the path"""
		
		cycle = []
		while vertex != destination:
			if vertex is None:
				return [] #no cycle
			cycle.append(vertex)
			vertex = self.spanning_tree[vertex]
		cycle.append(destination)
		return cycle

	def find_unique_cycles(self, vertex):
		"""Find unique cycles"""

		self.visited.add(vertex)
		for destination in self.graph[vertex]:
			if destination != GOAL and destination != DEADEND:
				if destination not in self.visited:
					self.spanning_tree[destination] = vertex #parent
					self.find_unique_cycles(destination)
				else:
					cycle = self.trace_ancestor(vertex, destination)
					if cycle:
						self.cycles.append(cycle)

	def make_solution(self, start):
		"""Generate JSON file for solution"""
		self.find_unique_nodes()
		self.find_shortest_path(start, GOAL, [start])
		self.find_unique_cycles(start)
		self.directed_cycle_count = len(self.cycles)
		self.shortest_path = min(self.shortest_path, key=len)

		solution = {'goal':self.goal, 
					'node_count':self.node_count,
					'shortest_path':self.shortest_path,
					'directed_cycle_count':self.directed_cycle_count}

		json_sol = open('crunchyroll.json', 'w+')
		json.dump(solution, json_sol, separators=(',',':'))

def main():

	my_id = 38418
	url_base = 'http://www.crunchyroll.com/tech-challenge/roaming-math/donnyreynolds@berkeley.edu/'
	crawl = Crawler(url_base)
	crawl.crawl(my_id)
	sol = Solution(crawl.graph, my_id)
	sol.make_solution(my_id)

	print "==================================="
	print "Crunchy Roll Roaming Math Challenge"
	print "==================================="
	print "Complete"
	print "JSON file dumped in current directory"
	print "UNIQUE NODES"
	print sol.node_count
	print "TOTAL DIRECTED CYCLE COUNT"
	print sol.directed_cycle_count
	print "SHORTEST PATH"
	print sol.shortest_path
	print "GOAL PAGE"
	print sol.goal
	print "COMPLETE GRAPH"
	print sol.graph


main()

		