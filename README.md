# gcr-cleaner
Script used for cleaning up Google Container Registry using Cloud Build

## Usage

There are 4 arguments:

* `--days-to-keep` - number of days for which tags should be kept
* `--tags-to-keep` - number of tags which are going to be kept, this takes precedence over `--days-to-keep` argument, so it means that even if there are tags older than X but they are smaller than value of this argument, then they will be kept anyway
* `--project` - google project where GCR will be cleaned
* `--do-it` - it actually says script to perform the cleanup, otherwise script will operate in `noop` mode

Running the cloudbuild

`gcloud build submits --substitutions _DAYS_TO_KEEP=10,_TAGS_TO_KEEP=5 .`

## Required Software

You only need gcloud installed and authenticated, script is at least Python3.5+ compatible (but might also work on older 3.x versions of python)

## Why not other solutions?

Currently it is hard to user raw Docker Registry API v2 to achieve same goals as this script:

* cleanup only one GCR project
* evaluate number of tags together with their age
