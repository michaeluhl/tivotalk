#!/usr/bin/env python3

import argparse
import json
import re
import sys


SEARCH_PAT = re.compile("(<[^<>]+>)")


def expand_utterance(sample, substitutions):
    utterances = []
    queue = [sample]
    while len(queue) > 0:
        utterance = queue.pop()
        match = SEARCH_PAT.search(utterance)
        if match is None:
            utterances.append(utterance)
        else:
            alt_group = match.groups()[0]
            alternates = alt_group.strip('<>').split('|')
            for alternate in alternates:
                if alternate in substitutions:
                    for substitution in substitutions[alternate]:
                        queue.append(utterance.replace(alt_group, substitution, 1))
                else:
                    queue.append(utterance.replace(alt_group, alternate, 1))
    return {u.strip() for u in utterances}


def main(args):
    utterances = []
    with open(args.model[0], 'rt') as source:
        try:
            schema = json.load(source)['schema']
        except KeyError:
            print("Invalid Model Definition.")
            sys.exit(1)
    for intent in schema['intents']:
        if 'utterances' in intent:
            for utterance in intent['utterances']:
                utterances.extend(["{} {}".format(intent['intent'], u) for u in expand_utterance(utterance, {})])
            del intent['utterances']
    utterances.sort()
    with open(args.utterances, "wt") as u_file:
        for utterance in utterances:
            u_file.write("{}\n".format(utterance))
    with open(args.schema, "wt") as i_file:
        json.dump(schema, i_file, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="model_parser.py",
                                     description="Split an interaction model into the interaction schema and "
                                                 "expanded utterances.")
    parser.add_argument('-s', '--schema',
                        action='store',
                        default='intent_schema.json',
                        nargs='?',
                        metavar='SCHEMA',
                        dest='schema',
                        help='Specifies the name of file to which the intent schema should be written.'
                             '  Default: intent_schema.json')
    parser.add_argument('-u', '--utterances',
                        action='store',
                        default='utterances.txt',
                        nargs='?',
                        metavar='UTTERANCES',
                        dest='utterances',
                        help='Specifies the name of the file to which the expanded utterances should be written.'
                             '  Default: utterances.txt')
    parser.add_argument(action='store',
                        nargs=1,
                        metavar='MODEL',
                        dest='model',
                        help='File containing the interaction model.')
    parsed = parser.parse_args()
    main(parsed)
