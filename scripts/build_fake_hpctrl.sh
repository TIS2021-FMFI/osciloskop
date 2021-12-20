#!/bin/sh

cd tools/fake_hpctrl || exit 1

go build hpctrl.go
GOOS=windows GOARCH=amd64 go build hpctrl.go