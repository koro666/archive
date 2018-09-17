Random ID Generation
====================

Technical description of the short link "random ID" generation algorithm.

Problem
-------

How does one generate truly "random-looking" IDs (something similar to what Imgur or Youtube do) without ever repeating a previously-issued ID, all while staying efficient?

Tentative #1
------------

The very first obvious idea is to simply generate a random string, try to insert it into the database, and if that fails because it already exists, generate a new one and retry until finding one that does not exist yet.

There are two problems with that approach:

- One needs to store every ID ever generated forever;
- It gets slower and slower as more IDs are generated.

It is thus not an effective solution.

Tentative #2
------------

The second obvious idea is to use an incrementing integer, and use a transformation function (such as Base64, or something more complex) to generate a string. Therefore one only needs to store the "last ID" generated.

There is still one problem with this approach. An attacker, either by knowing the algorithm or observing sequences of generated IDs, can predict past and future IDs. At this point, it's not really better than just handing off the numeric value directly.

Solution
--------

The solution for this problem... is simply to use both a bit of #1 and #2 at the same time! Generate a random ID given an incrementing integer, while adding randomness to it.

This is a description of how this happens in `randomid.py`.

A *seed* is specified in the configuration file that will assure an unrepeatable, but different sequence for that seed.

Using the seed, at startup, a random number generator is created and is used to:

- Generate an *inverter mask* ;
- Generate a *swizzle table* ;
- Shuffle the ID symbols into the *shuffled symbol set*.

An incrementing integer, called the *state*, is persisted to allow never repeating the same ID ever again.

Starting from a clean *state*, certain bits are toggled by XORing with the *inverter mask*. This gives the *inverted state*.

The *inverted state* is then passed through the *swizzle table* to become the *swizzled state*. The swizzle table defines, for each output bit in the swizzled state, which bit of the inverted state to pick, or whether to generate a random bit value.

The *shuffled symbol set* is then used to transform the *swizzled state* into a base-N *string*, with N being the number of symbols.

That string is the generated random ID.

All these things happen entirely so that two IDs generated from sequential states look vastly different. An attacker observing sequences of IDs would have trouble figuring out how to map the base-N string back to a number, given the randomness of symbol order as well as the noise. If they did figure it out anyway, and could isolate which bits of the swizzled state change in what fashion, they still would need to guess 2^(bits of noise) IDs to actually match the real generated ID.

Also, since the bits of the swizzled state corresponding to bits of the inverted state will never have the same pattern again, given the incrementing nature of the input state, it would be impossible to ever generate the same swizzled state again, thus preventing an ID from ever appearing twice.
