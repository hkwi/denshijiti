#!/bin/bash
set -ev

if [ "$TRAVIS_SECURE_ENV_VARS" != "true" ]; then
	exit 0
fi
if [ "$TRAVIS_BRANCH" != "master" ]; then
	exit 0
fi
if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
	exit 0
fi

git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"

git config user.name "Hiroaki KAWAI Trais"
git config user.email "hiroaki.kawai@gmail.com"

git checkout master
cp $TRAVIS_BUILD_DIR/code.ttl docs/
git add docs/code.ttl
git commit -m "auto"
git push "https://hkwi:${GH_TOKEN}@github.com/hkwi/denshijiti.git" master:master > /dev/null 2>&1
