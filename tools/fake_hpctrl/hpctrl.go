package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode"
)

// all commands have to be in lowercase
const (
	logPath               = "tools/fake_hpctrl/log"
	filePerm              = 0644
	endOfLineChar         = 10
	newLineChar           = '\n'
	cmdExit               = "exit"
	cmdGetIdn             = "q *idn?"
	responseIdn           = "HEWLETT-PACKARD,83480A,US35240110,07.12"
	cmdData               = "16"
	responseData          = "1776\n6441\n8921\n12026\n16171\n18826\n20363\n20797\n19499\n17190\n32256\n31744\n31232"
	cmdGetPreamble        = "q :waveform:preamble?"
	responsePreamble      = "2,2,2000,50,5.000000E-12,2.2000000000E-08,0,1.32375E-06,1.33434E-03,0,2,1.00000E-08,2.2000000000E-08,8.00000E-02,0.0E+000,\"10 DEC 2021\",\"14:16:16:16\",\"83480A:US35240110\",\"83485A:US34430174\",2,100,2,1,2.00000E+10,0E+000"
	cmdFile               = "file"
	cmdStopContinuousRead = "?"
	cmdPreambleOn         = "pon"
	cmdPreambleOff        = "poff"
	cmdGetAcquirePoints   = "q :acquire:points?"
	cmdGetAcquireCount    = "q :acquire:count?"
	cmdAcquirePoints      = "s :acquire:points"
	cmdAcquireCount       = "s :acquire:count"
	cmdGetAverage         = "q :acquire:average?"
	cmAverageOn           = "s :acquire:average on"
	cmAverageOff          = "s :acquire:average off"
	delayBetweenCommands  = 200 * time.Microsecond
)

var (
	fileWithPon              = filepath.Join("tools", "fake_hpctrl", "pon.txt")
	fileWithPoff             = filepath.Join("tools", "fake_hpctrl", "poff.txt")
	fileWithPoff1000         = filepath.Join("tools", "fake_hpctrl", "poff_1000.txt")
	cmdGetChannelStatusRegex = regexp.MustCompile(`q :channel[1-4]:display\?`)
)

type internalData struct {
	acquirePoints       int
	acquireCount        int
	measurementFilePath string
	isPreamble          bool
	isAverage           bool
	enabledChannels     map[int]struct{}
}

func newInternalData() internalData {
	res := internalData{}
	res.acquirePoints = 100
	res.acquireCount = 200
	res.isAverage = true
	res.enabledChannels = map[int]struct{}{1: {}, 3: {}}
	return res
}

func main() {
	iFlag := flag.Bool("i", false, "interactive flag")
	flag.Parse()

	if !*iFlag {
		log.Fatalln("the i flag wasn't used")
	}

	logFile, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, filePerm)
	exitIfErr(err)
	defer logFile.Close()
	writeToFile(logFile, []byte(fmt.Sprintf("started at %v\n", time.Now())))

	reader := bufio.NewReader(os.Stdin)

	data := newInternalData()

loop:
	for {
		input, err := reader.ReadBytes(endOfLineChar)
		exitIfErr(err)

		// simulating delay
		time.Sleep(delayBetweenCommands)

		writeToFile(logFile, input)

		trimmedInput := strings.TrimSpace(strings.ToLower(string(input)))

		switch trimmedInput {
		case cmdExit:
			break loop
		case cmdGetIdn:
			fmt.Println(responseIdn)
		case cmdData:
			fmt.Println(responseData)
		case cmdGetPreamble:
			fmt.Println(responsePreamble)
		case cmdPreambleOn:
			data.isPreamble = true
		case cmdPreambleOff:
			data.isPreamble = false
		case cmdGetAcquireCount:
			fmt.Println(data.acquireCount)
		case cmdGetAcquirePoints:
			fmt.Println(data.acquirePoints)
		case cmAverageOn:
			data.isAverage = true
		case cmAverageOff:
			data.isAverage = false
		case cmdGetAverage:
			if data.isAverage {
				fmt.Println("1")
			} else {
				fmt.Println("0")
			}
		case cmdStopContinuousRead:
			if data.measurementFilePath == "" {
				log.Fatalln("measurementFile is empty")
			}
			var fileWithData string
			if data.isPreamble {
				fileWithData = fileWithPon
			} else {
				if data.isAverage {
					fileWithData = fileWithPoff
				} else {
					fileWithData = fileWithPoff1000
				}
			}
			copyFile(data.measurementFilePath, fileWithData)
		}

		if strings.HasPrefix(trimmedInput, cmdFile) {
			data.measurementFilePath = strings.TrimSpace(strings.TrimPrefix(trimmedInput, cmdFile))
		} else if strings.HasPrefix(trimmedInput, cmdAcquirePoints) {
			points, err := getLastAsInt(trimmedInput)
			exitIfErr(err)
			data.acquirePoints = points
		} else if strings.HasPrefix(trimmedInput, cmdAcquireCount) {
			count, err := getLastAsInt(trimmedInput)
			exitIfErr(err)
			data.acquireCount = count
		} else if cmdGetChannelStatusRegex.MatchString(trimmedInput) {
			channelNumber, err := getChannelNumber(trimmedInput)
			exitIfErr(err)
			if _, ok := data.enabledChannels[channelNumber]; ok {
				fmt.Println("1")
			} else {
				fmt.Println("0")
			}
		}
	}

	writeToFile(logFile, []byte{newLineChar})
}

func writeToFile(f *os.File, msg []byte) {
	_, err := f.Write(msg)
	exitIfErr(err)
	f.Sync()
}

func exitIfErr(err error) {
	if err != nil {
		log.Fatalln(err)
	}
}

func copyFile(destination, source string) {
	src, err := os.Open(source)
	exitIfErr(err)
	defer src.Close()

	dst, err := os.Create(destination)
	exitIfErr(err)
	defer dst.Close()

	_, err = io.Copy(dst, src)
	exitIfErr(err)
}

func getLastAsInt(cmd string) (int, error) {
	split := strings.Fields(cmd)
	last := split[len(split)-1]
	return strconv.Atoi(last)
}

func getChannelNumber(command string) (int, error) {
	for _, i := range command {
		if unicode.IsDigit(i) {
			return strconv.Atoi(string(i))
		}
	}
	return 0, errors.New("invalid command")
}
