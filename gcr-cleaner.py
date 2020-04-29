#!/usr/bin/env python3
from subprocess import check_output, call
import json
from sys import argv
import datetime
import argparse

parser = argparse.ArgumentParser(
    description="Use this script to delete tags from GCR, you need to have gcloud installed and authenticated"
)
parser.add_argument(
    "--project", required=True, help="id of the project for which GCR will be cleaned"
)
parser.add_argument(
    "--days-to-keep",
    default=365,
    type=int,
    help="images older than that value will get deleted by the script",
)
parser.add_argument(
    "--tags-to-keep",
    default=5,
    type=int,
    help="minimal number of tags (digests, as one digest could have many tags but they mean the same image) to be kept per image, takes priority over days to keep",
)
parser.add_argument(
    "--do-it",
    help='Actually perform operations. If not set script is running in a "noop" mode.',
    action="store_true",
)
args = parser.parse_args()


def printable_name(digest):
    return digest["tags"] if len(digest["tags"]) else digest["digest"]


def get_json(command):
    return json.loads(check_output(command.split()).decode("utf-8"))


def get_images(repository):
    command = "gcloud container images list --repository %s --format json" % (
        repository
    )

    return get_json(command)


def get_digests(image):
    command = "gcloud container images list-tags %s --format json" % (image)
    return get_json(command)


def get_digests_to_delete(digests, image):
    candidates = []
    # starting from the oldest images
    for digest in reversed(digests):
        tags_left_after_deletion = len(digests) - len(candidates)
        if tags_left_after_deletion <= args.tags_to_keep:
            print(
                "stop searching %s as number of digests left after performing deletion will be: %s out of %s (%s will be deleted)"
                % (image, tags_left_after_deletion, len(digests), len(candidates))
            )
            break
        timestamp = digest["timestamp"]
        age = datetime.datetime(timestamp["year"], timestamp["month"], timestamp["day"])
        delta = datetime.datetime.now() - age
        if delta.days >= args.days_to_keep:
            print(
                "adding %s from %s as they are %s days old (created at: %s)"
                % (printable_name(digest), image, delta.days, age)
            )
            candidates.append("%s@%s" % (image, digest["digest"]))
        else:
            print(
                "stop searching %s as %s days from %s (created at: %s) is lower than %s days to be kept"
                % (image, delta.days, printable_name(digest), age, args.days_to_keep)
            )
            break
    return candidates


def find_candidates(images, digests_to_delete):
    for image in images:
        print(">> starting lookup for %s\n" % (image["name"]))
        digests = get_digests(image["name"])
        if not len(digests):
            print(
                "%s is in fact repository with nested images, so I will start recursive search on it"
                % (image["name"])
            )
            find_candidates(get_images(image["name"]), digests_to_delete)
        else:
            digests_to_delete.extend(get_digests_to_delete(digests, image["name"]))
        print("\n")


digests_to_delete = []
for registry in ["gcr.io", "eu.gcr.io"]:
    find_candidates(get_images("%s/%s" % (registry, args.project)), digests_to_delete)
if args.do_it:
    for digest in digests_to_delete:
        command = "gcloud container images delete %s" % (digest)
        call(command.split())
else:
    print(len(digests_to_delete))
