package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	"time"
)

const (
	logPath       = "tools/fake_hpctrl/log"
	filePerm      = 0644
	endOfLineChar = 10
	newLineChar   = '\n'
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

loop:
	for {
		text, err := reader.ReadBytes(endOfLineChar)
		ExitIfErr(err)
		writeToFile(f, text)

		textString := strings.TrimSpace(string(text))

		switch textString {
		case "exit":
			break loop
		case "q *IDN?":
			fmt.Print("HEWLETT-PACKARD,83480A,US35240110,07.12")
		}
	}

	writeToFile(f, []byte{endOfLineChar})
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
