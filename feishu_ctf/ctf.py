from enum import Enum

class CtfManager:
	def __init__(self):
		# maps CTF name to Event
		self._events = dict()
		# map group_id to its information.
		# this returns a tuple:
		# first element is event name;
		# second element is challenge name,
		# if group is main group, second element is None.
		self._group_map = dict()
		# maps event name to (main_group_id, chall_group_map)
		# which further maps challenge name to group_id
		self._event_map = dict()
		# data in these 3 fields should always be consistent
	def get_event(self, name):
		return self._events.get(name)
	def new_event(self, name, group_id, doc):
		self._events[name] = Event()
		self._group_map[group_id] = (name, None)
		self._event_map[name] = (group_id, dict(), doc)
	def get_event_from_group(self, group_id):
		return self._group_map.get(group_id, (None,))[0]
	def get_chall_from_group(self, group_id):
		return self._group_map.get(group_id)
	def add_challenge(self, event, chall, category, group_id):
		self._events[event].add_chall(chall, category)
		self._group_map[group_id] = (event, chall)
		self._event_map[event][1][chall] = group_id
	def get_main_chat(self, event):
		return self._event_map[event][0]
	def get_chall_chat(self, event, chall):
		return self._event_map[event][1].get(chall)
	def get_doc_token(self, event):
		return self._event_map[event][2]

class Event:
	def __init__(self):
		self._challenges = dict()
		# maps challenge name to Challenge
	def get_chall(self, name):
		return self._challenges.get(name)
	def add_chall(self, name, category):
		if self._challenges.get(name) is None:
			self._challenges[name] = Challenge(category)
	def iter_chall(self, func):
		for k in self._challenges:
			func(k, self._challenges[k])

class ChallState(Enum):
	Open = 'open'
	Progress = 'progress'
	Stuck = 'stuck'
	Solved = 'solved'

class Challenge:
	def __init__(self, category = None):
		self.categories = set() if category is None else {category}
		self.state = ChallState.Open
		self.workings = set()
	def add_person(self, p):
		self.workings.add(p)


CTF = CtfManager()