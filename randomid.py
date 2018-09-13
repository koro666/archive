#!/usr/bin/env python3.7
import math
import random
import common
import configuration

bits_state = int(configuration.rid_bits_state)
bits_noise = int(configuration.rid_bits_noise)

assert(bits_state > 0)
assert(bits_state + bits_noise) <= 63

generator = random.Random(configuration.rid_seed)

swizzle = []
swizzle.extend(range(0, bits_state))
swizzle.extend([255] * bits_noise)

symbols = list(configuration.rid_symbols)
generator.shuffle(symbols)
generator.shuffle(swizzle)

invalid = 2 ** bits_state
mask = generator.randint(0, invalid)
length = int(math.ceil(math.log(2 ** (bits_state + bits_noise), len(symbols))))
