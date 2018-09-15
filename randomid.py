#!/usr/bin/env python3.7
import os
import sys
import math
import random
import common
import database
import configuration

bits_state = int(configuration.rid_bits_state)
bits_noise = int(configuration.rid_bits_noise)

assert(bits_state > 0)

if configuration.rid_python2_random:
	generator = random.Random()
	generator.seed(configuration.rid_seed, version=1)
else:
	generator = random.Random(configuration.rid_seed)

swizzle = []
swizzle.extend(range(0, bits_state))
swizzle.extend([-1] * bits_noise)

symbols = list(configuration.rid_symbols)

if configuration.rid_python2_random:
	generator.shuffle(symbols, random=generator.random)
	generator.shuffle(swizzle, random=generator.random)
else:
	generator.shuffle(symbols)
	generator.shuffle(swizzle)

invalid = 2 ** bits_state

if configuration.rid_python2_random:
	inverter = int(generator.random() * invalid)
else:
	inverter = generator.randrange(0, invalid)

length = int(math.ceil(math.log(2 ** (bits_state + bits_noise), len(symbols))))

state_key = 'rid_state'

del generator

def peek_state(db):
	csr = db.cursor()
	csr.execute('SELECT value FROM state WHERE key = ?', (state_key,))
	row = csr.fetchone()
	return row[0] if row else 0

def get_state_range_unlocked(db, count):
	if not count:
		return []

	csr = db.cursor()
	csr.execute('UPDATE state SET value = value + ? WHERE key = ?', (count, state_key))

	if csr.rowcount:
		csr = db.cursor()
		csr.execute('SELECT value FROM state WHERE key = ?', (state_key,))
		last = csr.fetchone()[0]
	else:
		csr = db.cursor()
		csr.execute('INSERT INTO state (key, value) VALUES(?, ?)', (state_key, count))
		last = count

	return range(last - count, last)

def get_state_range(db, count):
	with db:
		return get_state_range_unlocked(db, count)

def make_id(state):
	state ^= inverter
	noise = int.from_bytes(os.urandom(math.ceil(bits_noise / 8)), 'little')
	swizzled = 0

	for i in range(0, len(swizzle)):
		if swizzle[i] < 0:
			bit = noise & 1
			noise >>= 1
		else:
			bit = (state >> swizzle[i]) & 1

		swizzled |= bit << i

	result = []
	for i in range(0, length):
		swizzled, index = divmod(swizzled, len(symbols))
		result.append(symbols[index])

	return ''.join(result)

if __name__ == '__main__':
	if len(sys.argv) > 1:
		count = int(sys.argv[1])
	else:
		count = 1

	with database.open_database() as db:
		state_range = get_state_range(db, count)

	for state in state_range:
		print(make_id(state))
