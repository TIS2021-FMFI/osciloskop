#!/bin/sh

cd tools/fake_hpctrl

go build hpctrl.go
GOOS=windows GOARCH=amd64 go build hpctrl.go