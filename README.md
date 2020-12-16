This is an experimental script that uses configuration variance and a common corpus to try to throughly test a smart contract (or multiple contracts) with the Echidna smart-contract fuzzer (https://github.com/crytic/echidna).

It runs Echidna instances in parallel, and uses two basic ideas derived from my research:

- swarm testing (https://agroce.github.io/issta12.pdf)

- test length matters (https://agroce.github.io/ase08.pdf)

Usage is almost like Echidna; in fact if you just use the same arguments as to Echidna, it'll probably work.  E.g.,

> echidna-hammer contract.sol --config config.yaml --contract TEST

will likely do something reasonable.  By default "generations" of testing are 5 minutes in length, and the testing runs for an hour.
