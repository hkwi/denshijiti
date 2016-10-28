#!/bin/bash
set -ev

if [ "$TRAVIS_SECURE_ENV_VARS" != "true" ] || [ "$TRAVIS_NODE_VERSION" != "node" ] || [ "$TRAVIS_BRANCH" != "master" ] || [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
	exit 0
fi

git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch --unshallow

git config user.name "Hiroaki KAWAI Trais"
git config user.email "hiroaki.kawai@gmail.com"

git checkout -- .
cp $TRAVIS_BUILD_DIR/code.ttl docs/
git commit -m "auto" docs/code.ttl
git push "https://${GH_TOKEN}@github.com/hkwi/denshijiti.git" > /dev/null 2>&1
