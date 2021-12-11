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
	logPath               = "tools/fake_hpctrl/log"
	filePerm              = 0644
	endOfLineChar         = 10
	newLineChar           = '\n'
	cmdExit               = "exit"
	cmdIdn                = "q *idn?"
	responseIdn           = "HEWLETT-PACKARD,83480A,US35240110,07.12"
	cmdData               = "16"
	responseData          = "1776\n6441\n8921\n12026\n16171\n18826\n20363\n20797\n19499\n17190"
	cmdPreamble           = "q :waveform:preamble?"
	responsePreamble      = "2,2,2000,50,5.000000E-12,2.2000000000E-08,0,1.32375E-06,1.33434E-03,0,2,1.00000E-08,2.2000000000E-08,8.00000E-02,0.0E+000,\"10 DEC 2021\",\"14:16:16:16\",\"83480A:US35240110\",\"83485A:US34430174\",2,100,2,1,2.00000E+10,0E+000"
	cmdFile               = "file"
	cmdStopContinuousRead = "?"
)

func main() {
	iFlag := flag.Bool("i", false, "interactive flag")
	flag.Parse()

	if !*iFlag {
		log.Fatalln("the i flag wasn't used")
	}

	logFile, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, filePerm)
	ExitIfErr(err)
	defer logFile.Close()

	var measurementFile *os.File

	writeToFile(logFile, []byte(fmt.Sprintf("started at %v\n", time.Now())))

	reader := bufio.NewReader(os.Stdin)

loop:
	for {
		text, err := reader.ReadBytes(endOfLineChar)
		ExitIfErr(err)
		writeToFile(logFile, text)

		textString := strings.TrimSpace(strings.ToLower(string(text)))

		switch textString {
		case cmdExit:
			break loop
		case cmdIdn:
			fmt.Println(responseIdn)
		case cmdData:
			fmt.Println(responseData)
		case cmdPreamble:
			fmt.Println(responsePreamble)
		case cmdStopContinuousRead:
			if measurementFile == nil {
				log.Fatalln("measurementFile is nil")
			}
			writeToFile(measurementFile, []byte("some\nbig\ndata"))
		}

		if strings.HasPrefix(textString, cmdFile) {
			path := strings.TrimSpace(strings.TrimPrefix(textString, cmdFile))
			measurementFile, err = os.Create(path)
			ExitIfErr(err)
			defer measurementFile.Close()
		}

	}

	writeToFile(logFile, []byte{newLineChar})
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
