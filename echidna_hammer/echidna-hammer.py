from __future__ import print_function

import argparse
from collections import namedtuple
import multiprocessing
import os
import random
import slither
import subprocess
import sys
import time
import yaml


def generate_config(rng, public, basic, config, initial=False):
    new_config = dict(basic)
    new_config["filterFunctions"] = []
    new_config["filterBlacklist"] = True
    basic_list = []
    blacklist = True
    if "filterFunctions" in basic:
        basic_list = basic["filterFunctions"]
        if "filterBlacklist" in basic:
            if not basic["filterBlacklist"]:
                blacklist = False
    excluded = []
    for f in public:
        if blacklist:
            if f in config.always:
                continue
            if f in basic_list:
                excluded.append(f)
            elif (not initial) and (rng.random() > config.prob):
                excluded.append(f)
        else:
            if f in config.always:
                continue
            if f in basic_list:
                if (not initial) and (rng.random() <= config.prob):
                    excluded.append(f)
            else:
                excluded.append(f)
    new_config["filterFunctions"] = excluded
    if 
    return new_config


def make_echidna_process(prefix, rng, public_functions, base_config, config, initial=False):
    g = generate_config(rng, public_functions, base_config, config, initial=initial)
    print("- LAUNCHING echidna-test with prefix", prefix, "blacklisting", g["filterFunctions"])
    os.mkdir(prefix)
    with open(prefix + "/config.yaml", 'w') as yf:
        yf.write(yaml.dump(g))
        outf = open(prefix + "/echidna.out", 'w')
        call = ["echidna-test"]
    call.extend(config.files)
    call.extend(["--config", "config.yaml"])
    if "config.contract" is not None:
        call.extend(["--contract", config.contract])
        call.extend(["--format", "text"])
    return (prefix, subprocess.Popen(call, stdout=outf, stderr=outf, cwd=os.path.abspath(prefix)), outf)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=os.path.abspath, nargs='+', default=None,
                        help='FILES argument for echidna-test')
    parser.add_argument('--name', type=str, default="hammer." + str(os.getpid()),
                        help='name for hammer (directory where output files are placed)')    
    parser.add_argument('--contract', type=str, default=None,
                        help='CONTRACT argument for echidna-test')
    parser.add_argument('--config', type=argparse.FileType('r'), default=None,
                        help='CONFIG argument for echidna-test')
    parser.add_argument('--ncores', type=int, default=multiprocessing.cpu_count(),
                        help='Number of cores to use (swarm instances to run in parallel (default = all available)')
    parser.add_argument('--corpus_dir', type=os.path.abspath, default=None,
                        help='Directory to store the echidna-hammer corpus (useful when existing corpus available)')
    parser.add_argument('--timeout', type=int, default=3600,
                        help='Total testing time (default = 3600)')
    parser.add_argument('--gen_time', type=int, default=3600,
                        help='Per-generation testing time (default = 300)')        
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed (default = None).')
    parser.add_argument('--prob', type=float, default=0.5,
                        help='Probability of including function in swarm config (default = 0.5).')
    parser.add_argument('--always', type=str, nargs='+', default=None,
                        help='functions to ALWAYS include in swarm configurations')
    parsed_args = parser.parse_args(sys.argv[1:])
    return (parsed_args, parser)


def make_config(pargs, parser):
    """
    Process the raw arguments, returning a namedtuple object holding the
    entire configuration, if everything parses correctly.
    """
    pdict = pargs.__dict__
    if pargs.files is None:
        parser.print_help()
        raise ValueError('You must specify some files to test!')
    # create a namedtuple object for fast attribute lookup
    key_list = list(pdict.keys())
    arg_list = [pdict[k] for k in key_list]
    Config = namedtuple('Config', key_list)
    nt_config = Config(*arg_list)
    return nt_config


def main():
    parsed_args, parser = parse_args()
    config = make_config(parsed_args, parser)
    print("Starting echidna-hammer with config={}".format(config))

    if os.path.exists(config.name):
        raise ValueError(config.name + ": refusing to overwrite existing directory!")
    else:
        os.mkdir(config.name)

    rng = random.Random(config.seed)

    public_functions = []
    for f in config.files:
        if not os.path.exists(f):
            raise ValueError('Specified file ' + f + ' does not exist!')
        with open (".slither-output", 'w') as sout:
            subprocess.call(["slither", f, "--print", "function-summary"], stdout=sout, stderr=sout)
        in_functions = False
        delim_count = 0
        with open(".slither-output", 'r') as sout:
            for line in sout:
                ls = line.split()
                if in_functions:
                    if len(ls) > 0:
                        if ls[0].find("+-") == 0:
                            delim_count +=1
                    if delim_count == 2:
                        in_functions = False
                    elif len(ls) > 2:
                        fname = ls[1].split("(")[0]
                        visibility = ls[3]
                        if visibility in ["public", "external"]:
                            public_functions.append(fname)
                if len(ls) > 1:
                    if ls[1] == "Function":
                        in_functions = True
    print("public functions:", public_functions)

    base_config = {}
    y = yaml.safe_load(config.config)
    for key in y:
        if key not in ["timeout", "testLimit", "stopOnFail", "corpusDir", "coverage"]:
            base_config[key] = y[key]
    base_config["timeout"] = config.gen_time
    if config.corpus_dir is not None:
        base_config["corpusDir"] = config.corpus_dir
    else:
        base_config["corpusDir"] = os.path.abspath(config.name + "/corpus")
    base_config["stopOnFail"] = False
    base_config["coverage"] = True
    if not os.path.exists(base_config["corpusDir"]):
        os.mkdir(base_config["corpusDir"])

    failures = []
    start = time.time()
    elapsed = time.time() - start
    
    print("RUNNING INITIAL CORPUS GENERATION")
    prefix = config.name + "/initial"
    (pname, p, outf) = make_echidna_process(prefix, rng, public_functions, base_config, config, initial=True)
    p.wait()
    if p.returncode != 0:
        print(pname, "FAILED")
        failures.append(pname + "/echidna.out")
    outf.close()
        
    generation = 1
    elapsed = time.time() - start
    while elapsed < config.timeout:
        print("SWARM GENERATION #" + str(generation))
        ps = []
        for i in range(config.ncores):
            prefix = config.name + "/gen." + str(generation) + "." + str(i)
            ps.append(make_echidna_process(prefix, rng, public_functions, base_config, config))
        any_not_done = True
        gen_start = time.time()
        while any_not_done:
            any_not_done = False
            done = []
            for (pname, p, outf) in ps:
                if p.poll() is None:
                    any_not_done = True
                else:
                    done.append((pname, p, outf))
                    outf.close()
                    if p.returncode != 0:
                        print(pname, "FAILED")
                        failures.append(pname + "/echidna.out")
            for d in done:
                ps.remove(d)
            gen_elapsed = time.time() - gen_start
            if gen_elapsed > (config.gen_time + 10): # 10 second fudge factor here!
                print("Generation still running after timeout!")
                for (pname, p, outf) in ps:
                    outf.close()
                    if p.poll() is None:
                        p.kill()
                any_not_done = False
        elapsed = time.time() - start
        generation += 1
    print("DONE!")
    if len(failures) == 0:
        sys.exit(0)
    else:
        for f in failures:
            print("See ", f, " for details on failing test(s).")
        sys.exit(len(failures))


if __name__ == '__main__':
    main()
