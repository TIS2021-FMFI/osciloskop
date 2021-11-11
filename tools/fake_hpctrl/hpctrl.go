package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"time"
)

const (
	logPath  = "tools/fake_hpctrl/log"
	filePerm = 0644
)

func main() {
	iFlag := flag.Bool("i", false, "interactive flag")
	flag.Parse()

	if !*iFlag {
		log.Fatalln("the i flag wasn't used")
	}

	f, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, filePerm)
	ExitIfErr(err)
	defer f.Close()

	writeToFile(f, []byte(fmt.Sprintf("started at %v\n", time.Now())))

	reader := bufio.NewReader(os.Stdin)
	var text []byte

	for {
		b, err := reader.ReadByte()
		if err != nil {
			break
		}
		text = append(text, b)
	}

	text = append(text, '\n')

	writeToFile(f, text)
}

func writeToFile(f *os.File, msg []byte) {
	_, err := f.Write(msg)
	ExitIfErr(err)
	f.Sync()
}

func ExitIfErr(err error) {
	if err != nil {
		log.Fatalln(err)
	}
}
