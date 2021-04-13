package utils

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
)

const (
	GeckoURL = "https://api.coingecko.com/api/v3/coins/%s"
)

type CurrentPrice struct {
	USD int `json:"usd"`
}

type MarketData struct {
	CurrentPrice CurrentPrice `json:"current_price"`
	PriceChange  int          `json:"price_change_24h"`
}

// The following is the API response gecko gives
type GeckoPriceResults struct {
	ID         string     `json:"id"`
	Symbol     string     `json:"symbol"`
	Name       string     `json:"name"`
	MarketData MarketData `json:"market_data"`
}

// GetCryptoPrice retrieves the price of a given ticker using the coin gecko API
func GetCryptoPrice(ticker string) (GeckoPriceResults, error) {
	var price GeckoPriceResults
	reqURL := fmt.Sprintf(GeckoURL, ticker)
	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return price, err
	}
	req.Header.Add("User-Agent", "Mozilla/5.0")
	req.Header.Add("accept", "application/json")
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return price, err
	}

	results, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return price, err
	}
	err = json.Unmarshal(results, &price)
	if err != nil {
		return price, err
	}
	return price, nil
}
