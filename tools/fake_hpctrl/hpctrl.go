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
	exitCmd  = "exit"
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

	writeToFile(f, fmt.Sprintf("started at %v\n", time.Now()))

	for true {
		reader := bufio.NewReader(os.Stdin)
		var text []byte

		for {
			b, err := reader.ReadByte()
			if err != nil {
				break
			}
			text = append(text, b)
		}

		textTrimmed := strings.Join(strings.Fields(string(text)), " ") + "\n"

		writeToFile(f, textTrimmed+"\n")

		fmt.Println(textTrimmed)

		if textTrimmed == exitCmd {
			return
		}
	}
}

func writeToFile(f *os.File, msg string) {
	_, err := f.WriteString(msg)
	ExitIfErr(err)
	f.Sync()
}

func ExitIfErr(err error) {
	if err != nil {
		log.Fatalln(err)
	}
}
