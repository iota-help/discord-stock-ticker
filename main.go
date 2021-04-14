package main

import (
	"flag"
	"os"
	"sync"

	env "github.com/caitlinelfring/go-env-default"
	log "github.com/sirupsen/logrus"
)

var logger = log.New()

func init() {
	// initialize logging
	logLevel := flag.Int("logLevel", 0, "defines the log level. 0=production builds. 1=dev builds.")
	flag.Parse()
	logger.Out = os.Stdout
	switch *logLevel {
	case 0:
		logger.SetLevel(log.InfoLevel)
	default:
		logger.SetLevel(log.DebugLevel)
	}
}

func main() {
	var wg sync.WaitGroup
	wg.Add(1)
	m := NewManager()

	// check for inital bots
	if os.Getenv("DISCORD_BOT_TOKEN") != "" {
		s := addInitialStock()
		m.addStock(s.Ticker, s)
	}

	// wait forever
	wg.Wait()
}

func addInitialStock() *Stock {
	var stock *Stock

	token := os.Getenv("DISCORD_BOT_TOKEN")
	if token == "" {
		logger.Fatal("Discord bot token is not set! Shutting down.")
	}

	ticker := os.Getenv("TICKER")
	if ticker == "" {
		logger.Fatal("Ticker is not set!")
	}

	// now get settings for it
	nickname := env.GetBoolDefault("SET_NICKNAME", false)
	color := env.GetBoolDefault("SET_COLOR", false)
	flashChange := env.GetBoolDefault("FLASH_CHANGE", false)
	frequency := env.GetIntDefault("FREQUENCY", 60)

	switch os.Getenv("CRYPTO_NAME") {
	case "":
		// if it's not a crypto, it's a stock
		stock = NewStock(ticker, token, os.Getenv("STOCK_NAME"), nickname, color, flashChange, frequency)
	default:
		stock = NewCrypto(ticker, token, os.Getenv("CRYPTO_NAME"), nickname, color, flashChange, frequency)
	}
	return stock
}
